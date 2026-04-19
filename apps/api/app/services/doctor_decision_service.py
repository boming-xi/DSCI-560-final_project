from __future__ import annotations

from dataclasses import dataclass

from app.schemas.doctor import DoctorProfile
from app.schemas.doctor_decision import (
    DoctorDecisionRequest,
    DoctorDecisionResponse,
    DoctorDecisionSharedBrief,
    DoctorDecisionSpeakerMessage,
)
from app.utils.parsers import normalize_text


@dataclass
class SharedDecisionContext:
    transcript: str
    user_goal: str
    symptom_anchor: str | None
    insurance_anchor: str | None
    language_anchor: str | None
    priorities: dict[str, str | bool | None]
    priority_labels: list[str]
    ranked: list[DoctorProfile]
    best: DoctorProfile
    alternate: DoctorProfile | None
    coverage_pick: DoctorProfile
    shortlist_names: list[str]
    case_summary: str
    coverage_watchout: str | None


class DoctorDecisionService:
    def reply(self, request: DoctorDecisionRequest) -> DoctorDecisionResponse:
        doctors = request.doctors[:5]
        if not doctors:
            return DoctorDecisionResponse(
                group_messages=[
                    DoctorDecisionSpeakerMessage(
                        speaker="Decision Guide",
                        content="I need a current doctor shortlist before I can help with the final choice. Run doctor search first, then I can compare the options.",
                    )
                ],
                shared_brief=None,
                suggested_prompts=[],
                recommended_doctor_id=None,
                recommended_reason=None,
            )

        transcript = self._collect_user_transcript(request)
        priorities = self._extract_priorities(transcript, request.preferred_language)
        ranked = sorted(
            doctors,
            key=lambda doctor: self._decision_score(
                doctor,
                priorities=priorities,
                preferred_language=request.preferred_language,
            ),
            reverse=True,
        )
        best = ranked[0]
        alternate = ranked[1] if len(ranked) > 1 else None
        coverage_pick = max(ranked, key=self._coverage_score)
        shared = self._build_shared_context(
            request=request,
            transcript=transcript,
            priorities=priorities,
            ranked=ranked,
            best=best,
            alternate=alternate,
            coverage_pick=coverage_pick,
        )

        recommended_reason = self._recommended_reason(shared)
        return DoctorDecisionResponse(
            group_messages=[
                DoctorDecisionSpeakerMessage(
                    speaker="Fit Analyst",
                    content=self._fit_message(shared),
                ),
                DoctorDecisionSpeakerMessage(
                    speaker="Coverage Checker",
                    content=self._coverage_message(shared),
                ),
                DoctorDecisionSpeakerMessage(
                    speaker="Decision Guide",
                    content=self._decision_message(
                        shared=shared,
                        recommended_reason=recommended_reason,
                    ),
                ),
            ],
            shared_brief=self._serialize_shared_brief(shared),
            suggested_prompts=self._suggested_prompts(shared),
            recommended_doctor_id=best.id,
            recommended_reason=recommended_reason,
        )

    def _collect_user_transcript(self, request: DoctorDecisionRequest) -> str:
        user_turns = [
            turn.content.strip()
            for turn in request.conversation
            if turn.role == "user" and turn.content.strip()
        ]
        message = request.message.strip()
        if message and (not user_turns or normalize_text(user_turns[-1]) != normalize_text(message)):
            user_turns.append(message)
        return " ".join(user_turns).strip() or message

    def _latest_user_goal(self, request: DoctorDecisionRequest) -> str:
        for turn in reversed(request.conversation):
            if turn.role == "user" and turn.content.strip():
                return turn.content.strip()
        return request.message.strip()

    def _extract_priorities(
        self,
        transcript: str,
        preferred_language: str | None,
    ) -> dict[str, str | bool | None]:
        text = normalize_text(transcript)
        priorities: dict[str, str | bool | None] = {
            "speed": any(
                term in text
                for term in ["soonest", "earliest", "fast", "quick", "today", "same day", "availability"]
            ),
            "insurance": any(
                term in text
                for term in ["insurance", "network", "in network", "covered", "copay", "cost", "referral"]
            ),
            "distance": any(
                term in text
                for term in ["near", "nearby", "close", "distance", "commute", "walking"]
            ),
            "telehealth": any(term in text for term in ["telehealth", "virtual", "video"]),
            "trust": any(
                term in text for term in ["best", "experience", "experienced", "rating", "review", "trust"]
            ),
            "language": any(term in text for term in ["language", "mandarin", "spanish", "korean", "english"]),
            "clarity": any(
                term in text
                for term in [
                    "explain",
                    "clear",
                    "understand",
                    "questions",
                    "bedside",
                    "patient",
                    "walk me through",
                    "comfortable",
                ]
            ),
            "language_target": None,
        }

        for language in ["Mandarin", "Spanish", "Korean", "English"]:
            if language.lower() in text:
                priorities["language"] = True
                priorities["language_target"] = language
                break

        if priorities["language_target"] is None and preferred_language:
            priorities["language_target"] = preferred_language

        return priorities

    def _priority_labels(self, priorities: dict[str, str | bool | None]) -> list[str]:
        labels: list[str] = []
        if priorities["speed"]:
            labels.append("fastest appointment")
        if priorities["insurance"]:
            labels.append("insurance certainty")
        if priorities["distance"]:
            labels.append("shorter commute")
        if priorities["language"] and priorities["language_target"]:
            labels.append(f"{priorities['language_target']} support")
        if priorities["clarity"]:
            labels.append("clear explanations")
        if priorities["telehealth"]:
            labels.append("telehealth flexibility")
        if priorities["trust"]:
            labels.append("strong trust profile")
        if not labels:
            labels.append("overall balance")
        return labels

    def _decision_score(
        self,
        doctor: DoctorProfile,
        *,
        priorities: dict[str, str | bool | None],
        preferred_language: str | None,
    ) -> float:
        score = float(doctor.ranking_breakdown.total_score if doctor.ranking_breakdown else 0)

        if priorities["speed"]:
            score += 2.2 if doctor.availability_days == 0 else max(0, 4 - doctor.availability_days) * 0.7
        if priorities["insurance"]:
            score += self._coverage_score(doctor)
        if priorities["distance"]:
            score += max(0, 12 - doctor.distance_km) * 0.16
        if priorities["telehealth"]:
            score += 1.2 if doctor.telehealth else -0.4
        if priorities["trust"]:
            score += (doctor.rating * 0.45) + min(doctor.years_experience, 15) * 0.07

        language_target = priorities["language_target"] or preferred_language
        if priorities["language"] and isinstance(language_target, str):
            score += 1.8 if language_target in doctor.languages else -0.8
        if priorities["clarity"]:
            score += self._clarity_score(doctor)

        return score

    def _clarity_score(self, doctor: DoctorProfile) -> float:
        searchable_text = normalize_text(
            " ".join(
                [
                    doctor.profile_blurb,
                    doctor.care_approach,
                    " ".join(doctor.visit_highlights),
                ]
            )
        )
        if any(term in searchable_text for term in ["shared decision", "questions", "education", "explains", "patient goals"]):
            return 1.2
        return 0.3

    def _coverage_score(self, doctor: DoctorProfile) -> float:
        status = doctor.insurance_verification.status if doctor.insurance_verification else "uncertain"
        status_score = {
            "verified": 3.2,
            "likely": 2.1,
            "demo": 1.0,
            "uncertain": -0.6,
        }[status]
        copay_bonus = 0.0
        if doctor.estimated_cost is not None:
            copay_bonus = max(0.0, 80 - doctor.estimated_cost) / 45
        referral_penalty = -0.6 if doctor.referral_required else 0.4
        return status_score + copay_bonus + referral_penalty

    def _build_shared_context(
        self,
        *,
        request: DoctorDecisionRequest,
        transcript: str,
        priorities: dict[str, str | bool | None],
        ranked: list[DoctorProfile],
        best: DoctorProfile,
        alternate: DoctorProfile | None,
        coverage_pick: DoctorProfile,
    ) -> SharedDecisionContext:
        priority_labels = self._priority_labels(priorities)
        shortlist_names = [doctor.name for doctor in ranked[:3]]
        symptom_anchor = request.symptom_text.strip() if request.symptom_text else None
        insurance_anchor = request.insurance_query.strip() if request.insurance_query else None
        language_anchor = (
            str(priorities["language_target"])
            if priorities["language_target"]
            else request.preferred_language
        )
        user_goal = self._latest_user_goal(request) or "Help me choose the best doctor from the shortlist."
        case_summary = self._case_summary(
            shortlist_names=shortlist_names,
            symptom_anchor=symptom_anchor,
            priority_labels=priority_labels,
        )
        coverage_watchout = self._coverage_watchout(best=best, coverage_pick=coverage_pick)

        return SharedDecisionContext(
            transcript=transcript,
            user_goal=user_goal,
            symptom_anchor=symptom_anchor,
            insurance_anchor=insurance_anchor,
            language_anchor=language_anchor,
            priorities=priorities,
            priority_labels=priority_labels,
            ranked=ranked,
            best=best,
            alternate=alternate,
            coverage_pick=coverage_pick,
            shortlist_names=shortlist_names,
            case_summary=case_summary,
            coverage_watchout=coverage_watchout,
        )

    def _case_summary(
        self,
        *,
        shortlist_names: list[str],
        symptom_anchor: str | None,
        priority_labels: list[str],
    ) -> str:
        shortlist_text = ", ".join(shortlist_names) if shortlist_names else "the current shortlist"
        priority_text = ", ".join(priority_labels[:3])
        if symptom_anchor:
            return (
                f"The group is comparing {shortlist_text} for {symptom_anchor[:120]}, "
                f"with the discussion currently prioritizing {priority_text}."
            )
        return (
            f"The group is comparing {shortlist_text}, "
            f"with the discussion currently prioritizing {priority_text}."
        )

    def _coverage_watchout(
        self,
        *,
        best: DoctorProfile,
        coverage_pick: DoctorProfile,
    ) -> str | None:
        if best.referral_required:
            return f"{best.name} may still need a referral before specialist care can be scheduled."
        if (
            best.insurance_verification
            and best.insurance_verification.status in {"uncertain", "demo"}
            and coverage_pick.id != best.id
        ):
            return (
                f"{best.name} is the strongest overall fit, but {coverage_pick.name} is the safer insurance fallback."
            )
        return None

    def _serialize_shared_brief(self, shared: SharedDecisionContext) -> DoctorDecisionSharedBrief:
        return DoctorDecisionSharedBrief(
            case_summary=shared.case_summary,
            patient_goal=shared.user_goal,
            symptom_anchor=shared.symptom_anchor,
            insurance_anchor=shared.insurance_anchor,
            language_anchor=shared.language_anchor,
            priority_labels=shared.priority_labels,
            shortlist_names=shared.shortlist_names,
            leading_doctor_name=shared.best.name,
            backup_doctor_name=shared.alternate.name if shared.alternate else None,
            coverage_watchout=shared.coverage_watchout,
        )

    def _fit_message(self, shared: SharedDecisionContext) -> str:
        focus_preview = (
            ", ".join(shared.best.clinical_focus[:2])
            if shared.best.clinical_focus
            else shared.best.specialty
        )
        priority_text = ", ".join(shared.priority_labels[:2])
        message = (
            f"Using the shared case file, I would keep {shared.best.name} as the clinical lead. "
            f"The strongest fit comes from {shared.best.specialty} care with particular strength in {focus_preview}. "
            f"That lines up well with the current priorities around {priority_text}. "
        )
        if shared.symptom_anchor:
            message += f"I am anchoring this recommendation to the symptom story: {shared.symptom_anchor[:140]}. "
        if shared.alternate is not None:
            message += (
                f"If the user wants a second clinical option in the room, {shared.alternate.name} is the most credible backup."
            )
        return message

    def _coverage_message(self, shared: SharedDecisionContext) -> str:
        best_label = (
            shared.best.insurance_verification.label
            if shared.best.insurance_verification
            else "No verification yet"
        )
        best_cost = (
            f"${shared.best.estimated_cost} estimated copay"
            if shared.best.estimated_cost is not None
            else "estimated cost still depends on plan"
        )
        if shared.coverage_pick.id == shared.best.id:
            return (
                f"Reviewing the same shortlist and priorities, I agree the front-runner is also the safest coverage choice. "
                f"{shared.best.name} is marked {best_label.lower()}, with {best_cost}, "
                f"and {'a referral may still be needed' if shared.best.referral_required else 'referral is usually not required'}."
            )

        coverage_label = (
            shared.coverage_pick.insurance_verification.label
            if shared.coverage_pick.insurance_verification
            else "No verification yet"
        )
        watchout = (
            f" {shared.coverage_watchout}"
            if shared.coverage_watchout
            else ""
        )
        return (
            f"Looking at the shared case file from the insurance side, {shared.coverage_pick.name} is the cleaner coverage-first fallback because it is marked "
            f"{coverage_label.lower()}. {shared.best.name} still has the better overall balance, but this is the place where I would ask the user how much risk they can tolerate.{watchout}"
        )

    def _decision_message(
        self,
        *,
        shared: SharedDecisionContext,
        recommended_reason: str,
    ) -> str:
        message = (
            f"Taking Fit Analyst's clinical lead and Coverage Checker's risk review together, my final call is to start with {shared.best.name}. "
            f"{recommended_reason} "
        )
        if shared.alternate is not None:
            message += (
                f"If the user becomes more insurance-conservative or wants a different bedside style, I would keep {shared.alternate.name} as the main alternative."
            )
        return message

    def _recommended_reason(self, shared: SharedDecisionContext) -> str:
        reasons: list[str] = []
        doctor = shared.best
        priorities = shared.priorities

        if priorities["speed"]:
            reasons.append(
                "It gives one of the fastest paths to an appointment"
                if doctor.availability_days <= 1
                else "It still balances fit well even if speed is not the absolute best"
            )
        if priorities["insurance"] and doctor.insurance_verification:
            reasons.append(f"the insurance status is {doctor.insurance_verification.label.lower()}")
        if priorities["language"] and shared.language_anchor and shared.language_anchor in doctor.languages:
            reasons.append(f"it supports {shared.language_anchor}")
        if priorities["clarity"]:
            reasons.append("the profile suggests a clearer and more explanatory visit style")
        if priorities["distance"]:
            reasons.append("it stays relatively close to the search area")
        if priorities["trust"]:
            reasons.append("it has a strong trust and experience profile")

        if not reasons:
            reasons.append("it offers the cleanest overall balance across fit, insurance, access, and trust")
        return reasons[0][0].upper() + reasons[0][1:] + "."

    def _suggested_prompts(self, shared: SharedDecisionContext) -> list[str]:
        prompts = [
            "Ask Fit Analyst to compare the top two doctors on clinical fit.",
            "Ask Coverage Checker whether the safer in-network choice changes the recommendation.",
            "Ask Decision Guide what happens if speed matters less than communication style.",
            "Ask the group which doctor is easiest for a first visit if I am anxious about the process.",
        ]
        if shared.priorities["language"]:
            prompts[2] = "Ask Decision Guide whether language support should outweigh rating or distance."
        if shared.priorities["insurance"]:
            prompts[1] = "Ask Coverage Checker whether the most verified network option should become the top choice."
        return prompts
