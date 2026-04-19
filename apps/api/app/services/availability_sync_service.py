from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
from pydantic import ValidationError
from sqlalchemy import select

from app.core.config import Settings
from app.db.models import AvailabilitySlotORM, ClinicORM, DoctorORM
from app.db.session import database_is_available, session_scope
from app.integrations.scheduling.base import SchedulingClient
from app.integrations.scheduling.fhir_client import FHIRSchedulingClient
from app.integrations.scheduling.http_client import HTTPSchedulingClient
from app.integrations.scheduling.schemas import AvailabilitySlotPayload
from app.integrations.scheduling.snapshot_client import SnapshotSchedulingClient


@dataclass(slots=True)
class AvailabilitySyncResult:
    source: str
    mode: str
    slots_upserted: int
    reference_data_backend: str


class AvailabilitySyncService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def sync(self) -> AvailabilitySyncResult:
        if not database_is_available(self.settings.postgres_url):
            raise RuntimeError("Postgres is unavailable. Start the database before syncing availability.")

        client = self._build_client()
        try:
            snapshot = client.fetch_snapshot()
        except (FileNotFoundError, httpx.HTTPError, ValidationError, ValueError) as exc:
            raise RuntimeError(f"Availability sync failed before database upsert: {exc}") from exc

        slots_upserted = 0
        seen_source_record_ids: set[str] = set()
        touched_doctor_ids: set[str] = set()
        with session_scope(self.settings.postgres_url) as session:
            for slot in snapshot.slots:
                doctor_id = self._resolve_doctor_id(session, snapshot.source, slot)
                clinic_id = self._resolve_clinic_id(session, snapshot.source, slot)
                source_record_id = slot.external_id or slot.id or self._build_slot_hash(snapshot.source, doctor_id, slot)
                internal_id = self._resolve_internal_slot_id(snapshot.source, source_record_id, doctor_id, slot)
                slot_orm = self._get_or_create_slot(
                    session=session,
                    source=snapshot.source,
                    source_record_id=source_record_id,
                    internal_id=internal_id,
                )
                self._apply_slot(
                    slot_orm=slot_orm,
                    slot=slot,
                    doctor_id=doctor_id,
                    clinic_id=clinic_id,
                    source=snapshot.source,
                    source_record_id=source_record_id,
                )
                slots_upserted += 1
                seen_source_record_ids.add(source_record_id)
                touched_doctor_ids.add(doctor_id)

            if touched_doctor_ids:
                self._invalidate_missing_slots(
                    session=session,
                    source=snapshot.source,
                    touched_doctor_ids=touched_doctor_ids,
                    seen_source_record_ids=seen_source_record_ids,
                )

        return AvailabilitySyncResult(
            source=snapshot.source,
            mode=self.settings.scheduling_source,
            slots_upserted=slots_upserted,
            reference_data_backend="postgres",
        )

    def _build_client(self) -> SchedulingClient:
        if self.settings.scheduling_source == "fhir":
            return FHIRSchedulingClient(
                base_url=self.settings.scheduling_api_url
                or "https://hapi.fhir.org/baseR4/Slot",
                api_key=self.settings.scheduling_api_key,
                api_key_header=self.settings.scheduling_api_key_header,
                timeout_seconds=self.settings.scheduling_timeout_seconds,
                count=self.settings.scheduling_fhir_count,
            )
        if self.settings.scheduling_source == "http":
            if not self.settings.scheduling_api_url:
                raise RuntimeError("Set SCHEDULING_API_URL before running HTTP scheduling sync.")
            return HTTPSchedulingClient(
                base_url=self.settings.scheduling_api_url,
                api_key=self.settings.scheduling_api_key,
                api_key_header=self.settings.scheduling_api_key_header,
                timeout_seconds=self.settings.scheduling_timeout_seconds,
            )

        snapshot_file = self.settings.scheduling_snapshot_file
        if snapshot_file is None:
            snapshot_file = self.settings.mock_data_dir / "provider_availability_snapshot.json"
        return SnapshotSchedulingClient(snapshot_file=snapshot_file)

    @staticmethod
    def _resolve_doctor_id(session, source: str, slot: AvailabilitySlotPayload) -> str:
        if slot.doctor_id:
            doctor = session.get(DoctorORM, slot.doctor_id)
            if doctor is not None:
                return doctor.id
        if slot.doctor_external_id:
            doctors = session.scalars(
                select(DoctorORM).where(
                    DoctorORM.source_record_id == slot.doctor_external_id,
                )
            ).all()
            if len(doctors) == 1:
                return doctors[0].id
            source_scoped_doctors = [doctor for doctor in doctors if doctor.source == source]
            if len(source_scoped_doctors) == 1:
                return source_scoped_doctors[0].id
            if slot.doctor_name:
                normalized_target = AvailabilitySyncService._normalize_doctor_name(slot.doctor_name)
                named_matches = [
                    doctor
                    for doctor in doctors
                    if AvailabilitySyncService._normalize_doctor_name(doctor.name) == normalized_target
                ]
                if len(named_matches) == 1:
                    return named_matches[0].id
        if slot.doctor_name:
            matched_doctor = AvailabilitySyncService._match_doctor_by_name(session, slot.doctor_name)
            if matched_doctor is not None:
                return matched_doctor.id
        raise RuntimeError(f"Could not resolve doctor for slot {slot.external_id or slot.id or slot.start}.")

    @staticmethod
    def _resolve_clinic_id(session, source: str, slot: AvailabilitySlotPayload) -> str | None:
        if slot.clinic_id:
            clinic = session.get(ClinicORM, slot.clinic_id)
            if clinic is not None:
                return clinic.id
        if slot.clinic_external_id:
            clinic = session.execute(
                select(ClinicORM).where(
                    ClinicORM.source == source,
                    ClinicORM.source_record_id == slot.clinic_external_id,
                )
            ).scalar_one_or_none()
            if clinic is not None:
                return clinic.id
        return None

    @staticmethod
    def _build_slot_hash(source: str, doctor_id: str, slot: AvailabilitySlotPayload) -> str:
        payload = f"{source}|{doctor_id}|{slot.start}|{slot.end}|{slot.appointment_mode or ''}"
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:20]

    @staticmethod
    def _resolve_internal_slot_id(
        source: str,
        source_record_id: str,
        doctor_id: str,
        slot: AvailabilitySlotPayload,
    ) -> str:
        if slot.id:
            return slot.id
        return f"slot-{source}-{doctor_id}-{source_record_id}"[:140]

    @staticmethod
    def _get_or_create_slot(session, source: str, source_record_id: str, internal_id: str) -> AvailabilitySlotORM:
        slot = session.execute(
            select(AvailabilitySlotORM).where(
                AvailabilitySlotORM.source == source,
                AvailabilitySlotORM.source_record_id == source_record_id,
            )
        ).scalar_one_or_none()
        if slot is None:
            slot = session.get(AvailabilitySlotORM, internal_id)
        if slot is None:
            slot = AvailabilitySlotORM(id=internal_id)
            session.add(slot)
        return slot

    @staticmethod
    def _apply_slot(
        slot_orm: AvailabilitySlotORM,
        slot: AvailabilitySlotPayload,
        doctor_id: str,
        clinic_id: str | None,
        source: str,
        source_record_id: str,
    ) -> None:
        starts_at = datetime.fromisoformat(slot.start.replace("Z", "+00:00"))
        ends_at = datetime.fromisoformat(slot.end.replace("Z", "+00:00"))
        if starts_at.tzinfo is None:
            starts_at = starts_at.replace(tzinfo=UTC)
        if ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=UTC)

        slot_orm.doctor_id = doctor_id
        slot_orm.clinic_id = clinic_id
        slot_orm.starts_at = starts_at
        slot_orm.ends_at = ends_at
        slot_orm.label = slot.label or starts_at.strftime("%a %b %d, %I:%M %p")
        slot_orm.available = slot.available
        slot_orm.appointment_mode = slot.appointment_mode
        slot_orm.source = source
        slot_orm.source_record_id = source_record_id
        slot_orm.comments = slot.comments
        slot_orm.last_synced_at = datetime.now(UTC)

    @staticmethod
    def _invalidate_missing_slots(
        session,
        source: str,
        touched_doctor_ids: set[str],
        seen_source_record_ids: set[str],
    ) -> None:
        now = datetime.now(UTC)
        existing_slots = session.scalars(
            select(AvailabilitySlotORM).where(
                AvailabilitySlotORM.source == source,
                AvailabilitySlotORM.doctor_id.in_(sorted(touched_doctor_ids)),
            )
        ).all()
        for existing_slot in existing_slots:
            if existing_slot.source_record_id in seen_source_record_ids:
                continue
            existing_slot.available = False
            existing_slot.last_synced_at = now

    @staticmethod
    def _match_doctor_by_name(session, doctor_name: str) -> DoctorORM | None:
        normalized_target = AvailabilitySyncService._normalize_doctor_name(doctor_name)
        if not normalized_target:
            return None
        matches: list[DoctorORM] = []
        for doctor in session.scalars(select(DoctorORM)).all():
            if AvailabilitySyncService._normalize_doctor_name(doctor.name) == normalized_target:
                matches.append(doctor)
        if len(matches) == 1:
            return matches[0]
        return None

    @staticmethod
    def _normalize_doctor_name(name: str) -> str:
        normalized = name.lower().strip()
        normalized = re.sub(r"^dr\.?\s+", "", normalized)
        normalized = normalized.split(",", 1)[0]
        normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
        return " ".join(normalized.split())
