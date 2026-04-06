from __future__ import annotations

import json
from functools import cached_property

from app.core.config import Settings
from app.models.insurance import InsurancePlanRecord
from app.utils.parsers import normalize_text, tokenize


class InsuranceRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @cached_property
    def plans(self) -> list[InsurancePlanRecord]:
        data = json.loads((self.settings.mock_data_dir / "insurance_plans.json").read_text())
        return [InsurancePlanRecord.model_validate(item) for item in data]

    def list_plans(self) -> list[InsurancePlanRecord]:
        return self.plans

    def get_plan(self, plan_id: str) -> InsurancePlanRecord | None:
        return next((plan for plan in self.plans if plan.id == plan_id), None)

    def match_plan(self, query: str | None) -> tuple[InsurancePlanRecord | None, float]:
        normalized_query = normalize_text(query)
        query_tokens = set(tokenize(normalized_query))
        if not normalized_query or not query_tokens:
            return None, 0.0

        best_plan: InsurancePlanRecord | None = None
        best_score = 0.0

        for plan in self.plans:
            candidate_text = f"{plan.provider} {plan.plan_name} {plan.plan_type} {plan.id}"
            candidate_tokens = set(tokenize(candidate_text))
            overlap = len(query_tokens & candidate_tokens)
            score = overlap / max(len(candidate_tokens), 1)
            if normalize_text(plan.provider) in normalized_query:
                score += 0.2
            if normalize_text(plan.plan_type) in normalized_query:
                score += 0.1
            if score > best_score:
                best_plan = plan
                best_score = score

        return best_plan, min(best_score, 0.99)

