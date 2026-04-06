from __future__ import annotations

from app.models.insurance import InsurancePlanRecord

PRIMARY_SPECIALTIES = {"family medicine", "internal medicine", "urgent care"}


def requires_referral(plan: InsurancePlanRecord | None, specialty: str) -> bool:
    if plan is None:
        return False
    if not plan.referral_required_for_specialists:
        return False
    return specialty.lower() not in PRIMARY_SPECIALTIES

