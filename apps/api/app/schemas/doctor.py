from __future__ import annotations

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


class ClinicInfo(BaseModel):
    id: str
    name: str
    address: str
    city: str
    state: str
    zip: str
    phone: str
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
    clinic: ClinicInfo
    distance_km: float
    estimated_cost: int | None = None
    referral_required: bool = False
    ranking_breakdown: RankingBreakdown | None = None


class DoctorSearchRequest(BaseModel):
    symptom_text: str
    insurance_query: str | None = None
    location: Location | None = None
    preferred_language: str | None = None
    duration_days: int | None = 1
    top_k: int = 5


class DoctorSearchResponse(BaseModel):
    triage: TriageRecommendation
    insurance_summary: InsuranceSummary | None = None
    doctors: list[DoctorProfile] = Field(default_factory=list)
    explanation: list[str] = Field(default_factory=list)

