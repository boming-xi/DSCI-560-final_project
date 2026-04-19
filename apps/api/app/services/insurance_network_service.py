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
from app.utils.parsers import normalize_text, tokenize


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
        self.legacy_catalog_path = settings.mock_data_dir / "insurance_advisor_catalog.json"
        self.marketplace_catalog_path = settings.mock_data_dir / "ca_marketplace_plans.json"

    @cached_property
    def legacy_catalog(self) -> dict[str, InsuranceAdvisorPlanRecord]:
        payload = json.loads(self.legacy_catalog_path.read_text())
        records = [InsuranceAdvisorPlanRecord.model_validate(item) for item in payload]
        return {record.plan_id: record for record in records}

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
            source = "ca_marketplace_catalog"
        elif selected_plan_id and selected_plan_id in self.legacy_catalog:
            record = self.legacy_catalog[selected_plan_id]
            source = "advisor_catalog"

        if record is not None:
            return self._context_from_record(
                record,
                source=source or "advisor_catalog",
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
                    source="legacy_plan_match",
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

        normalized_entries = self._doctor_entries(doctor)
        if not normalized_entries:
            evidence = ["No accepted insurance or network aliases were stored on this provider record."]
            if official_attempted:
                evidence.append(
                    "A live carrier provider directory was queried, but it did not return a matching record for this doctor and clinic."
                )
            return InsuranceVerification(
                status="uncertain",
                label="No network evidence",
                reason="This doctor record does not include carrier or network participation details yet.",
                evidence=evidence,
                network_name=plan_context.network_name,
                network_url=plan_context.network_url,
                source=plan_context.source,
            )

        exact_aliases = self._exact_aliases(plan_context)
        for alias, label in exact_aliases:
            normalized_alias = normalize_text(alias)
            if not normalized_alias:
                continue
            matched_entry = self._match_alias(normalized_alias, normalized_entries)
            if matched_entry:
                if label == "legacy plan id":
                    status = "demo"
                elif label == "carrier":
                    status = "likely"
                else:
                    status = "verified"
                return InsuranceVerification(
                    status=status,
                    label=(
                        "Verified in-network"
                        if status == "verified"
                        else "Carrier-level match"
                        if status == "likely"
                        else "Compatible demo mapping"
                    ),
                    reason=(
                        f"Matched this doctor to the selected plan through {label}: {matched_entry}."
                    ),
                    evidence=self._with_official_fallback_note(
                        [
                            f"Selected plan evidence: {alias}",
                            f"Doctor record includes: {matched_entry}",
                        ],
                        official_attempted=official_attempted,
                    ),
                    network_name=plan_context.network_name,
                    network_url=plan_context.network_url,
                    source=plan_context.source,
                )

        provider_match = self._provider_level_match(plan_context.provider, normalized_entries)
        if provider_match:
            return InsuranceVerification(
                status="likely",
                label="Carrier-level match",
                reason=(
                    f"The doctor record references {provider_match}, which matches the carrier for the selected plan."
                ),
                evidence=self._with_official_fallback_note(
                    [
                        f"Plan carrier: {plan_context.provider}",
                        f"Doctor record entry: {provider_match}",
                    ],
                    official_attempted=official_attempted,
                ),
                network_name=plan_context.network_name,
                network_url=plan_context.network_url,
                source=plan_context.source,
            )

        return InsuranceVerification(
            status="uncertain",
            label="Network not verified",
            reason=(
                "The live carrier directory did not confirm this doctor, and the stored carrier or network aliases also did not match."
                if official_attempted
                else "I could not match this doctor to the selected plan's stored carrier or network aliases."
            ),
            evidence=self._with_official_fallback_note(
                [
                    f"Checked carrier {plan_context.provider}",
                    (
                        f"Checked network {plan_context.network_name}"
                        if plan_context.network_name
                        else "No network alias was available for this plan."
                    ),
                ],
                official_attempted=official_attempted,
            ),
            network_name=plan_context.network_name,
            network_url=plan_context.network_url,
            source=plan_context.source,
        )

    @staticmethod
    def _with_official_fallback_note(
        evidence: list[str],
        *,
        official_attempted: bool,
    ) -> list[str]:
        if official_attempted:
            return [
                *evidence,
                "Live carrier provider directory check did not confirm a match, so this result falls back to stored local network evidence.",
            ]
        return evidence

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
                "Doctor in-network matching uses live carrier directories when configured, then falls back to stored carrier and network aliases.",
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

    def _doctor_entries(self, doctor: DoctorRecord) -> list[str]:
        unique_entries: list[str] = []
        seen: set[str] = set()
        for entry in doctor.accepted_insurance:
            normalized = normalize_text(entry)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique_entries.append(entry)
        return unique_entries

    def _exact_aliases(self, plan_context: PlanContext) -> list[tuple[str, str]]:
        aliases = [
            (plan_context.plan_id, "selected plan id"),
            (plan_context.plan_name, "plan marketing name"),
            (f"{plan_context.provider} {plan_context.plan_type}", "carrier and plan type"),
            (plan_context.provider, "carrier"),
        ]
        if plan_context.network_name:
            aliases.extend(
                [
                    (plan_context.network_name, "network name"),
                    (
                        f"{plan_context.provider} {plan_context.network_name}",
                        "carrier and network name",
                    ),
                ]
            )
        if plan_context.doctor_search_plan_id:
            aliases.append((plan_context.doctor_search_plan_id, "legacy plan id"))
        return aliases

    def _match_alias(self, alias: str, doctor_entries: list[str]) -> str | None:
        alias_tokens = set(tokenize(alias))
        for entry in doctor_entries:
            normalized_entry = normalize_text(entry)
            entry_tokens = set(tokenize(entry))
            if alias == normalized_entry:
                return entry
            if alias in normalized_entry or normalized_entry in alias:
                return entry
            if alias_tokens and alias_tokens.issubset(entry_tokens):
                return entry
        return None

    def _provider_level_match(self, provider: str, doctor_entries: list[str]) -> str | None:
        provider_tokens = set(tokenize(provider))
        if not provider_tokens:
            return None
        for entry in doctor_entries:
            entry_tokens = set(tokenize(entry))
            if provider_tokens.issubset(entry_tokens):
                return entry
        return None
