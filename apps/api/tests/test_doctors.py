from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_doctor_detail_includes_richer_profile_fields() -> None:
    response = client.get("/api/v1/doctors/ucla-kyung-ah-cho-anderson")

    assert response.status_code == 200
    payload = response.json()
    assert payload["clinical_focus"]
    assert payload["care_approach"]
    assert payload["education"]
    assert payload["board_certifications"]
    assert payload["visit_highlights"]
    assert payload["appointment_modes"]
    assert payload["clinic"]["languages"]
    assert payload["clinic"]["care_types"]


def test_real_provider_doctor_detail_exposes_official_booking_metadata() -> None:
    response = client.get("/api/v1/doctors/ucla-ryan-aronin")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider_system"] == "UCLA Health"
    assert payload["official_profile_url"]
    assert payload["official_booking_url"]
    assert payload["booking_system_name"] == "UCLA Health online scheduling"
    assert payload["pilot_region"] == "Los Angeles pilot"
