from __future__ import annotations

import re
from dataclasses import dataclass

import httpx
from pydantic import ValidationError
from sqlalchemy import select

from app.core.config import Settings
from app.db.models import ClinicORM, DoctorORM
from app.db.session import database_is_available, session_scope
from app.integrations.provider_directory.base import ProviderDirectoryClient
from app.integrations.provider_directory.census_geocoder import CensusGeocoderClient
from app.integrations.provider_directory.http_client import HTTPProviderDirectoryClient
from app.integrations.provider_directory.nppes_client import NPPESProviderDirectoryClient
from app.integrations.provider_directory.schemas import (
    ProviderClinicPayload,
    ProviderDoctorPayload,
)
from app.integrations.provider_directory.snapshot_client import SnapshotProviderDirectoryClient


@dataclass(slots=True)
class ProviderSyncResult:
    source: str
    mode: str
    clinics_upserted: int
    doctors_upserted: int
    reference_data_backend: str


class ProviderSyncService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def sync(self) -> ProviderSyncResult:
        if not database_is_available(self.settings.postgres_url):
            raise RuntimeError("Postgres is unavailable. Start the database before syncing providers.")

        client = self._build_client()
        try:
            snapshot = client.fetch_snapshot()
        except (FileNotFoundError, httpx.HTTPError, ValidationError, ValueError) as exc:
            raise RuntimeError(f"Provider sync failed before database upsert: {exc}") from exc

        clinics_upserted = 0
        doctors_upserted = 0
        clinic_id_map: dict[str, str] = {}

        with session_scope(self.settings.postgres_url) as session:
            for clinic in snapshot.clinics:
                clinic_record_id = clinic.external_id or clinic.id
                internal_clinic_id = self._resolve_entity_id("clinic", snapshot.source, clinic_record_id, clinic.id)
                clinic_orm = self._get_or_create_clinic(
                    session=session,
                    source=snapshot.source,
                    source_record_id=clinic_record_id or internal_clinic_id,
                    internal_id=internal_clinic_id,
                )
                self._apply_clinic(clinic_orm, clinic, snapshot.source, clinic_record_id or internal_clinic_id)
                clinics_upserted += 1
                if clinic.external_id:
                    clinic_id_map[clinic.external_id] = clinic_orm.id
                if clinic.id:
                    clinic_id_map[clinic.id] = clinic_orm.id

            for doctor in snapshot.doctors:
                clinic_internal_id = self._resolve_doctor_clinic_id(doctor, clinic_id_map)
                doctor_record_id = doctor.external_id or doctor.id
                internal_doctor_id = self._resolve_entity_id("doctor", snapshot.source, doctor_record_id, doctor.id)
                doctor_orm = self._get_or_create_doctor(
                    session=session,
                    source=snapshot.source,
                    source_record_id=doctor_record_id or internal_doctor_id,
                    internal_id=internal_doctor_id,
                )
                self._apply_doctor(
                    doctor_orm=doctor_orm,
                    doctor=doctor,
                    clinic_id=clinic_internal_id,
                    source=snapshot.source,
                    source_record_id=doctor_record_id or internal_doctor_id,
                )
                doctors_upserted += 1

        return ProviderSyncResult(
            source=snapshot.source,
            mode=self.settings.provider_directory_source,
            clinics_upserted=clinics_upserted,
            doctors_upserted=doctors_upserted,
            reference_data_backend="postgres",
        )

    def _build_client(self) -> ProviderDirectoryClient:
        if self.settings.provider_directory_source == "nppes":
            return NPPESProviderDirectoryClient(
                base_url=self.settings.provider_directory_api_url or "https://npiregistry.cms.hhs.gov/api/",
                geocoder=CensusGeocoderClient(
                    base_url=self.settings.provider_directory_geocoder_url,
                    benchmark=self.settings.provider_directory_geocoder_benchmark,
                    timeout_seconds=self.settings.provider_directory_timeout_seconds,
                ),
                timeout_seconds=self.settings.provider_directory_timeout_seconds,
                city=self.settings.provider_directory_query_city,
                state=self.settings.provider_directory_query_state,
                taxonomy_description=self.settings.provider_directory_query_taxonomy,
                limit=self.settings.provider_directory_query_limit,
                default_latitude=self.settings.provider_directory_default_latitude,
                default_longitude=self.settings.provider_directory_default_longitude,
            )
        if self.settings.provider_directory_source == "http":
            if not self.settings.provider_directory_api_url:
                raise RuntimeError("Set PROVIDER_DIRECTORY_API_URL before running HTTP provider sync.")
            return HTTPProviderDirectoryClient(
                base_url=self.settings.provider_directory_api_url,
                api_key=self.settings.provider_directory_api_key,
                api_key_header=self.settings.provider_directory_api_key_header,
                timeout_seconds=self.settings.provider_directory_timeout_seconds,
            )

        snapshot_file = self.settings.provider_directory_snapshot_file
        if snapshot_file is None:
            snapshot_file = self.settings.reference_data_dir / "provider_directory_snapshot.json"
        return SnapshotProviderDirectoryClient(snapshot_file=snapshot_file)

    @staticmethod
    def _resolve_entity_id(
        entity_type: str,
        source: str,
        source_record_id: str | None,
        explicit_id: str | None,
    ) -> str:
        if explicit_id:
            return explicit_id
        raw = source_record_id or f"{entity_type}-{source}"
        normalized = re.sub(r"[^a-z0-9]+", "-", f"{entity_type}-{source}-{raw}".lower()).strip("-")
        return normalized[:100]

    @staticmethod
    def _get_or_create_clinic(session, source: str, source_record_id: str, internal_id: str) -> ClinicORM:
        clinic = session.execute(
            select(ClinicORM).where(
                ClinicORM.source == source,
                ClinicORM.source_record_id == source_record_id,
            )
        ).scalar_one_or_none()
        if clinic is None:
            clinic = session.get(ClinicORM, internal_id)
        if clinic is None:
            clinic = ClinicORM(id=internal_id)
            session.add(clinic)
        return clinic

    @staticmethod
    def _get_or_create_doctor(session, source: str, source_record_id: str, internal_id: str) -> DoctorORM:
        doctor = session.execute(
            select(DoctorORM).where(
                DoctorORM.source == source,
                DoctorORM.source_record_id == source_record_id,
            )
        ).scalar_one_or_none()
        if doctor is None:
            doctor = session.get(DoctorORM, internal_id)
        if doctor is None:
            doctor = DoctorORM(id=internal_id)
            session.add(doctor)
        return doctor

    @staticmethod
    def _apply_clinic(clinic_orm: ClinicORM, clinic: ProviderClinicPayload, source: str, source_record_id: str) -> None:
        clinic_orm.name = clinic.name
        clinic_orm.care_types = clinic.care_types
        clinic_orm.address = clinic.address
        clinic_orm.city = clinic.city
        clinic_orm.state = clinic.state
        clinic_orm.zip_code = clinic.zip
        clinic_orm.latitude = clinic.latitude
        clinic_orm.longitude = clinic.longitude
        clinic_orm.languages = clinic.languages
        clinic_orm.open_weekends = clinic.open_weekends
        clinic_orm.urgent_care = clinic.urgent_care
        clinic_orm.phone = clinic.phone
        clinic_orm.source = source
        clinic_orm.source_record_id = source_record_id

    @staticmethod
    def _apply_doctor(
        doctor_orm: DoctorORM,
        doctor: ProviderDoctorPayload,
        clinic_id: str,
        source: str,
        source_record_id: str,
    ) -> None:
        doctor_orm.name = doctor.name
        doctor_orm.specialty = doctor.specialty
        doctor_orm.care_types = doctor.care_types
        doctor_orm.clinic_id = clinic_id
        doctor_orm.years_experience = doctor.years_experience
        doctor_orm.languages = doctor.languages
        doctor_orm.rating = doctor.rating
        doctor_orm.review_count = doctor.review_count
        doctor_orm.accepted_insurance = doctor.accepted_insurance
        doctor_orm.availability_days = doctor.availability_days
        doctor_orm.telehealth = doctor.telehealth
        doctor_orm.gender = doctor.gender
        doctor_orm.profile_blurb = doctor.profile_blurb or f"{doctor.specialty} clinician synced from {source}."
        doctor_orm.source = source
        doctor_orm.source_record_id = source_record_id

    @staticmethod
    def _resolve_doctor_clinic_id(
        doctor: ProviderDoctorPayload,
        clinic_id_map: dict[str, str],
    ) -> str:
        if doctor.clinic_external_id and doctor.clinic_external_id in clinic_id_map:
            return clinic_id_map[doctor.clinic_external_id]
        if doctor.clinic_id and doctor.clinic_id in clinic_id_map:
            return clinic_id_map[doctor.clinic_id]
        if doctor.clinic_id:
            return doctor.clinic_id
        raise RuntimeError(f"Could not resolve clinic for doctor {doctor.name}.")
