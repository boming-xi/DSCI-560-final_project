from __future__ import annotations

import json
from pathlib import Path

from app.core.config import Settings
from app.db.bootstrap import bootstrap_reference_data
from app.repositories.availability_repo import AvailabilityRepository
from app.repositories.booking_repo import BookingRepository
from app.repositories.doctor_repo import DoctorRepository
from app.services.availability_sync_service import AvailabilitySyncService
from app.services.booking_service import BookingService


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
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'availability_sync.db'}",
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
        scheduling_snapshot_file=snapshot_path,
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


def test_availability_sync_populates_slots_and_booking_prefers_them(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "availability_snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "source": "test_scheduling_api",
                "slots": [
                    {
                        "external_id": "slot-1",
                        "doctor_id": "dr-michelle-lin",
                        "clinic_id": "clinic-union",
                        "start": "2026-04-20T09:00:00-07:00",
                        "end": "2026-04-20T09:30:00-07:00",
                        "label": "Mon Apr 20, 09:00 AM",
                        "available": True,
                        "appointment_mode": "In person",
                        "comments": "Real slot sync test",
                    }
                ],
            }
        )
    )

    settings = build_test_settings(tmp_path, snapshot_path)
    bootstrap_reference_data(settings)

    sync_result = AvailabilitySyncService(settings).sync()
    availability_repo = AvailabilityRepository(settings)
    slots = availability_repo.list_current_slots_for_doctor("dr-michelle-lin")
    booking_service = BookingService(
        doctor_repo=DoctorRepository(settings),
        booking_repo=BookingRepository(),
        availability_repo=availability_repo,
    )
    booking_response = booking_service.get_slots("dr-michelle-lin")

    assert sync_result.slots_upserted == 1
    assert slots
    assert slots[0].source == "test_scheduling_api"
    assert booking_response.source == "external_sync"
    assert booking_response.slots[0].appointment_mode == "In person"
    assert booking_response.slots[0].source == "test_scheduling_api"
