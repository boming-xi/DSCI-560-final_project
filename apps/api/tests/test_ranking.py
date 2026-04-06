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

