from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_doctor_decision_group_chat_returns_recommendation() -> None:
    search_response = client.post(
        "/api/v1/doctors/search",
        json={
            "symptom_text": "I need help finding a primary care doctor for a sore throat and fever",
            "insurance_query": "Blue Shield of California Gold 80 Trio HMO",
            "insurance_selected_plan_id": "70285CA8040016",
            "preferred_language": "Mandarin",
            "location": {"latitude": 34.0224, "longitude": -118.2851},
            "duration_days": 1,
            "top_k": 3,
        },
    )
    assert search_response.status_code == 200
    doctors = search_response.json()["doctors"]

    auth_response = client.post("/api/v1/auth/demo-login", json={})
    token = auth_response.json()["access_token"]

    response = client.post(
        "/api/v1/doctors/advisor/message",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "I care most about insurance confidence and the earliest appointment.",
            "conversation": [],
            "doctors": doctors,
            "symptom_text": "I need help finding a primary care doctor for a sore throat and fever",
            "insurance_query": "Blue Shield of California Gold 80 Trio HMO",
            "preferred_language": "Mandarin",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommended_doctor_id"]
    assert len(payload["group_messages"]) == 3
    assert payload["group_messages"][0]["speaker"] == "Fit Analyst"
    assert payload["shared_brief"]["shared_context_confirmed"] is True
    assert payload["shared_brief"]["shortlist_names"]
    assert payload["shared_brief"]["priority_labels"]


def test_doctor_decision_uses_priorities_from_previous_user_turns() -> None:
    search_response = client.post(
        "/api/v1/doctors/search",
        json={
            "symptom_text": "I need a primary care doctor for a sore throat and fever",
            "insurance_query": "Blue Shield of California Gold 80 Trio HMO",
            "insurance_selected_plan_id": "70285CA8040016",
            "preferred_language": "Mandarin",
            "location": {"latitude": 34.0224, "longitude": -118.2851},
            "duration_days": 1,
            "top_k": 3,
        },
    )
    doctors = search_response.json()["doctors"]

    auth_response = client.post("/api/v1/auth/demo-login", json={})
    token = auth_response.json()["access_token"]

    response = client.post(
        "/api/v1/doctors/advisor/message",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Who should I choose if I mainly care about the overall balance now?",
            "conversation": [
                {
                    "role": "user",
                    "speaker": "You",
                    "content": "Language support matters a lot to me and I want someone who explains things clearly.",
                }
            ],
            "doctors": doctors,
            "symptom_text": "I need a primary care doctor for a sore throat and fever",
            "insurance_query": "Blue Shield of California Gold 80 Trio HMO",
            "preferred_language": "Mandarin",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "Mandarin support" in payload["shared_brief"]["priority_labels"]
    assert "clear explanations" in payload["shared_brief"]["priority_labels"]
