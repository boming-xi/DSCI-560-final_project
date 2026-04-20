from __future__ import annotations

from pydantic import BaseModel, Field


class ClinicRecord(BaseModel):
    id: str
    name: str
    care_types: list[str]
    address: str
    city: str
    state: str
    zip: str
    latitude: float
    longitude: float
    languages: list[str]
    open_weekends: bool
    urgent_care: bool
    phone: str


class DoctorRecord(BaseModel):
    id: str
    name: str
    specialty: str
    care_types: list[str]
    clinic_id: str
    years_experience: int
    languages: list[str]
    rating: float
    review_count: int
    accepted_insurance: list[str] = Field(default_factory=list)
    availability_days: int
    telehealth: bool
    gender: str
    profile_blurb: str
    provider_system: str | None = None
    official_profile_url: str | None = None
    official_booking_url: str | None = None
    official_booking_label: str | None = None
    booking_system_name: str | None = None
    booking_note: str | None = None
    pilot_region: str | None = None
