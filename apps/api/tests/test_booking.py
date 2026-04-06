from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_booking_slots_and_confirmation() -> None:
    slots_response = client.get("/api/v1/booking/slots/dr-michelle-lin")
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
    )

    assert book_response.status_code == 200
    payload = book_response.json()
    assert payload["confirmation_id"].startswith("APT-")
    assert payload["doctor_name"] == "Dr. Michelle Lin"
