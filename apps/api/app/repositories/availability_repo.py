from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.models import AvailabilitySlotORM
from app.db.session import database_is_available, session_scope


@dataclass(slots=True)
class AvailabilitySlotRecord:
    id: str
    doctor_id: str
    clinic_id: str | None
    start: datetime
    end: datetime
    label: str
    available: bool
    appointment_mode: str | None
    source: str
    source_record_id: str
    comments: str | None
    last_synced_at: datetime


class AvailabilityRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def list_current_slots_for_doctor(self, doctor_id: str) -> list[AvailabilitySlotRecord]:
        if not database_is_available(self.settings.postgres_url):
            return []
        freshness_cutoff = datetime.now(UTC) - timedelta(hours=self.settings.scheduling_slot_stale_hours)
        try:
            with session_scope(self.settings.postgres_url) as session:
                slots = session.scalars(
                    select(AvailabilitySlotORM)
                    .where(
                        AvailabilitySlotORM.doctor_id == doctor_id,
                        AvailabilitySlotORM.available.is_(True),
                        AvailabilitySlotORM.starts_at >= datetime.now(UTC),
                        AvailabilitySlotORM.last_synced_at >= freshness_cutoff,
                    )
                    .order_by(AvailabilitySlotORM.starts_at)
                ).all()
            return [self._from_orm(slot) for slot in slots]
        except SQLAlchemyError:
            return []

    def has_recent_sync_for_doctor(self, doctor_id: str) -> bool:
        if not database_is_available(self.settings.postgres_url):
            return False
        freshness_cutoff = datetime.now(UTC) - timedelta(hours=self.settings.scheduling_slot_stale_hours)
        try:
            with session_scope(self.settings.postgres_url) as session:
                slot = session.scalars(
                    select(AvailabilitySlotORM)
                    .where(
                        AvailabilitySlotORM.doctor_id == doctor_id,
                        AvailabilitySlotORM.last_synced_at >= freshness_cutoff,
                    )
                    .limit(1)
                ).first()
            return slot is not None
        except SQLAlchemyError:
            return False

    @staticmethod
    def _from_orm(slot: AvailabilitySlotORM) -> AvailabilitySlotRecord:
        return AvailabilitySlotRecord(
            id=slot.id,
            doctor_id=slot.doctor_id,
            clinic_id=slot.clinic_id,
            start=slot.starts_at,
            end=slot.ends_at,
            label=slot.label,
            available=slot.available,
            appointment_mode=slot.appointment_mode,
            source=slot.source,
            source_record_id=slot.source_record_id,
            comments=slot.comments,
            last_synced_at=slot.last_synced_at,
        )
