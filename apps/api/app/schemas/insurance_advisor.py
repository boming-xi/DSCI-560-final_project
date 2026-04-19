from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.chat import ChatTurn
from app.schemas.insurance import InsuranceSummary

CoverageChannel = Literal["student", "marketplace", "employer", "unsure"]
MonthlyBudget = Literal["low", "medium", "high"]
CareUsage = Literal["low", "moderate", "high"]
DeductibleBand = Literal["low", "medium", "high"]
PremiumBand = Literal["low", "medium", "high"]
NetworkFlexibility = Literal["low", "high"]


class InsuranceAdvisorProfile(BaseModel):
    age: int | None = None
    state: str | None = None
    zip_code: str | None = None
    household_size: int | None = None
    income_band: str | None = None
    coverage_channel: CoverageChannel | None = None
    monthly_budget: MonthlyBudget | None = None
    care_usage: CareUsage | None = None
    referrals_ok: bool | None = None
    keep_existing_doctors: bool | None = None
    has_prescriptions: bool | None = None
    preferred_language: str | None = None


class InsuranceAdvisorSpeakerMessage(BaseModel):
    speaker: Literal["Navigator", "Eligibility Checker", "Plan Matcher"]
    content: str


class InsuranceAdvisorPlanRecord(BaseModel):
    plan_id: str
    provider: str | None = None
    plan_name: str | None = None
    plan_type: str | None = None
    network_name: str | None = None
    metal_level: str | None = None
    coverage_channels: list[CoverageChannel] = Field(default_factory=list)
    service_states: list[str] = Field(default_factory=list)
    supported_zip_codes: list[str] = Field(default_factory=list)
    service_counties: list[str] = Field(default_factory=list)
    monthly_premium_band: PremiumBand
    monthly_premium_amount: float | None = None
    monthly_premium_samples: dict[str, float] = Field(default_factory=dict)
    deductible_band: DeductibleBand
    deductible_amount: int | None = None
    out_of_pocket_max_amount: int | None = None
    network_flexibility: NetworkFlexibility
    care_usage_fit: list[CareUsage] = Field(default_factory=list)
    prescription_support: Literal["moderate", "strong"] = "moderate"
    quality_band: Literal["solid", "strong"] = "solid"
    quality_rating: float | None = None
    referral_required_for_specialists: bool | None = None
    advisor_blurb: str
    ideal_for: list[str] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)
    purchase_url: str | None = None
    purchase_cta_label: str | None = None
    source_url: str | None = None
    quality_source_url: str | None = None
    network_url: str | None = None
    doctor_search_plan_id: str | None = None


class InsuranceAdvisorRecommendation(BaseModel):
    plan_id: str
    doctor_search_plan_id: str | None = None
    provider: str
    plan_name: str
    plan_type: str
    network_name: str | None = None
    metal_level: str | None = None
    insurance_query: str
    fit_score: float
    confidence_label: Literal["early", "good", "strong"]
    monthly_premium_band: PremiumBand
    monthly_premium_amount: float | None = None
    deductible_band: DeductibleBand
    deductible_amount: int | None = None
    out_of_pocket_max_amount: int | None = None
    network_flexibility: NetworkFlexibility
    quality_rating: float | None = None
    advisor_blurb: str
    reasons: list[str] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)
    ideal_for: list[str] = Field(default_factory=list)
    purchase_url: str | None = None
    purchase_cta_label: str | None = None
    source_url: str | None = None
    network_url: str | None = None
    insurance_summary: InsuranceSummary


class InsuranceAdvisorMessageRequest(BaseModel):
    message: str
    conversation: list[ChatTurn] = Field(default_factory=list)
    profile: InsuranceAdvisorProfile | None = None


class InsuranceAdvisorMessageResponse(BaseModel):
    profile: InsuranceAdvisorProfile
    profile_summary: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    readiness_label: Literal["intake", "narrowing", "recommended"]
    group_messages: list[InsuranceAdvisorSpeakerMessage] = Field(default_factory=list)
    recommendations: list[InsuranceAdvisorRecommendation] = Field(default_factory=list)
    suggested_prompts: list[str] = Field(default_factory=list)
    disclaimer: str
