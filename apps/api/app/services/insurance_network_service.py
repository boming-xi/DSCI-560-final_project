from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cached_property

from app.models.doctor import ClinicRecord, DoctorRecord
from app.schemas.doctor import InsuranceVerification
from app.schemas.insurance import InsuranceSummary
from app.schemas.insurance_advisor import InsuranceAdvisorPlanRecord
from app.services.insurance_service import InsuranceService
from app.services.official_provider_directory_service import (
    OfficialProviderDirectoryService,
)
from app.utils.parsers import normalize_text


@dataclass(slots=True)
class PlanContext:
    plan_id: str
    provider: str
    plan_name: str
    plan_type: str
    network_name: str | None
    network_url: str | None
    source: str
    doctor_search_plan_id: str | None
    referral_required_for_specialists: bool


class InsuranceNetworkService:
    def __init__(
        self,
        insurance_service: InsuranceService,
        official_provider_directory_service: OfficialProviderDirectoryService | None = None,
    ) -> None:
        self.insurance_service = insurance_service
        self.official_provider_directory_service = official_provider_directory_service
        settings = insurance_service.insurance_repo.settings
        self.marketplace_catalog_path = settings.mock_data_dir / "ca_marketplace_plans.json"

    @cached_property
    def marketplace_catalog(self) -> dict[str, InsuranceAdvisorPlanRecord]:
        if not self.marketplace_catalog_path.exists():
            return {}
        payload = json.loads(self.marketplace_catalog_path.read_text())
        records = [InsuranceAdvisorPlanRecord.model_validate(item) for item in payload]
        return {record.plan_id: record for record in records}

    def resolve_plan_context(
        self,
        *,
        selected_plan_id: str | None,
        doctor_search_plan_id: str | None,
        insurance_query: str | None,
    ) -> tuple[PlanContext | None, InsuranceSummary | None]:
        record = None
        source = None
        if selected_plan_id and selected_plan_id in self.marketplace_catalog:
            record = self.marketplace_catalog[selected_plan_id]
            source = "official_ca_marketplace_catalog"

        if record is not None:
            return self._context_from_record(
                record,
                source=source or "official_ca_marketplace_catalog",
                doctor_search_plan_id=doctor_search_plan_id,
                insurance_query=insurance_query,
            )

        effective_plan_id = doctor_search_plan_id or selected_plan_id
        summary = (
            self.insurance_service.summarize_plan_id(
                effective_plan_id,
                raw_query=insurance_query,
                match_confidence=0.95,
            )
            if effective_plan_id
            else self.insurance_service.summarize_query(insurance_query)
        )
        if summary and summary.matched and summary.plan_id:
            return (
                PlanContext(
                    plan_id=summary.plan_id,
                    provider=summary.provider or "Unknown provider",
                    plan_name=summary.plan_name or summary.plan_id,
                    plan_type=summary.plan_type or "Unknown",
                    network_name=None,
                    network_url=None,
                    source="official_marketplace_match",
                    doctor_search_plan_id=summary.plan_id,
                    referral_required_for_specialists=summary.referral_required_for_specialists,
                ),
                summary,
            )
        return None, summary

    def build_verification(
        self,
        doctor: DoctorRecord,
        clinic: ClinicRecord,
        plan_context: PlanContext | None,
    ) -> InsuranceVerification | None:
        if plan_context is None:
            return None

        official_attempted = False
        if self.official_provider_directory_service is not None:
            official_attempted = self.official_provider_directory_service.has_live_client(
                plan_context
            )
            official_match = self.official_provider_directory_service.verify(
                plan_context=plan_context,
                doctor=doctor,
                clinic=clinic,
            )
            if official_match is not None:
                return InsuranceVerification(
                    status="verified",
                    label=official_match.label,
                    reason=official_match.reason,
                    evidence=official_match.evidence,
                    network_name=plan_context.network_name,
                    network_url=official_match.network_url or plan_context.network_url,
                    source=official_match.source,
                )

        return InsuranceVerification(
            status="uncertain",
            label=(
                "Official network check not configured"
                if not official_attempted
                else "Network not verified"
            ),
            reason=(
                "The live carrier provider directory did not confirm this doctor for the selected plan."
                if official_attempted
                else "This app is currently set to show only official provider-directory confirmation, and no live carrier directory is configured for this plan yet."
            ),
            evidence=[
                f"Plan carrier: {plan_context.provider}",
                (
                    f"Plan network: {plan_context.network_name}"
                    if plan_context.network_name
                    else "No public network label was available for this plan record."
                ),
                (
                    "A live carrier provider directory was queried and did not confirm this doctor."
                    if official_attempted
                    else "No live carrier provider directory client is configured for this plan."
                ),
            ],
            network_name=plan_context.network_name,
            network_url=plan_context.network_url,
            source=plan_context.source,
        )

    def _context_from_record(
        self,
        record: InsuranceAdvisorPlanRecord,
        *,
        source: str,
        doctor_search_plan_id: str | None,
        insurance_query: str | None,
    ) -> tuple[PlanContext, InsuranceSummary]:
        fallback_plan_id = doctor_search_plan_id or record.doctor_search_plan_id or record.plan_id
        legacy_summary = self.insurance_service.summarize_plan_id(
            fallback_plan_id,
            raw_query=insurance_query or f"{record.provider or ''} {record.plan_name or ''}",
            match_confidence=0.95,
        )

        summary = InsuranceSummary(
            matched=True,
            plan_id=record.plan_id,
            provider=record.provider,
            plan_name=record.plan_name,
            plan_type=record.plan_type,
            referral_required_for_specialists=bool(
                record.referral_required_for_specialists
            ),
            primary_care_copay=legacy_summary.primary_care_copay if legacy_summary else None,
            specialist_copay=legacy_summary.specialist_copay if legacy_summary else None,
            urgent_care_copay=legacy_summary.urgent_care_copay if legacy_summary else None,
            notes=[
                "Plan context resolved from the selected insurance recommendation.",
                "Doctor in-network matching is only treated as confirmed when a live carrier provider directory verifies the doctor.",
            ],
            match_confidence=0.95,
            normalized_query=normalize_text(
                insurance_query or f"{record.provider or ''} {record.plan_name or ''}"
            ),
        )
        return (
            PlanContext(
                plan_id=record.plan_id,
                provider=record.provider or "Unknown provider",
                plan_name=record.plan_name or record.plan_id,
                plan_type=record.plan_type or "Unknown",
                network_name=record.network_name,
                network_url=record.network_url,
                source=source,
                doctor_search_plan_id=fallback_plan_id,
                referral_required_for_specialists=bool(
                    record.referral_required_for_specialists
                ),
            ),
            summary,
        )
