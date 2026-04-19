from __future__ import annotations

from fastapi import HTTPException, status

from app.repositories.doctor_repo import DoctorRepository
from app.repositories.insurance_repo import InsuranceRepository
from app.schemas.doctor import DoctorProfile, DoctorSearchRequest, DoctorSearchResponse
from app.schemas.insurance import InsuranceSummary
from app.schemas.symptom import SymptomTriageRequest
from app.services.insurance_service import InsuranceService
from app.services.insurance_network_service import InsuranceNetworkService
from app.services.ranking_service import RankingService
from app.services.triage_service import TriageService
from app.utils.validators import coalesce_location


class DoctorSearchService:
    def __init__(
        self,
        doctor_repo: DoctorRepository,
        insurance_repo: InsuranceRepository,
        triage_service: TriageService,
        insurance_service: InsuranceService,
        insurance_network_service: InsuranceNetworkService,
        ranking_service: RankingService,
    ) -> None:
        self.doctor_repo = doctor_repo
        self.insurance_repo = insurance_repo
        self.triage_service = triage_service
        self.insurance_service = insurance_service
        self.insurance_network_service = insurance_network_service
        self.ranking_service = ranking_service

    def search(self, request: DoctorSearchRequest) -> DoctorSearchResponse:
        triage = self.triage_service.triage(
            SymptomTriageRequest(
                symptom_text=request.symptom_text,
                duration_days=request.duration_days,
                location=request.location,
            )
        )
        plan_context, insurance_summary = self.insurance_network_service.resolve_plan_context(
            selected_plan_id=request.insurance_selected_plan_id,
            doctor_search_plan_id=request.insurance_plan_id_override,
            insurance_query=request.insurance_query,
        )
        legacy_plan_ids = {plan.id for plan in self.insurance_repo.list_plans()}
        plan = self.insurance_service.get_plan(
            request.insurance_plan_id_override
            or (
                insurance_summary.plan_id
                if insurance_summary
                and insurance_summary.matched
                and insurance_summary.plan_id in legacy_plan_ids
                else None
            )
        )
        location = coalesce_location(request.location)

        candidate_profiles: list[DoctorProfile] = []
        for doctor in self.doctor_repo.list_doctors():
            clinic = self.doctor_repo.get_clinic(doctor.clinic_id)
            if clinic is None:
                continue
            insurance_verification = self.insurance_network_service.build_verification(
                doctor,
                clinic,
                plan_context,
            )
            profile = self.ranking_service.build_profile(
                doctor=doctor,
                clinic=clinic,
                triage=triage,
                location=location,
                plan=plan,
                insurance_verification=insurance_verification,
                preferred_language=request.preferred_language,
            )
            candidate_profiles.append(profile)

        ranked_profiles = sorted(
            candidate_profiles,
            key=lambda profile: (
                1
                if profile.insurance_verification
                and profile.insurance_verification.status == "verified"
                else 0,
                profile.ranking_breakdown.total_score if profile.ranking_breakdown else 0,
            ),
            reverse=True,
        )

        explanation = self._build_explanation(
            triage,
            insurance_summary,
            request.preferred_language,
            ranked_profiles,
        )
        return DoctorSearchResponse(
            triage=triage,
            insurance_summary=insurance_summary,
            doctors=ranked_profiles[: request.top_k],
            explanation=explanation,
        )

    def get_doctor(self, doctor_id: str) -> DoctorProfile:
        doctor = self.doctor_repo.get_doctor(doctor_id)
        if doctor is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
        clinic = self.doctor_repo.get_clinic(doctor.clinic_id)
        if clinic is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found.")
        fallback_triage = self.triage_service.triage(
            SymptomTriageRequest(symptom_text="general health visit", duration_days=1)
        )
        return self.ranking_service.build_profile(
            doctor=doctor,
            clinic=clinic,
            triage=fallback_triage,
            location=(clinic.latitude, clinic.longitude),
            plan=None,
            insurance_verification=None,
            preferred_language=None,
        )

    def _build_explanation(
        self,
        triage: object,
        insurance_summary: InsuranceSummary | None,
        preferred_language: str | None,
        ranked_profiles: list[DoctorProfile],
    ) -> list[str]:
        notes = [
            f"Triage suggests starting with {getattr(triage, 'care_type')} care.",
            "Ranking weights specialty match, insurance fit, distance, availability, language, and trust.",
        ]
        if insurance_summary and insurance_summary.matched:
            notes.append(
                f"Matched insurance plan: {insurance_summary.provider} {insurance_summary.plan_name}."
            )
        if ranked_profiles and any(profile.insurance_verification for profile in ranked_profiles):
            verified_count = sum(
                1
                for profile in ranked_profiles
                if profile.insurance_verification
                and profile.insurance_verification.status == "verified"
            )
            likely_count = sum(
                1
                for profile in ranked_profiles
                if profile.insurance_verification
                and profile.insurance_verification.status == "likely"
            )
            notes.append(
                f"Insurance verification used stored carrier and network aliases: {verified_count} verified matches, {likely_count} carrier-level matches."
            )
        if preferred_language:
            notes.append(f"Language preference boosted doctors who speak {preferred_language}.")
        return notes
