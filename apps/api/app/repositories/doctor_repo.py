from __future__ import annotations

import json
import logging
from functools import cached_property

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.models import ClinicORM, DoctorORM
from app.db.session import database_is_available, session_scope
from app.models.doctor import ClinicRecord, DoctorRecord

logger = logging.getLogger(__name__)


class DoctorRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @cached_property
    def clinics(self) -> list[ClinicRecord]:
        data = json.loads((self.settings.mock_data_dir / "clinics.json").read_text())
        return [ClinicRecord.model_validate(item) for item in data]

    @cached_property
    def doctors(self) -> list[DoctorRecord]:
        data = json.loads((self.settings.mock_data_dir / "doctors.json").read_text())
        return [DoctorRecord.model_validate(item) for item in data]

    def list_doctors(self) -> list[DoctorRecord]:
        doctors = self._list_doctors_from_db()
        if doctors:
            return doctors
        return self.doctors

    def list_clinics(self) -> list[ClinicRecord]:
        clinics = self._list_clinics_from_db()
        if clinics:
            return clinics
        return self.clinics

    def get_doctor(self, doctor_id: str) -> DoctorRecord | None:
        doctor = self._get_doctor_from_db(doctor_id)
        if doctor is not None:
            return doctor
        return next((doctor for doctor in self.doctors if doctor.id == doctor_id), None)

    def get_clinic(self, clinic_id: str) -> ClinicRecord | None:
        clinic = self._get_clinic_from_db(clinic_id)
        if clinic is not None:
            return clinic
        return next((clinic for clinic in self.clinics if clinic.id == clinic_id), None)

    def _database_ready(self) -> bool:
        return database_is_available(self.settings.postgres_url)

    def _list_doctors_from_db(self) -> list[DoctorRecord]:
        if not self._database_ready():
            return []
        try:
            with session_scope(self.settings.postgres_url) as session:
                doctors = session.scalars(select(DoctorORM).order_by(DoctorORM.name)).all()
            return [self._doctor_from_orm(doctor) for doctor in doctors]
        except SQLAlchemyError as exc:
            logger.warning("Doctor repository falling back to JSON fixtures: %s", exc)
            return []

    def _list_clinics_from_db(self) -> list[ClinicRecord]:
        if not self._database_ready():
            return []
        try:
            with session_scope(self.settings.postgres_url) as session:
                clinics = session.scalars(select(ClinicORM).order_by(ClinicORM.name)).all()
            return [self._clinic_from_orm(clinic) for clinic in clinics]
        except SQLAlchemyError as exc:
            logger.warning("Clinic repository falling back to JSON fixtures: %s", exc)
            return []

    def _get_doctor_from_db(self, doctor_id: str) -> DoctorRecord | None:
        if not self._database_ready():
            return None
        try:
            with session_scope(self.settings.postgres_url) as session:
                doctor = session.get(DoctorORM, doctor_id)
            return self._doctor_from_orm(doctor) if doctor else None
        except SQLAlchemyError as exc:
            logger.warning("Doctor detail falling back to JSON fixtures: %s", exc)
            return None

    def _get_clinic_from_db(self, clinic_id: str) -> ClinicRecord | None:
        if not self._database_ready():
            return None
        try:
            with session_scope(self.settings.postgres_url) as session:
                clinic = session.get(ClinicORM, clinic_id)
            return self._clinic_from_orm(clinic) if clinic else None
        except SQLAlchemyError as exc:
            logger.warning("Clinic detail falling back to JSON fixtures: %s", exc)
            return None

    @staticmethod
    def _clinic_from_orm(clinic: ClinicORM) -> ClinicRecord:
        return ClinicRecord(
            id=clinic.id,
            name=clinic.name,
            care_types=list(clinic.care_types or []),
            address=clinic.address,
            city=clinic.city,
            state=clinic.state,
            zip=clinic.zip_code,
            latitude=clinic.latitude,
            longitude=clinic.longitude,
            languages=list(clinic.languages or []),
            open_weekends=clinic.open_weekends,
            urgent_care=clinic.urgent_care,
            phone=clinic.phone,
        )

    @staticmethod
    def _doctor_from_orm(doctor: DoctorORM) -> DoctorRecord:
        return DoctorRecord(
            id=doctor.id,
            name=doctor.name,
            specialty=doctor.specialty,
            care_types=list(doctor.care_types or []),
            clinic_id=doctor.clinic_id,
            years_experience=doctor.years_experience,
            languages=list(doctor.languages or []),
            rating=doctor.rating,
            review_count=doctor.review_count,
            accepted_insurance=list(doctor.accepted_insurance or []),
            availability_days=doctor.availability_days,
            telehealth=doctor.telehealth,
            gender=doctor.gender,
            profile_blurb=doctor.profile_blurb,
        )
