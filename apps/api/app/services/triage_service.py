from __future__ import annotations

from app.rules.urgency_rules import evaluate_urgency
from app.schemas.symptom import SymptomTriageRequest, TriageRecommendation


class TriageService:
    def triage(self, request: SymptomTriageRequest) -> TriageRecommendation:
        result = evaluate_urgency(request.symptom_text, request.duration_days)
        return TriageRecommendation(
            urgency_level=result["urgency_level"],
            care_type=result["care_type"],
            summary=result["summary"],
            red_flags=list(result["red_flags"]),
            next_step=result["next_step"],
            safety_notice=(
                "This tool is for navigation support only and does not replace a licensed clinician."
            ),
            matched_specialties=list(result["matched_specialties"]),
        )

