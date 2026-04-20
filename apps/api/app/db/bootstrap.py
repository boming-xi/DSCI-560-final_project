from __future__ import annotations

import json
import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.base import Base
from app.db.models import ClinicORM, DoctorORM, InsurancePlanORM
from app.db.session import get_engine, session_scope
from app.models.doctor import ClinicRecord, DoctorRecord
from app.models.insurance import InsurancePlanRecord

logger = logging.getLogger(__name__)


def initialize_database(settings: Settings) -> None:
    Base.metadata.create_all(bind=get_engine(settings.postgres_url))


def bootstrap_reference_data(settings: Settings) -> bool:
    try:
        initialize_database(settings)
        with session_scope(settings.postgres_url) as session:
            existing_clinic_ids = set(session.scalars(select(ClinicORM.id)).all())
            existing_doctor_ids = set(session.scalars(select(DoctorORM.id)).all())
            existing_plan_ids = set(session.scalars(select(InsurancePlanORM.id)).all())

            clinics = _load_clinics(settings)
            doctors = _load_doctors(settings)
            plans = _load_plans(settings)

            inserted_counts = {"clinics": 0, "doctors": 0, "insurance_plans": 0}

            for clinic in clinics:
                if clinic.id in existing_clinic_ids:
                    continue
                session.add(_to_clinic_orm(clinic))
                inserted_counts["clinics"] += 1

            for doctor in doctors:
                if doctor.id in existing_doctor_ids:
                    continue
                session.add(_to_doctor_orm(doctor))
                inserted_counts["doctors"] += 1

            for plan in plans:
                if plan.id in existing_plan_ids:
                    continue
                session.add(_to_plan_orm(plan))
                inserted_counts["insurance_plans"] += 1

        if any(inserted_counts.values()):
            logger.info("Bootstrapped reference data into database: %s", inserted_counts)
        else:
            logger.info("Reference data already present in database; skipping bootstrap.")
        return True
    except SQLAlchemyError as exc:
        logger.warning(
            "Database bootstrap unavailable at %s, continuing with JSON fallback: %s",
            settings.postgres_url,
            exc,
        )
        return False


def _load_clinics(settings: Settings) -> list[ClinicRecord]:
    data = json.loads((settings.reference_data_dir / "clinics.json").read_text())
    return [ClinicRecord.model_validate(item) for item in data]


def _load_doctors(settings: Settings) -> list[DoctorRecord]:
    data = json.loads((settings.reference_data_dir / "doctors.json").read_text())
    return [DoctorRecord.model_validate(item) for item in data]


def _load_plans(settings: Settings) -> list[InsurancePlanRecord]:
    data = json.loads((settings.reference_data_dir / "insurance_plans.json").read_text())
    return [InsurancePlanRecord.model_validate(item) for item in data]


def _to_clinic_orm(clinic: ClinicRecord) -> ClinicORM:
    return ClinicORM(
        id=clinic.id,
        name=clinic.name,
        care_types=clinic.care_types,
        address=clinic.address,
        city=clinic.city,
        state=clinic.state,
        zip_code=clinic.zip,
        latitude=clinic.latitude,
        longitude=clinic.longitude,
        languages=clinic.languages,
        open_weekends=clinic.open_weekends,
        urgent_care=clinic.urgent_care,
        phone=clinic.phone,
        source="mock_data",
        source_record_id=clinic.id,
    )


def _to_doctor_orm(doctor: DoctorRecord) -> DoctorORM:
    return DoctorORM(
        id=doctor.id,
        name=doctor.name,
        specialty=doctor.specialty,
        care_types=doctor.care_types,
        clinic_id=doctor.clinic_id,
        years_experience=doctor.years_experience,
        languages=doctor.languages,
        rating=doctor.rating,
        review_count=doctor.review_count,
        accepted_insurance=doctor.accepted_insurance,
        availability_days=doctor.availability_days,
        telehealth=doctor.telehealth,
        gender=doctor.gender,
        profile_blurb=doctor.profile_blurb,
        source="mock_data",
        source_record_id=doctor.id,
    )


def _to_plan_orm(plan: InsurancePlanRecord) -> InsurancePlanORM:
    return InsurancePlanORM(
        id=plan.id,
        provider=plan.provider,
        plan_name=plan.plan_name,
        plan_type=plan.plan_type,
        referral_required_for_specialists=plan.referral_required_for_specialists,
        primary_care_copay=plan.primary_care_copay,
        specialist_copay=plan.specialist_copay,
        urgent_care_copay=plan.urgent_care_copay,
        notes=plan.notes,
        source="mock_data",
        source_record_id=plan.id,
    )
