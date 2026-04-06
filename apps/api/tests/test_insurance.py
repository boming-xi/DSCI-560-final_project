from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_insurance_query_matches_known_plan() -> None:
    response = client.post(
        "/api/v1/insurance/parse",
        json={"insurance_query": "USC Aetna student PPO plan"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched"] is True
    assert payload["provider"] == "Aetna"

