from __future__ import annotations

from app.models.doctor import DoctorRecord
from app.models.insurance import InsurancePlanRecord
from app.schemas.doctor import InsuranceVerification


def compute_estimated_cost(plan: InsurancePlanRecord | None, doctor: DoctorRecord) -> int | None:
    if plan is None:
        return None
    specialty = doctor.specialty.lower()
    if "urgent" in specialty:
        return plan.urgent_care_copay
    if specialty in {"family medicine", "internal medicine"}:
        return plan.primary_care_copay
    return plan.specialist_copay


def insurance_fit_score(
    plan: InsurancePlanRecord | None,
    doctor: DoctorRecord,
    verification: InsuranceVerification | None = None,
) -> float:
    if verification is not None:
        if verification.status == "verified":
            return 1.0
        if verification.status == "likely":
            return 0.78
        return 0.12
    if plan is None:
        return 0.45
    return 1.0 if plan.id in doctor.accepted_insurance else 0.05


def insurance_notes(plan: InsurancePlanRecord | None, matched: bool) -> list[str]:
    if plan is None:
        return ["No insurance plan matched, so cost estimates are approximate."]
    notes = [plan.notes]
    if matched:
        notes.append("Matched a structured insurance plan record.")
    else:
        notes.append("Plan matched, but not every doctor shown is necessarily in-network.")
    return notes
