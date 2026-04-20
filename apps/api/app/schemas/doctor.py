from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.insurance import InsuranceSummary
from app.schemas.symptom import Location, TriageRecommendation


class RankingBreakdown(BaseModel):
    specialty_score: float
    insurance_score: float
    distance_score: float
    availability_score: float
    language_score: float
    trust_score: float
    total_score: float
    summary: str


class InsuranceVerification(BaseModel):
    status: Literal["verified", "likely", "uncertain"]
    label: str
    reason: str
    evidence: list[str] = Field(default_factory=list)
    network_name: str | None = None
    network_url: str | None = None
    source: str | None = None


class ClinicInfo(BaseModel):
    id: str
    name: str
    care_types: list[str] = Field(default_factory=list)
    address: str
    city: str
    state: str
    zip: str
    phone: str
    languages: list[str] = Field(default_factory=list)
    urgent_care: bool
    open_weekends: bool


class DoctorProfile(BaseModel):
    id: str
    name: str
    specialty: str
    years_experience: int
    languages: list[str]
    rating: float
    review_count: int
    accepted_insurance: list[str] = Field(default_factory=list)
    availability_days: int
    telehealth: bool
    gender: str
    profile_blurb: str
    appointment_modes: list[str] = Field(default_factory=list)
    accepts_new_patients: bool = True
    next_opening_label: str
    clinical_focus: list[str] = Field(default_factory=list)
    care_approach: str
    education: list[str] = Field(default_factory=list)
    board_certifications: list[str] = Field(default_factory=list)
    visit_highlights: list[str] = Field(default_factory=list)
    clinic: ClinicInfo
    distance_km: float
    estimated_cost: int | None = None
    referral_required: bool = False
    insurance_verification: InsuranceVerification | None = None
    ranking_breakdown: RankingBreakdown | None = None
    provider_system: str | None = None
    official_profile_url: str | None = None
    official_booking_url: str | None = None
    official_booking_label: str | None = None
    booking_system_name: str | None = None
    booking_note: str | None = None
    pilot_region: str | None = None


class DoctorSearchRequest(BaseModel):
    symptom_text: str
    insurance_query: str | None = None
    insurance_selected_plan_id: str | None = None
    insurance_plan_id_override: str | None = None
    location: Location | None = None
    preferred_language: str | None = None
    duration_days: int | None = 1
    top_k: int = 5


class DoctorSearchResponse(BaseModel):
    triage: TriageRecommendation
    insurance_summary: InsuranceSummary | None = None
    doctors: list[DoctorProfile] = Field(default_factory=list)
    explanation: list[str] = Field(default_factory=list)
