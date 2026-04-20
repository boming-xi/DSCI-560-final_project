from __future__ import annotations

import json
from functools import cached_property

from app.models.insurance import InsurancePlanRecord
from app.repositories.insurance_repo import InsuranceRepository
from app.schemas.insurance_advisor import InsuranceAdvisorPlanRecord
from app.schemas.insurance import InsuranceParseRequest, InsuranceSummary
from app.utils.parsers import normalize_text, tokenize


class InsuranceService:
    def __init__(self, insurance_repo: InsuranceRepository) -> None:
        self.insurance_repo = insurance_repo
        self.marketplace_catalog_path = (
            insurance_repo.settings.reference_data_dir / "ca_marketplace_plans.json"
        )

    @cached_property
    def official_marketplace_catalog(self) -> list[InsuranceAdvisorPlanRecord]:
        if not self.marketplace_catalog_path.exists():
            return []
        payload = json.loads(self.marketplace_catalog_path.read_text())
        return [InsuranceAdvisorPlanRecord.model_validate(item) for item in payload]

    def parse_insurance(self, request: InsuranceParseRequest) -> InsuranceSummary:
        raw_query = request.insurance_query or request.uploaded_text or ""
        record, confidence = self._match_official_marketplace_record(raw_query)
        return self._build_official_summary(record, confidence, raw_query)

    def summarize_query(self, insurance_query: str | None) -> InsuranceSummary | None:
        if not insurance_query:
            return None
        record, confidence = self._match_official_marketplace_record(insurance_query)
        return self._build_official_summary(record, confidence, insurance_query)

    def get_plan(self, plan_id: str | None) -> InsurancePlanRecord | None:
        if not plan_id:
            return None
        return self.insurance_repo.get_plan(plan_id)

    def summarize_plan_id(
        self,
        plan_id: str | None,
        *,
        raw_query: str | None = None,
        match_confidence: float = 0.99,
    ) -> InsuranceSummary | None:
        if not plan_id:
            return None
        record = next(
            (item for item in self.official_marketplace_catalog if item.plan_id == plan_id),
            None,
        )
        if record is None:
            return None
        return self._build_official_summary(
            record,
            match_confidence,
            raw_query or f"{record.provider or ''} {record.plan_name or ''}",
        )

    def _match_official_marketplace_record(
        self,
        raw_query: str,
    ) -> tuple[InsuranceAdvisorPlanRecord | None, float]:
        normalized_query = normalize_text(raw_query)
        query_tokens = set(tokenize(normalized_query))
        if not normalized_query or not query_tokens:
            return None, 0.0

        best_record: InsuranceAdvisorPlanRecord | None = None
        best_score = 0.0

        for record in self.official_marketplace_catalog:
            candidate_text = " ".join(
                filter(
                    None,
                    [
                        record.provider,
                        record.plan_name,
                        record.plan_type,
                        record.network_name,
                        record.metal_level,
                        record.plan_id,
                    ],
                )
            )
            candidate_tokens = set(tokenize(candidate_text))
            overlap = len(query_tokens & candidate_tokens)
            score = overlap / max(len(candidate_tokens), 1)
            if record.provider and normalize_text(record.provider) in normalized_query:
                score += 0.2
            if record.plan_type and normalize_text(record.plan_type) in normalized_query:
                score += 0.1
            if record.network_name and normalize_text(record.network_name) in normalized_query:
                score += 0.15
            if score > best_score:
                best_record = record
                best_score = score

        return best_record, min(best_score, 0.99)

    def _build_official_summary(
        self,
        record: InsuranceAdvisorPlanRecord | None,
        confidence: float,
        raw_query: str,
    ) -> InsuranceSummary:
        if record is None:
            return InsuranceSummary(
                matched=False,
                notes=[
                    "We could not confirm that insurance against the current official California marketplace plan catalog.",
                    "Right now the app only returns official marketplace plan matches and official provider-system doctor results.",
                ],
                match_confidence=0.0,
                normalized_query=normalize_text(raw_query),
            )
        return InsuranceSummary(
            matched=True,
            plan_id=record.plan_id,
            provider=record.provider,
            plan_name=record.plan_name,
            plan_type=record.plan_type,
            referral_required_for_specialists=bool(record.referral_required_for_specialists),
            primary_care_copay=None,
            specialist_copay=None,
            urgent_care_copay=None,
            notes=[
                "Matched against the official California marketplace plan catalog.",
                "Confirm final pricing, subsidies, network participation, and enrollment details on the carrier or Covered California site.",
            ],
            match_confidence=round(confidence, 2),
            normalized_query=normalize_text(raw_query),
        )
