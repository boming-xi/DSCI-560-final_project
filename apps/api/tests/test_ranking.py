from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_doctor_search_returns_ranked_results() -> None:
    response = client.post(
        "/api/v1/doctors/search",
        json={
            "symptom_text": "I have had a sore throat and fever for three days",
            "insurance_query": "Blue Shield of California Gold 80 Trio HMO",
            "insurance_selected_plan_id": "70285CA8040016",
            "preferred_language": "Mandarin",
            "location": {"latitude": 34.0224, "longitude": -118.2851},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["doctors"]) >= 1
    assert all(doctor["official_booking_url"] for doctor in payload["doctors"])
    assert payload["doctors"][0]["ranking_breakdown"]["total_score"] >= payload["doctors"][-1]["ranking_breakdown"]["total_score"]


def test_doctor_search_returns_official_only_network_statuses() -> None:
    response = client.post(
        "/api/v1/doctors/search",
        json={
            "symptom_text": "I have had a sore throat and fever for three days",
            "insurance_query": "Blue Shield of California Gold 80 Trio HMO",
            "insurance_selected_plan_id": "70285CA8040016",
            "preferred_language": "Mandarin",
            "location": {"latitude": 34.0224, "longitude": -118.2851},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["insurance_summary"]["plan_id"] == "70285CA8040016"
    assert all(
        doctor["insurance_verification"]["status"] in {"verified", "likely", "uncertain"}
        for doctor in payload["doctors"]
        if doctor["insurance_verification"]
    )


def test_doctor_search_uses_official_marketplace_plan_ids() -> None:
    response = client.post(
        "/api/v1/doctors/search",
        json={
            "symptom_text": "I need help finding a dermatologist",
            "insurance_query": "Health Net Minimum Coverage Ambetter PPO",
            "insurance_selected_plan_id": "67138CA0700033",
            "preferred_language": "English",
            "location": {"latitude": 34.0224, "longitude": -118.2851},
            "top_k": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["insurance_summary"]["plan_id"] == "67138CA0700033"
    assert payload["doctors"]
