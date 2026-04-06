from __future__ import annotations

from pydantic import BaseModel, Field


class InsuranceParseRequest(BaseModel):
    insurance_query: str | None = None
    uploaded_text: str | None = None


class InsuranceSummary(BaseModel):
    matched: bool
    plan_id: str | None = None
    provider: str | None = None
    plan_name: str | None = None
    plan_type: str | None = None
    referral_required_for_specialists: bool = False
    primary_care_copay: int | None = None
    specialist_copay: int | None = None
    urgent_care_copay: int | None = None
    notes: list[str] = Field(default_factory=list)
    match_confidence: float = 0.0
    normalized_query: str | None = None

