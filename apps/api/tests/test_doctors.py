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


def test_keck_doctor_detail_exposes_official_booking_metadata() -> None:
    response = client.get("/api/v1/doctors/keck-ron-ben-ari")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider_system"] == "Keck Medicine of USC"
    assert payload["official_profile_url"] == "https://www.keckmedicine.org/provider/ron-ben-ari/"
    assert payload["official_booking_url"] == "https://www.keckmedicine.org/provider/ron-ben-ari/"
    assert payload["booking_system_name"] == "Keck Medicine of USC scheduling"
    assert payload["pilot_region"] == "Los Angeles pilot"


def test_doctor_search_returns_expanded_official_la_shortlist() -> None:
    response = client.post(
        "/api/v1/doctors/search",
        json={
            "symptom_text": "I want a primary care doctor for preventive care and follow-up visits.",
            "location": {"latitude": 34.0224, "longitude": -118.2851},
            "top_k": 15,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["doctors"]) == 15
    assert all(doctor["official_booking_url"] for doctor in payload["doctors"])
    ids = {doctor["id"] for doctor in payload["doctors"]}
    assert "ucla-clifford-pang" in ids
    assert "ucla-sarah-kim" in ids or "ucla-noah-ravenborg" in ids
    assert "keck-ron-ben-ari" in ids or "keck-caitlin-mcauley" in ids
