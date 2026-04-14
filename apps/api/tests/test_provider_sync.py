from __future__ import annotations

import json
from pathlib import Path

from app.core.config import Settings
from app.db.bootstrap import bootstrap_reference_data
from app.repositories.doctor_repo import DoctorRepository
from app.services.provider_sync_service import ProviderSyncService


def build_test_settings(tmp_path: Path, snapshot_path: Path) -> Settings:
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
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'provider_sync.db'}",
        provider_directory_source="snapshot",
        provider_directory_snapshot_file=snapshot_path,
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
        mock_data_dir=project_root / "packages" / "mock-data",
    )


def test_provider_sync_upserts_external_clinic_and_doctor(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "provider_snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "source": "test_provider_api",
                "clinics": [
                    {
                        "external_id": "clinic-900",
                        "name": "Sunset Family Health",
                        "care_types": ["primary_care"],
                        "address": "900 Sunset Blvd",
                        "city": "Los Angeles",
                        "state": "CA",
                        "zip": "90026",
                        "latitude": 34.078,
                        "longitude": -118.260,
                        "languages": ["English", "Spanish"],
                        "open_weekends": True,
                        "urgent_care": False,
                        "phone": "(213) 555-0900",
                    }
                ],
                "doctors": [
                    {
                        "external_id": "doctor-900",
                        "name": "Dr. Elena Cruz",
                        "specialty": "Family Medicine",
                        "care_types": ["primary_care"],
                        "clinic_external_id": "clinic-900",
                        "years_experience": 8,
                        "languages": ["English", "Spanish"],
                        "rating": 4.8,
                        "review_count": 61,
                        "accepted_insurance": ["usc-aetna-student"],
                        "availability_days": 1,
                        "telehealth": True,
                        "gender": "Female",
                        "profile_blurb": "Imported from external provider feed.",
                    }
                ],
            }
        )
    )

    settings = build_test_settings(tmp_path, snapshot_path)
    bootstrap_reference_data(settings)

    result = ProviderSyncService(settings).sync()
    repo = DoctorRepository(settings)

    synced_doctor = next((doctor for doctor in repo.list_doctors() if doctor.name == "Dr. Elena Cruz"), None)
    synced_clinic = repo.get_clinic("clinic-test-provider-api-clinic-900")

    assert result.mode == "snapshot"
    assert result.source == "test_provider_api"
    assert result.clinics_upserted == 1
    assert result.doctors_upserted == 1
    assert synced_doctor is not None
    assert synced_doctor.clinic_id == "clinic-test-provider-api-clinic-900"
    assert synced_clinic is not None
    assert synced_clinic.name == "Sunset Family Health"
