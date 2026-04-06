from __future__ import annotations

from app.models.insurance import InsurancePlanRecord
from app.repositories.insurance_repo import InsuranceRepository
from app.rules.insurance_rules import insurance_notes
from app.schemas.insurance import InsuranceParseRequest, InsuranceSummary
from app.utils.parsers import normalize_text


class InsuranceService:
    def __init__(self, insurance_repo: InsuranceRepository) -> None:
        self.insurance_repo = insurance_repo

    def parse_insurance(self, request: InsuranceParseRequest) -> InsuranceSummary:
        raw_query = request.insurance_query or request.uploaded_text or ""
        plan, confidence = self.insurance_repo.match_plan(raw_query)
        return self._build_summary(plan, confidence, raw_query)

    def summarize_query(self, insurance_query: str | None) -> InsuranceSummary | None:
        if not insurance_query:
            return None
        plan, confidence = self.insurance_repo.match_plan(insurance_query)
        return self._build_summary(plan, confidence, insurance_query)

    def get_plan(self, plan_id: str | None) -> InsurancePlanRecord | None:
        if not plan_id:
            return None
        return self.insurance_repo.get_plan(plan_id)

    def _build_summary(
        self,
        plan: InsurancePlanRecord | None,
        confidence: float,
        raw_query: str,
    ) -> InsuranceSummary:
        if plan is None:
            return InsuranceSummary(
                matched=False,
                notes=[
                    "We could not confidently match that plan in the demo dataset.",
                    "You can still browse doctors, but insurance filtering will be softer.",
                ],
                match_confidence=0.0,
                normalized_query=normalize_text(raw_query),
            )
        return InsuranceSummary(
            matched=True,
            plan_id=plan.id,
            provider=plan.provider,
            plan_name=plan.plan_name,
            plan_type=plan.plan_type,
            referral_required_for_specialists=plan.referral_required_for_specialists,
            primary_care_copay=plan.primary_care_copay,
            specialist_copay=plan.specialist_copay,
            urgent_care_copay=plan.urgent_care_copay,
            notes=insurance_notes(plan, matched=True),
            match_confidence=round(confidence, 2),
            normalized_query=normalize_text(raw_query),
        )

