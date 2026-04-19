from __future__ import annotations

from fastapi import HTTPException, status

from app.repositories.doctor_repo import DoctorRepository
from app.repositories.insurance_repo import InsuranceRepository
from app.schemas.doctor import DoctorProfile, DoctorSearchRequest, DoctorSearchResponse
from app.schemas.insurance import InsuranceSummary
from app.schemas.symptom import SymptomTriageRequest
from app.services.insurance_service import InsuranceService
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
        ranking_service: RankingService,
    ) -> None:
        self.doctor_repo = doctor_repo
        self.insurance_repo = insurance_repo
        self.triage_service = triage_service
        self.insurance_service = insurance_service
        self.ranking_service = ranking_service

    def search(self, request: DoctorSearchRequest) -> DoctorSearchResponse:
        triage = self.triage_service.triage(
            SymptomTriageRequest(
                symptom_text=request.symptom_text,
                duration_days=request.duration_days,
                location=request.location,
            )
        )
        insurance_summary = (
            self.insurance_service.summarize_plan_id(
                request.insurance_plan_id_override,
                raw_query=request.insurance_query,
                match_confidence=0.95,
            )
            if request.insurance_plan_id_override
            else self.insurance_service.summarize_query(request.insurance_query)
        )
        plan = self.insurance_service.get_plan(
            insurance_summary.plan_id if insurance_summary and insurance_summary.matched else None
        )
        location = coalesce_location(request.location)

        candidate_profiles: list[DoctorProfile] = []
        for doctor in self.doctor_repo.list_doctors():
            clinic = self.doctor_repo.get_clinic(doctor.clinic_id)
            if clinic is None:
                continue
            profile = self.ranking_service.build_profile(
                doctor=doctor,
                clinic=clinic,
                triage=triage,
                location=location,
                plan=plan,
                preferred_language=request.preferred_language,
            )
            candidate_profiles.append(profile)

        in_network_first = sorted(
            candidate_profiles,
            key=lambda profile: (
                1 if insurance_summary and insurance_summary.plan_id in profile.accepted_insurance else 0,
                profile.ranking_breakdown.total_score if profile.ranking_breakdown else 0,
            ),
            reverse=True,
        )

        explanation = self._build_explanation(triage, insurance_summary, request.preferred_language)
        return DoctorSearchResponse(
            triage=triage,
            insurance_summary=insurance_summary,
            doctors=in_network_first[: request.top_k],
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
            preferred_language=None,
        )

    def _build_explanation(
        self,
        triage: object,
        insurance_summary: InsuranceSummary | None,
        preferred_language: str | None,
    ) -> list[str]:
        notes = [
            f"Triage suggests starting with {getattr(triage, 'care_type')} care.",
            "Ranking weights specialty match, insurance fit, distance, availability, language, and trust.",
        ]
        if insurance_summary and insurance_summary.matched:
            notes.append(
                f"Matched insurance plan: {insurance_summary.provider} {insurance_summary.plan_name}."
            )
        if preferred_language:
            notes.append(f"Language preference boosted doctors who speak {preferred_language}.")
        return notes
