from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _demo_auth_headers() -> dict[str, str]:
    response = client.post("/api/v1/auth/demo-login", json={})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_booking_requires_authentication() -> None:
    response = client.get("/api/v1/booking/slots/dr-michelle-lin")
    assert response.status_code == 401


def test_booking_slots_and_confirmation() -> None:
    headers = _demo_auth_headers()
    slots_response = client.get("/api/v1/booking/slots/dr-michelle-lin", headers=headers)
    assert slots_response.status_code == 200
    slots = slots_response.json()["slots"]
    assert slots

    book_response = client.post(
        "/api/v1/booking/appointments",
        json={
            "doctor_id": "dr-michelle-lin",
            "patient_name": "Boming Xi",
            "email": "boming@example.com",
            "preferred_slot": slots[0]["start"],
            "notes": "Looking for the first available visit.",
        },
        headers=headers,
    )

    assert book_response.status_code == 200
    payload = book_response.json()
    assert payload["confirmation_id"].startswith("APT-")
    assert payload["doctor_name"] == "Dr. Michelle Lin"
