from __future__ import annotations

from pydantic import BaseModel


class AppointmentRecord(BaseModel):
    confirmation_id: str
    doctor_id: str
    patient_name: str
    email: str
    slot: str
    notes: str | None = None
