from __future__ import annotations

from pydantic import BaseModel, Field


class TimeSlot(BaseModel):
    start: str
    end: str
    label: str
    available: bool = True


class BookingSlotsResponse(BaseModel):
    doctor_id: str
    doctor_name: str
    slots: list[TimeSlot] = Field(default_factory=list)


class BookingRequest(BaseModel):
    doctor_id: str
    patient_name: str
    email: str
    preferred_slot: str
    insurance_plan_id: str | None = None
    symptom_text: str | None = None
    notes: str | None = None


class BookingConfirmation(BaseModel):
    confirmation_id: str
    doctor_id: str
    doctor_name: str
    clinic_name: str
    slot: str
    estimated_cost: int | None = None
    next_steps: list[str] = Field(default_factory=list)
