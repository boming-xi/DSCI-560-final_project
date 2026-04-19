from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_doctor_search_returns_ranked_results() -> None:
    response = client.post(
        "/api/v1/doctors/search",
        json={
            "symptom_text": "I have had a sore throat and fever for three days",
            "insurance_query": "USC Aetna student PPO",
            "preferred_language": "Mandarin",
            "location": {"latitude": 34.0224, "longitude": -118.2851},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["doctors"]) >= 1
    assert payload["doctors"][0]["ranking_breakdown"]["total_score"] >= payload["doctors"][-1]["ranking_breakdown"]["total_score"]


def test_doctor_search_verifies_student_network_aliases() -> None:
    response = client.post(
        "/api/v1/doctors/search",
        json={
            "symptom_text": "I have had a sore throat and fever for three days",
            "insurance_query": "USC SHIP / Aetna Student Health",
            "insurance_selected_plan_id": "usc-aetna-student",
            "insurance_plan_id_override": "usc-aetna-student",
            "preferred_language": "Mandarin",
            "location": {"latitude": 34.0224, "longitude": -118.2851},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["doctors"][0]["insurance_verification"]["status"] == "verified"
    assert payload["insurance_summary"]["plan_id"] == "usc-aetna-student"


def test_doctor_search_verifies_marketplace_network_aliases() -> None:
    response = client.post(
        "/api/v1/doctors/search",
        json={
            "symptom_text": "I need help finding a dermatologist",
            "insurance_query": "Health Net Minimum Coverage Ambetter PPO",
            "insurance_selected_plan_id": "67138CA0700033",
            "insurance_plan_id_override": "blue-shield-ppo",
            "preferred_language": "English",
            "location": {"latitude": 34.0224, "longitude": -118.2851},
            "top_k": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["insurance_summary"]["plan_id"] == "67138CA0700033"
    assert any(
        doctor["insurance_verification"] and doctor["insurance_verification"]["status"] == "verified"
        for doctor in payload["doctors"]
    )
