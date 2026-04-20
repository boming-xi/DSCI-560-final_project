from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.core.config import Settings
from app.db.bootstrap import bootstrap_reference_data
from app.db.models import ClinicORM, DoctorORM, InsurancePlanORM
from app.db.session import session_scope
from app.repositories.doctor_repo import DoctorRepository
from app.repositories.insurance_repo import InsuranceRepository


def build_test_settings(tmp_path: Path) -> Settings:
    project_root = Path(__file__).resolve().parents[3]
    return Settings(
        api_host="127.0.0.1",
        api_port=8000,
        cors_origins=["http://localhost:3000"],
        openai_api_key=None,
        openai_chat_model="gpt-5.4-mini",
        openai_embedding_model="text-embedding-3-small",
        openai_ocr_model="gpt-5.4-mini",
        openai_reasoning_effort="low",
        openai_max_output_tokens=700,
        demo_users_file=tmp_path / "demo_users.json",
        demo_auth_secret="test-secret",
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'reference_data.db'}",
        provider_directory_source="snapshot",
        provider_directory_snapshot_file=None,
        provider_directory_api_url=None,
        provider_directory_api_key=None,
        provider_directory_api_key_header="Authorization",
        provider_directory_timeout_seconds=15.0,
        provider_directory_query_city=None,
        provider_directory_query_state=None,
        provider_directory_query_taxonomy=None,
        provider_directory_query_limit=25,
        provider_directory_geocoder_url="https://geocoding.geo.census.gov/geocoder/locations/onelineaddress",
        provider_directory_geocoder_benchmark="Public_AR_Current",
        provider_directory_default_latitude=34.0224,
        provider_directory_default_longitude=-118.2851,
        scheduling_source="snapshot",
        scheduling_snapshot_file=None,
        scheduling_api_url=None,
        scheduling_api_key=None,
        scheduling_api_key_header="Authorization",
        scheduling_timeout_seconds=15.0,
        scheduling_slot_stale_hours=24,
        scheduling_fhir_count=50,
        qdrant_url="http://localhost:6333",
        qdrant_local_path=tmp_path / "qdrant",
        qdrant_collection_prefix="documents",
        project_root=project_root,
        reference_data_dir=project_root / "packages" / "reference-data",
    )


def test_bootstrap_reference_data_seeds_database(tmp_path: Path) -> None:
    settings = build_test_settings(tmp_path)
    doctor_repo = DoctorRepository(settings)
    insurance_repo = InsuranceRepository(settings)

    assert bootstrap_reference_data(settings) is True
    assert bootstrap_reference_data(settings) is True

    with session_scope(settings.postgres_url) as session:
        clinic_ids = session.scalars(select(ClinicORM.id)).all()
        doctor_ids = session.scalars(select(DoctorORM.id)).all()
        plan_ids = session.scalars(select(InsurancePlanORM.id)).all()

    assert len(clinic_ids) == len(doctor_repo.clinics)
    assert len(doctor_ids) == len(doctor_repo.doctors)
    assert len(plan_ids) == len(insurance_repo.plans)


def test_repositories_read_from_database_after_bootstrap(tmp_path: Path) -> None:
    settings = build_test_settings(tmp_path)
    bootstrap_reference_data(settings)

    doctor_repo = DoctorRepository(settings)
    insurance_repo = InsuranceRepository(settings)

    doctor = doctor_repo.get_doctor("dr-michelle-lin")
    clinic = doctor_repo.get_clinic("clinic-union")
    matched_plan, confidence = insurance_repo.match_plan("USC Aetna Student Health PPO")

    assert doctor is not None
    assert clinic is not None
    assert doctor.clinic_id == clinic.id
    assert matched_plan is not None
    assert matched_plan.id == "usc-aetna-student"
    assert confidence > 0
