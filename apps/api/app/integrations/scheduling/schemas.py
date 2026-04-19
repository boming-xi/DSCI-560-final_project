from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class AvailabilitySlotPayload(BaseModel):
    id: str | None = None
    external_id: str | None = None
    doctor_id: str | None = None
    doctor_external_id: str | None = None
    doctor_name: str | None = None
    clinic_id: str | None = None
    clinic_external_id: str | None = None
    start: str
    end: str
    label: str | None = None
    available: bool = True
    appointment_mode: str | None = None
    comments: str | None = None

    @model_validator(mode="after")
    def validate_references(self) -> "AvailabilitySlotPayload":
        if not self.doctor_id and not self.doctor_external_id and not self.doctor_name:
            raise ValueError(
                "Availability slot must include doctor_id, doctor_external_id, or doctor_name."
            )
        return self


class SchedulingSnapshot(BaseModel):
    source: str = "external_scheduling"
    slots: list[AvailabilitySlotPayload] = Field(default_factory=list)
