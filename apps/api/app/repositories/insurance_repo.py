from __future__ import annotations

import json
import logging
from functools import cached_property

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.models import InsurancePlanORM
from app.db.session import database_is_available, session_scope
from app.models.insurance import InsurancePlanRecord
from app.utils.parsers import normalize_text, tokenize

logger = logging.getLogger(__name__)


class InsuranceRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @cached_property
    def plans(self) -> list[InsurancePlanRecord]:
        data = json.loads((self.settings.mock_data_dir / "insurance_plans.json").read_text())
        return [InsurancePlanRecord.model_validate(item) for item in data]

    def list_plans(self) -> list[InsurancePlanRecord]:
        plans = self._list_plans_from_db()
        if plans:
            return plans
        return self.plans

    def get_plan(self, plan_id: str) -> InsurancePlanRecord | None:
        plan = self._get_plan_from_db(plan_id)
        if plan is not None:
            return plan
        return next((plan for plan in self.plans if plan.id == plan_id), None)

    def match_plan(self, query: str | None) -> tuple[InsurancePlanRecord | None, float]:
        normalized_query = normalize_text(query)
        query_tokens = set(tokenize(normalized_query))
        if not normalized_query or not query_tokens:
            return None, 0.0

        best_plan: InsurancePlanRecord | None = None
        best_score = 0.0

        for plan in self.list_plans():
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

    @cached_property
    def _database_ready(self) -> bool:
        return database_is_available(self.settings.postgres_url)

    def _list_plans_from_db(self) -> list[InsurancePlanRecord]:
        if not self._database_ready:
            return []
        try:
            with session_scope(self.settings.postgres_url) as session:
                plans = session.scalars(select(InsurancePlanORM).order_by(InsurancePlanORM.provider)).all()
            return [self._plan_from_orm(plan) for plan in plans]
        except SQLAlchemyError as exc:
            logger.warning("Insurance repository falling back to JSON fixtures: %s", exc)
            return []

    def _get_plan_from_db(self, plan_id: str) -> InsurancePlanRecord | None:
        if not self._database_ready:
            return None
        try:
            with session_scope(self.settings.postgres_url) as session:
                plan = session.get(InsurancePlanORM, plan_id)
            return self._plan_from_orm(plan) if plan else None
        except SQLAlchemyError as exc:
            logger.warning("Insurance detail falling back to JSON fixtures: %s", exc)
            return None

    @staticmethod
    def _plan_from_orm(plan: InsurancePlanORM) -> InsurancePlanRecord:
        return InsurancePlanRecord(
            id=plan.id,
            provider=plan.provider,
            plan_name=plan.plan_name,
            plan_type=plan.plan_type,
            referral_required_for_specialists=plan.referral_required_for_specialists,
            primary_care_copay=plan.primary_care_copay,
            specialist_copay=plan.specialist_copay,
            urgent_care_copay=plan.urgent_care_copay,
            notes=plan.notes,
        )
