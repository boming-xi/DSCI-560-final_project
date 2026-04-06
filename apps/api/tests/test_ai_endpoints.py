from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_endpoint_works_without_openai_key() -> None:
    response = client.post(
        "/api/v1/chat/message",
        json={
            "message": "What kind of doctor should I see for sore throat and fever?",
            "conversation": [],
            "symptom_text": "I have had a sore throat and fever for three days",
            "insurance_query": "USC Aetna student PPO",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"]
    assert payload["suggested_next_actions"]


def test_document_explainer_works_without_openai_key() -> None:
    response = client.post(
        "/api/v1/documents/explain",
        json={
            "title": "CBC note",
            "content": "CBC result shows WBC slightly elevated with mild inflammation.",
            "document_type": "lab_report",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]
    assert payload["disclaimer"]
