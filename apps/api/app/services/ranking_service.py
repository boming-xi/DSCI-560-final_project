from __future__ import annotations

from app.models.doctor import ClinicRecord, DoctorRecord
from app.models.insurance import InsurancePlanRecord
from app.rules.insurance_rules import compute_estimated_cost, insurance_fit_score
from app.rules.ranking_rules import combine_scores
from app.rules.referral_rules import requires_referral
from app.schemas.doctor import ClinicInfo, DoctorProfile, RankingBreakdown
from app.schemas.symptom import TriageRecommendation
from app.utils.geo import haversine_km


class RankingService:
    def build_profile(
        self,
        doctor: DoctorRecord,
        clinic: ClinicRecord,
        triage: TriageRecommendation,
        location: tuple[float, float],
        plan: InsurancePlanRecord | None,
        preferred_language: str | None,
    ) -> DoctorProfile:
        specialty_score = self._specialty_score(doctor, triage)
        insurance_score = insurance_fit_score(plan, doctor)
        distance_km = haversine_km(location[0], location[1], clinic.latitude, clinic.longitude)
        distance_score = max(0.0, 1 - (distance_km / 20))
        availability_score = self._availability_score(doctor.availability_days)
        language_score = self._language_score(doctor, preferred_language)
        trust_score = self._trust_score(doctor.rating, doctor.review_count)

        raw_scores = {
            "specialty": specialty_score,
            "insurance": insurance_score,
            "distance": distance_score,
            "availability": availability_score,
            "language": language_score,
            "trust": trust_score,
        }

        total_score = combine_scores(raw_scores)
        ranking_breakdown = RankingBreakdown(
            specialty_score=round(specialty_score, 2),
            insurance_score=round(insurance_score, 2),
            distance_score=round(distance_score, 2),
            availability_score=round(availability_score, 2),
            language_score=round(language_score, 2),
            trust_score=round(trust_score, 2),
            total_score=total_score,
            summary=(
                f"Strongest signals: {doctor.specialty}, "
                f"{'in-network fit' if insurance_score >= 0.9 else 'coverage uncertain'}, "
                f"and {distance_km} km travel distance."
            ),
        )

        return DoctorProfile(
            id=doctor.id,
            name=doctor.name,
            specialty=doctor.specialty,
            years_experience=doctor.years_experience,
            languages=doctor.languages,
            rating=doctor.rating,
            review_count=doctor.review_count,
            accepted_insurance=doctor.accepted_insurance,
            availability_days=doctor.availability_days,
            telehealth=doctor.telehealth,
            gender=doctor.gender,
            profile_blurb=doctor.profile_blurb,
            clinic=ClinicInfo(
                id=clinic.id,
                name=clinic.name,
                address=clinic.address,
                city=clinic.city,
                state=clinic.state,
                zip=clinic.zip,
                phone=clinic.phone,
                urgent_care=clinic.urgent_care,
                open_weekends=clinic.open_weekends,
            ),
            distance_km=distance_km,
            estimated_cost=compute_estimated_cost(plan, doctor),
            referral_required=requires_referral(plan, doctor.specialty),
            ranking_breakdown=ranking_breakdown,
        )

    def _specialty_score(self, doctor: DoctorRecord, triage: TriageRecommendation) -> float:
        doctor_specialty = doctor.specialty.lower()
        matched_specialties = [specialty.lower() for specialty in triage.matched_specialties]
        if doctor_specialty in matched_specialties:
            return 1.0
        if triage.care_type in doctor.care_types:
            return 0.8
        if triage.care_type == "urgent_care" and "urgent_care" in doctor.care_types:
            return 1.0
        if triage.care_type == "general_practitioner" and any(
            care in doctor.care_types for care in ["general_practitioner", "primary_care"]
        ):
            return 0.9
        return 0.35

    def _availability_score(self, days: int) -> float:
        if days == 0:
            return 1.0
        if days <= 2:
            return 0.85
        if days <= 5:
            return 0.65
        return 0.45

    def _language_score(self, doctor: DoctorRecord, preferred_language: str | None) -> float:
        if not preferred_language:
            return 0.6
        normalized = preferred_language.lower()
        return 1.0 if any(language.lower() == normalized for language in doctor.languages) else 0.3

    def _trust_score(self, rating: float, review_count: int) -> float:
        rating_component = rating / 5
        review_component = min(review_count, 250) / 250
        return (rating_component * 0.7) + (review_component * 0.3)

