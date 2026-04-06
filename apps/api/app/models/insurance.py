from __future__ import annotations

from pydantic import BaseModel


class InsurancePlanRecord(BaseModel):
    id: str
    provider: str
    plan_name: str
    plan_type: str
    referral_required_for_specialists: bool
    primary_care_copay: int
    specialist_copay: int
    urgent_care_copay: int
    notes: str

