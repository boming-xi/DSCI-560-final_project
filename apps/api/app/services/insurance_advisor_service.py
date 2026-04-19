from __future__ import annotations

import json
import re
from functools import cached_property

from app.ai.llm_client import LLMClient
from app.ai.prompt_templates import INSURANCE_ADVISOR_SYSTEM_PROMPT
from app.models.insurance import InsurancePlanRecord
from app.repositories.insurance_repo import InsuranceRepository
from app.schemas.insurance import InsuranceSummary
from app.schemas.insurance_advisor import (
    CareUsage,
    InsuranceAdvisorMessageRequest,
    InsuranceAdvisorMessageResponse,
    InsuranceAdvisorPlanRecord,
    InsuranceAdvisorProfile,
    InsuranceAdvisorRecommendation,
    InsuranceAdvisorSpeakerMessage,
    MonthlyBudget,
)
from app.services.insurance_service import InsuranceService
from app.utils.parsers import normalize_text


class InsuranceAdvisorService:
    def __init__(
        self,
        insurance_repo: InsuranceRepository,
        insurance_service: InsuranceService,
        llm_client: LLMClient,
    ) -> None:
        self.insurance_repo = insurance_repo
        self.insurance_service = insurance_service
        self.llm_client = llm_client
        self.legacy_catalog_path = insurance_repo.settings.mock_data_dir / "insurance_advisor_catalog.json"
        self.ca_marketplace_catalog_path = (
            insurance_repo.settings.mock_data_dir / "ca_marketplace_plans.json"
        )

    @cached_property
    def legacy_advisor_catalog(self) -> dict[str, InsuranceAdvisorPlanRecord]:
        payload = json.loads(self.legacy_catalog_path.read_text())
        catalog = [InsuranceAdvisorPlanRecord.model_validate(item) for item in payload]
        return {item.plan_id: item for item in catalog}

    @cached_property
    def ca_marketplace_catalog(self) -> list[InsuranceAdvisorPlanRecord]:
        if not self.ca_marketplace_catalog_path.exists():
            return []
        payload = json.loads(self.ca_marketplace_catalog_path.read_text())
        return [InsuranceAdvisorPlanRecord.model_validate(item) for item in payload]

    def reply(self, request: InsuranceAdvisorMessageRequest) -> InsuranceAdvisorMessageResponse:
        base_profile = request.profile or InsuranceAdvisorProfile()
        extracted_profile = self._extract_profile_updates(request.message)
        profile = self._merge_profiles(base_profile, extracted_profile)

        profile_summary = self._profile_summary(profile)
        missing_fields = self._missing_fields(profile)
        recommendations = self._recommend_plans(profile)
        readiness_label = self._readiness_label(profile, recommendations)

        navigator_message = self._navigator_message(
            message=request.message,
            profile=profile,
            missing_fields=missing_fields,
            recommendations=recommendations,
        )
        eligibility_message = self._eligibility_message(profile, missing_fields)
        plan_matcher_message = self._plan_matcher_message(recommendations, readiness_label)

        return InsuranceAdvisorMessageResponse(
            profile=profile,
            profile_summary=profile_summary,
            missing_fields=missing_fields,
            readiness_label=readiness_label,
            group_messages=[
                InsuranceAdvisorSpeakerMessage(
                    speaker="Navigator",
                    content=navigator_message,
                ),
                InsuranceAdvisorSpeakerMessage(
                    speaker="Eligibility Checker",
                    content=eligibility_message,
                ),
                InsuranceAdvisorSpeakerMessage(
                    speaker="Plan Matcher",
                    content=plan_matcher_message,
                ),
            ],
            recommendations=recommendations,
            suggested_prompts=self._suggested_prompts(profile, missing_fields, readiness_label),
            disclaimer=(
                "This is a planning tool, not official enrollment, tax, or legal advice. "
                "Final eligibility, subsidies, provider networks, and enrollment still need confirmation on the official plan site."
            ),
        )

    def _merge_profiles(
        self,
        base: InsuranceAdvisorProfile,
        updates: InsuranceAdvisorProfile,
    ) -> InsuranceAdvisorProfile:
        merged = base.model_dump()
        for key, value in updates.model_dump().items():
            if value is not None:
                merged[key] = value
        return InsuranceAdvisorProfile.model_validate(merged)

    def _extract_profile_updates(self, message: str) -> InsuranceAdvisorProfile:
        text = normalize_text(message)
        updates: dict[str, object] = {}

        age = self._extract_age(message)
        if age is not None:
            updates["age"] = age

        zip_match = re.search(r"\b(\d{5})(?:-\d{4})?\b", message)
        if zip_match:
            updates["zip_code"] = zip_match.group(1)

        if "california" in text or re.search(r"\bca\b", text) or "los angeles" in text:
            updates["state"] = "CA"

        household_size = self._extract_household_size(text)
        if household_size is not None:
            updates["household_size"] = household_size

        income_band = self._extract_income_band(message)
        if income_band is not None:
            updates["income_band"] = income_band

        coverage_channel = self._extract_coverage_channel(text)
        if coverage_channel is not None:
            updates["coverage_channel"] = coverage_channel

        monthly_budget = self._extract_monthly_budget(message, text)
        if monthly_budget is not None:
            updates["monthly_budget"] = monthly_budget

        care_usage = self._extract_care_usage(text)
        if care_usage is not None:
            updates["care_usage"] = care_usage

        referrals_ok = self._extract_boolean(
            text,
            positive_terms=[
                "okay with referral",
                "ok with referral",
                "fine with referral",
                "hmo is okay",
                "okay with hmo",
                "referrals are fine",
            ],
            negative_terms=[
                "no referrals",
                "dont want referral",
                "don't want referral",
                "want ppo",
                "need ppo",
                "need flexibility",
                "no hmo",
                "avoid hmo",
            ],
        )
        if referrals_ok is not None:
            updates["referrals_ok"] = referrals_ok

        keep_existing_doctors = self._extract_boolean(
            text,
            positive_terms=[
                "keep my doctor",
                "keep my doctors",
                "already have a doctor",
                "current doctor",
                "specific doctor",
                "want usc doctor",
                "keck",
                "cedars",
                "ucla",
            ],
            negative_terms=[
                "no preferred doctor",
                "no current doctor",
                "dont care which doctor",
                "don't care which doctor",
            ],
        )
        if keep_existing_doctors is not None:
            updates["keep_existing_doctors"] = keep_existing_doctors

        has_prescriptions = self._extract_boolean(
            text,
            positive_terms=[
                "prescription",
                "prescriptions",
                "medication",
                "medications",
                "refill",
                "refills",
                "take meds",
                "take medicine",
            ],
            negative_terms=["no prescriptions", "no medication", "no medications"],
        )
        if has_prescriptions is not None:
            updates["has_prescriptions"] = has_prescriptions

        preferred_language = self._extract_language(text)
        if preferred_language is not None:
            updates["preferred_language"] = preferred_language

        return InsuranceAdvisorProfile.model_validate(updates)

    def _extract_age(self, message: str) -> int | None:
        patterns = [
            r"\bi am (\d{2})\b",
            r"\bi'm (\d{2})\b",
            r"\bage (\d{2})\b",
            r"\b(\d{2}) years old\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                age = int(match.group(1))
                if 18 <= age <= 64:
                    return age
        return None

    def _extract_household_size(self, text: str) -> int | None:
        if "just me" in text or "only me" in text or "single" in text:
            return 1
        if "my spouse and i" in text or "two of us" in text or "2 of us" in text:
            return 2

        patterns = [
            r"family of (\d)",
            r"household of (\d)",
            r"(\d) people",
            r"(\d) person household",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None

    def _extract_income_band(self, message: str) -> str | None:
        match = re.search(r"\$?\s*(\d{2,3})(?:,?(\d{3}))?\s*(k|000)?", message.lower())
        if not match:
            return None

        leading = int(match.group(1))
        trailing = match.group(2)
        suffix = match.group(3)
        if trailing:
            income_value = int(f"{leading}{trailing}")
        elif suffix == "k":
            income_value = leading * 1000
        elif suffix == "000":
            income_value = leading * 1000
        else:
            return None

        if income_value < 30000:
            return "under_30000"
        if income_value < 60000:
            return "30000_to_60000"
        if income_value < 100000:
            return "60000_to_100000"
        return "over_100000"

    def _extract_coverage_channel(self, text: str) -> str | None:
        if any(term in text for term in ["student", "usc", "school plan", "university plan"]):
            return "student"
        if any(term in text for term in ["covered california", "marketplace", "aca", "exchange plan"]):
            return "marketplace"
        if any(term in text for term in ["employer", "through work", "job insurance", "company plan"]):
            return "employer"
        if any(term in text for term in ["uninsured", "no insurance", "need insurance"]):
            return "marketplace"
        return None

    def _extract_monthly_budget(self, message: str, text: str) -> MonthlyBudget | None:
        if any(
            term in text
            for term in [
                "lowest premium",
                "cheap",
                "tight budget",
                "budget is tight",
                "low premium",
            ]
        ):
            return "low"
        if any(
            term in text
            for term in [
                "premium is not a big issue",
                "okay paying more",
                "fine with higher premium",
            ]
        ):
            return "high"

        dollar_match = re.search(r"\$?\s*(\d{2,4})\s*(?:/|per)?\s*month", message.lower())
        if not dollar_match:
            return None
        value = int(dollar_match.group(1))
        if value <= 250:
            return "low"
        if value <= 450:
            return "medium"
        return "high"

    def _extract_care_usage(self, text: str) -> CareUsage | None:
        if any(term in text for term in ["rarely go", "rarely see", "healthy", "just in case", "mostly preventive"]):
            return "low"
        if any(
            term in text
            for term in [
                "chronic",
                "monthly",
                "regular visits",
                "ongoing care",
                "specialist often",
                "therapy",
                "follow up often",
                "pregnan",
                "prescription",
                "medication",
            ]
        ):
            return "high"
        if any(term in text for term in ["a few visits", "sometimes", "moderate use", "occasional specialist"]):
            return "moderate"
        return None

    def _extract_boolean(
        self,
        text: str,
        *,
        positive_terms: list[str],
        negative_terms: list[str],
    ) -> bool | None:
        if any(term in text for term in negative_terms):
            return False
        if any(term in text for term in positive_terms):
            return True
        return None

    def _extract_language(self, text: str) -> str | None:
        if "mandarin" in text or "chinese" in text:
            return "Mandarin"
        if "spanish" in text:
            return "Spanish"
        if "korean" in text:
            return "Korean"
        return None

    def _profile_summary(self, profile: InsuranceAdvisorProfile) -> list[str]:
        summary: list[str] = []
        if profile.coverage_channel:
            summary.append(f"Coverage path: {profile.coverage_channel}")
        if profile.age:
            summary.append(f"Age used for premium estimates: {profile.age}")
        if profile.state or profile.zip_code:
            location_bits = [bit for bit in [profile.state, profile.zip_code] if bit]
            summary.append(f"Location: {' / '.join(location_bits)}")
        if profile.household_size:
            summary.append(f"Household size: {profile.household_size}")
        if profile.income_band:
            summary.append(f"Income band noted for subsidy context: {profile.income_band}")
        if profile.monthly_budget:
            summary.append(f"Monthly budget preference: {profile.monthly_budget}")
        if profile.care_usage:
            summary.append(f"Expected care usage: {profile.care_usage}")
        if profile.referrals_ok is not None:
            summary.append(
                "Referral tolerance: okay with referrals"
                if profile.referrals_ok
                else "Referral tolerance: prefers direct specialist access"
            )
        if profile.keep_existing_doctors is not None:
            summary.append(
                "Provider preference: wants to keep current doctors"
                if profile.keep_existing_doctors
                else "Provider preference: no specific doctor lock-in"
            )
        if profile.has_prescriptions is not None:
            summary.append(
                "Prescription needs: ongoing medications matter"
                if profile.has_prescriptions
                else "Prescription needs: no regular medications flagged"
            )
        return summary

    def _missing_fields(self, profile: InsuranceAdvisorProfile) -> list[str]:
        required_fields = [
            ("coverage_channel", "how you expect to access coverage (student, marketplace, or employer)"),
            ("zip_code", "your ZIP code"),
            ("monthly_budget", "your monthly budget comfort level"),
            ("care_usage", "whether you expect low, moderate, or high care usage"),
            ("referrals_ok", "whether you are okay with referrals / HMO-style coordination"),
        ]

        missing = [
            label
            for field_name, label in required_fields
            if getattr(profile, field_name) is None
        ]
        if profile.household_size is None:
            missing.append("how many people need coverage")
        if profile.has_prescriptions is None:
            missing.append("whether you have regular prescriptions")
        if profile.coverage_channel == "marketplace" and profile.age is None:
            missing.append("your age, so I can ground the premium estimate more accurately")
        return missing[:5]

    def _readiness_label(
        self,
        profile: InsuranceAdvisorProfile,
        recommendations: list[InsuranceAdvisorRecommendation],
    ) -> str:
        if recommendations and len(self._missing_fields(profile)) <= 2:
            return "recommended"
        if recommendations:
            return "narrowing"
        return "intake"

    def _recommend_plans(self, profile: InsuranceAdvisorProfile) -> list[InsuranceAdvisorRecommendation]:
        populated_fields = sum(
            1
            for value in profile.model_dump().values()
            if value is not None and value != ""
        )
        if populated_fields < 3:
            return []

        recommendations: list[InsuranceAdvisorRecommendation] = []
        for plan_metadata in self._candidate_catalog(profile):
            score_payload = self._score_plan(plan_metadata, profile)
            if score_payload is None:
                continue
            score, reasons, premium_amount = score_payload
            confidence_label = "early"
            if score >= 5.4:
                confidence_label = "strong"
            elif score >= 4.0:
                confidence_label = "good"

            provider = plan_metadata.provider or "Unknown provider"
            plan_name = plan_metadata.plan_name or plan_metadata.plan_id
            plan_type = plan_metadata.plan_type or "Unknown"
            recommendations.append(
                InsuranceAdvisorRecommendation(
                    plan_id=plan_metadata.plan_id,
                    doctor_search_plan_id=plan_metadata.doctor_search_plan_id or plan_metadata.plan_id,
                    provider=provider,
                    plan_name=plan_name,
                    plan_type=plan_type,
                    network_name=plan_metadata.network_name,
                    metal_level=plan_metadata.metal_level,
                    insurance_query=f"{provider} {plan_name}".strip(),
                    fit_score=round(score, 2),
                    confidence_label=confidence_label,
                    monthly_premium_band=plan_metadata.monthly_premium_band,
                    monthly_premium_amount=premium_amount,
                    deductible_band=plan_metadata.deductible_band,
                    deductible_amount=plan_metadata.deductible_amount,
                    out_of_pocket_max_amount=plan_metadata.out_of_pocket_max_amount,
                    network_flexibility=plan_metadata.network_flexibility,
                    quality_rating=plan_metadata.quality_rating,
                    advisor_blurb=plan_metadata.advisor_blurb,
                    reasons=reasons[:4],
                    tradeoffs=plan_metadata.tradeoffs,
                    ideal_for=plan_metadata.ideal_for,
                    purchase_url=plan_metadata.purchase_url,
                    purchase_cta_label=plan_metadata.purchase_cta_label,
                    source_url=plan_metadata.source_url,
                    network_url=plan_metadata.network_url,
                    insurance_summary=self._insurance_summary_for_record(plan_metadata, premium_amount),
                )
            )

        recommendations.sort(key=lambda item: item.fit_score, reverse=True)
        return recommendations[:3]

    def _candidate_catalog(self, profile: InsuranceAdvisorProfile) -> list[InsuranceAdvisorPlanRecord]:
        if profile.coverage_channel == "student":
            return [
                record
                for record in self.legacy_advisor_catalog.values()
                if "student" in record.coverage_channels
            ]
        if profile.coverage_channel == "marketplace":
            if self.ca_marketplace_catalog and (profile.state in {None, "CA"}):
                return self.ca_marketplace_catalog
            return [
                record
                for record in self.legacy_advisor_catalog.values()
                if "marketplace" in record.coverage_channels
            ]
        if profile.coverage_channel == "employer":
            return [
                record
                for record in self.legacy_advisor_catalog.values()
                if "employer" in record.coverage_channels
            ]
        return list(self.legacy_advisor_catalog.values()) + self.ca_marketplace_catalog

    def _score_plan(
        self,
        plan_metadata: InsuranceAdvisorPlanRecord,
        profile: InsuranceAdvisorProfile,
    ) -> tuple[float, list[str], float | None] | None:
        if profile.state and plan_metadata.service_states and profile.state not in plan_metadata.service_states:
            return None

        if profile.zip_code and plan_metadata.supported_zip_codes:
            if profile.zip_code not in plan_metadata.supported_zip_codes:
                return None

        score = 1.0
        premium_amount = self._estimated_monthly_premium(plan_metadata, profile.age)
        reasons = [plan_metadata.advisor_blurb]

        if profile.coverage_channel:
            if profile.coverage_channel in plan_metadata.coverage_channels:
                score += 2.1
                reasons.append(f"It matches the {profile.coverage_channel} coverage path you described.")
            elif profile.coverage_channel != "unsure":
                score -= 1.4

        if profile.zip_code:
            if plan_metadata.supported_zip_codes and profile.zip_code in plan_metadata.supported_zip_codes:
                score += 1.6
                reasons.append(f"It is filed to serve ZIP {profile.zip_code}.")
            elif plan_metadata.service_states:
                score += 0.15

        if profile.monthly_budget:
            budget_score, budget_reason = self._budget_score(
                profile.monthly_budget,
                premium_amount,
                plan_metadata.monthly_premium_band,
            )
            score += budget_score
            if budget_reason:
                reasons.append(budget_reason)

        if profile.care_usage:
            usage_score, usage_reason = self._care_usage_score(
                profile.care_usage,
                plan_metadata,
            )
            score += usage_score
            if usage_reason:
                reasons.append(usage_reason)

        if profile.keep_existing_doctors:
            if plan_metadata.network_flexibility == "high":
                score += 1.0
                reasons.append("It leaves more room to preserve doctor choice or specialist access.")
            else:
                score -= 0.9

        if profile.referrals_ok is not None:
            if not profile.referrals_ok and not plan_metadata.referral_required_for_specialists:
                score += 1.2
                reasons.append("It avoids referral friction for specialist visits.")
            elif not profile.referrals_ok and plan_metadata.referral_required_for_specialists:
                score -= 1.3
            elif profile.referrals_ok and plan_metadata.referral_required_for_specialists:
                score += 0.5
                reasons.append("You said HMO-style coordination is acceptable, so referral-based plans still fit.")

        if profile.has_prescriptions:
            if plan_metadata.prescription_support == "strong":
                score += 0.8
                reasons.append("It looks safer for a year where prescriptions may matter.")
            else:
                score += 0.2

        if plan_metadata.quality_rating:
            if plan_metadata.quality_rating >= 5:
                score += 0.5
                reasons.append("Covered California quality ratings are strong for this carrier and plan type.")
            else:
                score += 0.2

        if plan_metadata.plan_type == "PPO":
            score += 0.15
        elif plan_metadata.plan_type == "EPO":
            score += 0.05

        if profile.household_size and profile.household_size > 1:
            score += 0.1

        return score, reasons, premium_amount

    def _budget_score(
        self,
        budget: MonthlyBudget,
        premium_amount: float | None,
        stored_band: str,
    ) -> tuple[float, str | None]:
        premium_band = self._premium_band(premium_amount) if premium_amount is not None else stored_band
        if budget == premium_band:
            if premium_amount is not None:
                return 1.6, f"Its estimated monthly premium lands around ${premium_amount:.0f}, which lines up with your budget."
            return 1.3, "Its premium level lines up with your monthly budget preference."

        if budget == "low":
            if premium_band == "medium":
                return 0.4, "It is not the cheapest option, but it may still be manageable if you want stronger coverage."
            return -1.4, "This plan runs expensive relative to the budget you described."
        if budget == "medium":
            if premium_band == "low":
                return 0.6, "It keeps premiums lower than the budget you expected."
            return -0.3, "Premiums may be a stretch compared with your target range."
        if premium_band == "high":
            return 1.0, "You said you can tolerate a higher premium to reduce friction later."
        return 0.2, None

    def _care_usage_score(
        self,
        care_usage: CareUsage,
        plan_metadata: InsuranceAdvisorPlanRecord,
    ) -> tuple[float, str | None]:
        if care_usage in plan_metadata.care_usage_fit:
            return 1.4, "Its deductible and cost-sharing profile better fit the amount of care you expect to use."
        if care_usage == "high":
            if plan_metadata.deductible_band == "high":
                return -1.0, "High deductibles make this less comfortable for a heavier-care year."
            if plan_metadata.out_of_pocket_max_amount and plan_metadata.out_of_pocket_max_amount <= 6500:
                return 1.0, "The lower out-of-pocket ceiling is safer if you expect more visits."
        if care_usage == "low":
            if plan_metadata.monthly_premium_band == "low":
                return 0.9, "It keeps monthly costs lean for a lighter-care year."
            if plan_metadata.monthly_premium_band == "high":
                return -0.6, "You may be overpaying if you expect only light use."
        return 0.0, None

    def _estimated_monthly_premium(
        self,
        plan_metadata: InsuranceAdvisorPlanRecord,
        age: int | None,
    ) -> float | None:
        if age is not None and plan_metadata.monthly_premium_samples:
            nearest_age = min(
                (int(sample_age) for sample_age in plan_metadata.monthly_premium_samples),
                key=lambda sample_age: abs(sample_age - age),
            )
            return plan_metadata.monthly_premium_samples.get(str(nearest_age))
        return plan_metadata.monthly_premium_amount

    def _premium_band(self, premium_amount: float | None) -> str:
        if premium_amount is None:
            return "medium"
        if premium_amount <= 360:
            return "low"
        if premium_amount <= 620:
            return "medium"
        return "high"

    def _insurance_summary_for_record(
        self,
        plan_metadata: InsuranceAdvisorPlanRecord,
        premium_amount: float | None,
    ) -> InsuranceSummary:
        provider = plan_metadata.provider or "Unknown provider"
        plan_name = plan_metadata.plan_name or plan_metadata.plan_id
        plan_type = plan_metadata.plan_type or "Unknown"
        legacy_plan = self._legacy_plan_for_record(plan_metadata)

        notes = [
            "Shortlisted by the insurance advisor based on your coverage path, ZIP code, budget, and care usage.",
            "Confirm subsidy amounts, exact doctor network participation, and final enrollment details on the official plan page.",
        ]
        if premium_amount is not None:
            notes.insert(1, f"Estimated monthly premium is around ${premium_amount:.0f} before subsidies.")

        return InsuranceSummary(
            matched=True,
            plan_id=plan_metadata.plan_id,
            provider=provider,
            plan_name=plan_name,
            plan_type=plan_type,
            referral_required_for_specialists=bool(
                plan_metadata.referral_required_for_specialists
            ),
            primary_care_copay=legacy_plan.primary_care_copay if legacy_plan else None,
            specialist_copay=legacy_plan.specialist_copay if legacy_plan else None,
            urgent_care_copay=legacy_plan.urgent_care_copay if legacy_plan else None,
            notes=notes,
            match_confidence=0.92,
            normalized_query=normalize_text(f"{provider} {plan_name}"),
        )

    def _legacy_plan_for_record(
        self,
        plan_metadata: InsuranceAdvisorPlanRecord,
    ) -> InsurancePlanRecord | None:
        override_id = plan_metadata.doctor_search_plan_id or plan_metadata.plan_id
        return self.insurance_service.get_plan(override_id)

    def _navigator_message(
        self,
        *,
        message: str,
        profile: InsuranceAdvisorProfile,
        missing_fields: list[str],
        recommendations: list[InsuranceAdvisorRecommendation],
    ) -> str:
        recommendation_names = ", ".join(
            f"{item.provider} {item.plan_name}" for item in recommendations[:2]
        ) or "none yet"
        prompt = (
            "Insurance advisor profile:\n"
            f"{json.dumps(profile.model_dump(), indent=2)}\n\n"
            f"Missing fields: {missing_fields or ['none']}\n"
            f"Current user message: {message}\n"
            f"Current shortlist: {recommendation_names}\n\n"
            "Write a short, warm next message from the Navigator role. "
            "If information is still missing, ask at most two concrete follow-up questions. "
            "If there is already a shortlist, briefly acknowledge that and ask one decision-making question. "
            "Do not mention being an AI model."
        )
        try:
            return self.llm_client.complete(
                system_prompt=INSURANCE_ADVISOR_SYSTEM_PROMPT,
                user_prompt=prompt,
            )
        except Exception:
            if missing_fields:
                return (
                    "I can keep narrowing this down. Next, tell me "
                    f"{missing_fields[0]}"
                    + (f", and {missing_fields[1]}." if len(missing_fields) > 1 else ".")
                )
            if recommendations:
                return (
                    "We have a usable shortlist now. Tell me whether lower monthly cost or easier specialist access matters more, "
                    "and I can help you choose between the top plans."
                )
            return "Tell me a little more about your budget and expected care use, and I’ll narrow the plan list."

    def _eligibility_message(
        self,
        profile: InsuranceAdvisorProfile,
        missing_fields: list[str],
    ) -> str:
        if profile.coverage_channel == "student":
            base = "Right now I would compare student-plan options first, then only fall back to marketplace choices if flexibility or cost pushes us there."
        elif profile.coverage_channel == "marketplace":
            base = "This looks most like a marketplace comparison, and for California I can now ground the shortlist in Covered California plan data."
        elif profile.coverage_channel == "employer":
            base = "This sounds more like an employer-plan comparison, but I can still help translate tradeoffs and think about network fit."
        else:
            base = "I still need a little more intake detail before I can confidently choose the right coverage path."

        if missing_fields:
            return f"{base} The biggest gaps are {', '.join(missing_fields[:3])}."
        return f"{base} I have enough detail to start giving a more concrete shortlist."

    def _plan_matcher_message(
        self,
        recommendations: list[InsuranceAdvisorRecommendation],
        readiness_label: str,
    ) -> str:
        if not recommendations:
            return (
                "I am not ranking plans yet because the intake is still thin. "
                "Once I have your coverage path, ZIP code, budget, and likely care usage, I can produce a more defensible top 3."
            )

        top = recommendations[0]
        second = recommendations[1] if len(recommendations) > 1 else None
        premium_copy = (
            f" Estimated premium is about ${top.monthly_premium_amount:.0f} before subsidies."
            if top.monthly_premium_amount is not None
            else ""
        )
        if readiness_label == "recommended":
            comparison_tail = (
                f" If you want a backup with a slightly different tradeoff, also look at {second.provider} {second.plan_name}."
                if second
                else ""
            )
            return (
                f"My current best fit is {top.provider} {top.plan_name} because it lines up with the preferences you shared on cost, access, and care usage."
                f"{premium_copy}{comparison_tail}"
            )

        return (
            f"I have a preliminary shortlist led by {top.provider} {top.plan_name}. "
            "I can tighten the ranking once you confirm the last few preferences."
        )

    def _suggested_prompts(
        self,
        profile: InsuranceAdvisorProfile,
        missing_fields: list[str],
        readiness_label: str,
    ) -> list[str]:
        if readiness_label == "recommended":
            prompts = [
                "I care more about keeping specialist access easy than saving on premium.",
                "I want the cheapest option that still feels safe for a few visits a year.",
                "Which of these is safest if I may need regular prescriptions?",
            ]
            if profile.coverage_channel == "student":
                prompts.insert(0, "Compare the top student plan against the best marketplace fallback.")
            if profile.coverage_channel == "marketplace":
                prompts.insert(0, "Show me the best PPO-style option even if the premium is higher.")
            return prompts[:3]

        prompts = [
            "I am a USC student in Los Angeles 90007 and I want something simple.",
            "I need a Covered California plan in 90007, I am 24, and my budget is around $320 per month.",
            "I expect regular visits and I also have ongoing prescriptions.",
        ]
        if not missing_fields:
            return prompts[:2]
        return prompts
