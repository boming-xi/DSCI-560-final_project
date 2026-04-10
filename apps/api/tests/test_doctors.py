from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_doctor_detail_includes_richer_profile_fields() -> None:
    response = client.get("/api/v1/doctors/dr-michelle-lin")

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
