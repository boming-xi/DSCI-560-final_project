from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_triage_returns_primary_care_for_common_symptoms() -> None:
    response = client.post(
        "/api/v1/symptoms/triage",
        json={"symptom_text": "I have had a sore throat and fever for three days", "duration_days": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["urgency_level"] in {"routine", "urgent"}
    assert "Family Medicine" in payload["matched_specialties"]


def test_triage_flags_emergency_keywords() -> None:
    response = client.post(
        "/api/v1/symptoms/triage",
        json={"symptom_text": "I have chest pain and shortness of breath", "duration_days": 1},
    )

    assert response.status_code == 200
    assert response.json()["urgency_level"] == "emergency"

