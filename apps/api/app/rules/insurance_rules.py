from __future__ import annotations

from app.models.doctor import DoctorRecord
from app.models.insurance import InsurancePlanRecord


def compute_estimated_cost(plan: InsurancePlanRecord | None, doctor: DoctorRecord) -> int | None:
    if plan is None:
        return None
    specialty = doctor.specialty.lower()
    if "urgent" in specialty:
        return plan.urgent_care_copay
    if specialty in {"family medicine", "internal medicine"}:
        return plan.primary_care_copay
    return plan.specialist_copay


def insurance_fit_score(plan: InsurancePlanRecord | None, doctor: DoctorRecord) -> float:
    if plan is None:
        return 0.45
    return 1.0 if plan.id in doctor.accepted_insurance else 0.05


def insurance_notes(plan: InsurancePlanRecord | None, matched: bool) -> list[str]:
    if plan is None:
        return ["No insurance plan matched, so cost estimates are approximate."]
    notes = [plan.notes]
    if matched:
        notes.append("Matched an in-network style plan from the mock data catalog.")
    else:
        notes.append("Plan matched, but not every doctor shown is necessarily in-network.")
    return notes

