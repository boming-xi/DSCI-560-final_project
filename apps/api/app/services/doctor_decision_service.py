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
    def _language(self, ui_language: str | None) -> str:
        if ui_language in {"Mandarin", "Spanish"}:
            return ui_language
        return "English"

    def reply(self, request: DoctorDecisionRequest) -> DoctorDecisionResponse:
        language = self._language(request.ui_language)
        doctors = request.doctors[:5]
        if not doctors:
            return DoctorDecisionResponse(
                group_messages=[
                    DoctorDecisionSpeakerMessage(
                        speaker="Decision Guide",
                        content={
                            "English": "I need a current doctor shortlist before I can help with the final choice. Run doctor search first, then I can compare the options.",
                            "Mandarin": "我需要先拿到当前的医生候选列表，才能帮你做最后选择。请先运行医生搜索，然后我再来比较这些选项。",
                            "Spanish": "Necesito primero una lista actual de doctores antes de ayudarte con la elección final. Ejecuta la búsqueda de doctores y luego comparo las opciones.",
                        }[language],
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
            language=language,
        )

        recommended_reason = self._recommended_reason(shared, language)
        return DoctorDecisionResponse(
            group_messages=[
                DoctorDecisionSpeakerMessage(
                    speaker="Fit Analyst",
                    content=self._fit_message(shared, language),
                ),
                DoctorDecisionSpeakerMessage(
                    speaker="Coverage Checker",
                    content=self._coverage_message(shared, language),
                ),
                DoctorDecisionSpeakerMessage(
                    speaker="Decision Guide",
                    content=self._decision_message(
                        shared=shared,
                        recommended_reason=recommended_reason,
                        language=language,
                    ),
                ),
            ],
            shared_brief=self._serialize_shared_brief(shared),
            suggested_prompts=self._suggested_prompts(shared, language),
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

    def _priority_labels(
        self,
        priorities: dict[str, str | bool | None],
        language: str,
    ) -> list[str]:
        labels: list[str] = []
        if priorities["speed"]:
            labels.append(
                {
                    "English": "fastest appointment",
                    "Mandarin": "尽快约到号",
                    "Spanish": "cita más rápida",
                }[language]
            )
        if priorities["insurance"]:
            labels.append(
                {
                    "English": "insurance certainty",
                    "Mandarin": "保险更确定",
                    "Spanish": "certeza del seguro",
                }[language]
            )
        if priorities["distance"]:
            labels.append(
                {
                    "English": "shorter commute",
                    "Mandarin": "通勤更短",
                    "Spanish": "trayecto más corto",
                }[language]
            )
        if priorities["language"] and priorities["language_target"]:
            labels.append(
                {
                    "English": f"{priorities['language_target']} support",
                    "Mandarin": f"{priorities['language_target']} 支持",
                    "Spanish": f"atención en {priorities['language_target']}",
                }[language]
            )
        if priorities["clarity"]:
            labels.append(
                {
                    "English": "clear explanations",
                    "Mandarin": "讲解清楚",
                    "Spanish": "explicaciones claras",
                }[language]
            )
        if priorities["telehealth"]:
            labels.append(
                {
                    "English": "telehealth flexibility",
                    "Mandarin": "远程问诊灵活",
                    "Spanish": "flexibilidad de telemedicina",
                }[language]
            )
        if priorities["trust"]:
            labels.append(
                {
                    "English": "strong trust profile",
                    "Mandarin": "信任度更强",
                    "Spanish": "perfil de confianza sólido",
                }[language]
            )
        if not labels:
            labels.append(
                {
                    "English": "overall balance",
                    "Mandarin": "整体平衡",
                    "Spanish": "equilibrio general",
                }[language]
            )
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
            "uncertain": -0.6,
        }.get(status, -0.6)
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
        language: str,
    ) -> SharedDecisionContext:
        priority_labels = self._priority_labels(priorities, language)
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
            language=language,
        )
        coverage_watchout = self._coverage_watchout(
            best=best,
            coverage_pick=coverage_pick,
            language=language,
        )

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
        language: str,
    ) -> str:
        shortlist_text = ", ".join(shortlist_names) if shortlist_names else "the current shortlist"
        priority_text = ", ".join(priority_labels[:3])
        if symptom_anchor:
            if language == "Mandarin":
                return (
                    f"当前讨论在比较 {shortlist_text}，针对的症状背景是：{symptom_anchor[:120]}，"
                    f"目前最优先考虑的是 {priority_text}。"
                )
            if language == "Spanish":
                return (
                    f"El grupo está comparando {shortlist_text} para {symptom_anchor[:120]}, "
                    f"y ahora mismo prioriza {priority_text}."
                )
            return (
                f"The group is comparing {shortlist_text} for {symptom_anchor[:120]}, "
                f"with the discussion currently prioritizing {priority_text}."
            )
        if language == "Mandarin":
            return (
                f"当前讨论在比较 {shortlist_text}，目前最优先考虑的是 {priority_text}。"
            )
        if language == "Spanish":
            return (
                f"El grupo está comparando {shortlist_text}, y ahora mismo prioriza {priority_text}."
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
        language: str,
    ) -> str | None:
        if best.referral_required:
            if language == "Mandarin":
                return f"{best.name} 在安排专科就诊前，可能仍然需要先拿到转诊。"
            if language == "Spanish":
                return f"{best.name} todavía podría necesitar un referido antes de programar atención especializada."
            return f"{best.name} may still need a referral before specialist care can be scheduled."
        if (
            best.insurance_verification
            and best.insurance_verification.status == "uncertain"
            and coverage_pick.id != best.id
        ):
            if language == "Mandarin":
                return f"{best.name} 是整体最优选择，但 {coverage_pick.name} 是保险层面更稳妥的备选。"
            if language == "Spanish":
                return f"{best.name} es la mejor opción general, pero {coverage_pick.name} es el respaldo más seguro desde el punto de vista del seguro."
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

    def _fit_message(self, shared: SharedDecisionContext, language: str) -> str:
        focus_preview = (
            ", ".join(shared.best.clinical_focus[:2])
            if shared.best.clinical_focus
            else shared.best.specialty
        )
        priority_text = ", ".join(shared.priority_labels[:2])
        if language == "Mandarin":
            message = (
                f"基于这份共享病例摘要，我会继续把 {shared.best.name} 放在临床匹配的第一位。"
                f"最强的匹配点来自 {shared.best.specialty}，尤其擅长 {focus_preview}。"
                f"这和当前优先考虑的 {priority_text} 很一致。"
            )
        elif language == "Spanish":
            message = (
                f"Usando el expediente compartido, mantendría a {shared.best.name} como líder clínico. "
                f"El ajuste más fuerte viene de su atención en {shared.best.specialty}, con fortaleza particular en {focus_preview}. "
                f"Eso encaja bien con las prioridades actuales alrededor de {priority_text}. "
            )
        else:
            message = (
                f"Using the shared case file, I would keep {shared.best.name} as the clinical lead. "
                f"The strongest fit comes from {shared.best.specialty} care with particular strength in {focus_preview}. "
                f"That lines up well with the current priorities around {priority_text}. "
            )
        if shared.symptom_anchor:
            if language == "Mandarin":
                message += f"我把这条建议锚定在你的症状描述上：{shared.symptom_anchor[:140]}。"
            elif language == "Spanish":
                message += f"Estoy anclando esta recomendación a la historia de síntomas: {shared.symptom_anchor[:140]}. "
            else:
                message += f"I am anchoring this recommendation to the symptom story: {shared.symptom_anchor[:140]}. "
        if shared.alternate is not None:
            if language == "Mandarin":
                message += f"如果你想保留第二个临床上也说得通的选择，{shared.alternate.name} 是最可信的备选。"
            elif language == "Spanish":
                message += f"Si el usuario quiere una segunda opción clínica en la mesa, {shared.alternate.name} es el respaldo más creíble."
            else:
                message += (
                    f"If the user wants a second clinical option in the room, {shared.alternate.name} is the most credible backup."
                )
        return message

    def _coverage_message(self, shared: SharedDecisionContext, language: str) -> str:
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
            if language == "Mandarin":
                return (
                    f"从保险和网络角度看，我同意目前排第一的医生也是更稳妥的覆盖选择。"
                    f"{shared.best.name} 当前标记为 {best_label.lower()}，费用上 {best_cost}，"
                    f"{'而且可能仍然需要转诊' if shared.best.referral_required else '通常不需要转诊'}。"
                )
            if language == "Spanish":
                return (
                    f"Revisando la misma lista y prioridades, coincido en que el doctor líder también es la opción de cobertura más segura. "
                    f"{shared.best.name} está marcado como {best_label.lower()}, con {best_cost}, "
                    f"y {'todavía puede requerir un referido' if shared.best.referral_required else 'normalmente no requiere referido'}."
                )
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
        if language == "Mandarin":
            return (
                f"如果只从保险角度看，{shared.coverage_pick.name} 是更干净的覆盖优先备选，因为它当前标记为 {coverage_label.lower()}。"
                f"{shared.best.name} 在整体平衡上仍然更好，但这里我会进一步确认你愿意承受多少网络风险。{watchout}"
            )
        if language == "Spanish":
            return (
                f"Mirando el caso compartido desde el lado del seguro, {shared.coverage_pick.name} es el respaldo más limpio si priorizamos cobertura, porque está marcado como {coverage_label.lower()}. "
                f"{shared.best.name} sigue teniendo el mejor equilibrio general, pero aquí yo preguntaría cuánto riesgo quiere tolerar el usuario.{watchout}"
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
        language: str,
    ) -> str:
        if language == "Mandarin":
            message = (
                f"综合 Fit Analyst 的临床判断和 Coverage Checker 的风险评估后，我最后建议先从 {shared.best.name} 开始。"
                f"{recommended_reason} "
            )
        elif language == "Spanish":
            message = (
                f"Tomando juntos el liderazgo clínico de Fit Analyst y la revisión de riesgo de Coverage Checker, mi decisión final es empezar con {shared.best.name}. "
                f"{recommended_reason} "
            )
        else:
            message = (
                f"Taking Fit Analyst's clinical lead and Coverage Checker's risk review together, my final call is to start with {shared.best.name}. "
                f"{recommended_reason} "
            )
        if shared.alternate is not None:
            if language == "Mandarin":
                message += f"如果你后来更保守地看待保险风险，或更在意沟通风格不同，我会把 {shared.alternate.name} 作为主要备选。"
            elif language == "Spanish":
                message += f"Si el usuario después se vuelve más conservador con el seguro o quiere otro estilo de trato, mantendría a {shared.alternate.name} como la alternativa principal."
            else:
                message += (
                    f"If the user becomes more insurance-conservative or wants a different bedside style, I would keep {shared.alternate.name} as the main alternative."
                )
        return message

    def _recommended_reason(self, shared: SharedDecisionContext, language: str) -> str:
        reasons: list[str] = []
        doctor = shared.best
        priorities = shared.priorities

        if priorities["speed"]:
            reasons.append(
                {
                    "English": "It gives one of the fastest paths to an appointment"
                    if doctor.availability_days <= 1
                    else "It still balances fit well even if speed is not the absolute best",
                    "Mandarin": "它提供了最快的一批就诊路径之一"
                    if doctor.availability_days <= 1
                    else "即使不是最快，它在整体匹配上仍然很平衡",
                    "Spanish": "Ofrece una de las rutas más rápidas para conseguir cita"
                    if doctor.availability_days <= 1
                    else "Sigue equilibrando muy bien el ajuste aunque no sea la opción más rápida",
                }[language]
            )
        if priorities["insurance"] and doctor.insurance_verification:
            reasons.append(
                {
                    "English": f"the insurance status is {doctor.insurance_verification.label.lower()}",
                    "Mandarin": f"它的保险状态是 {doctor.insurance_verification.label.lower()}",
                    "Spanish": f"el estado del seguro es {doctor.insurance_verification.label.lower()}",
                }[language]
            )
        if priorities["language"] and shared.language_anchor and shared.language_anchor in doctor.languages:
            reasons.append(
                {
                    "English": f"it supports {shared.language_anchor}",
                    "Mandarin": f"它支持 {shared.language_anchor}",
                    "Spanish": f"ofrece atención en {shared.language_anchor}",
                }[language]
            )
        if priorities["clarity"]:
            reasons.append(
                {
                    "English": "the profile suggests a clearer and more explanatory visit style",
                    "Mandarin": "资料显示它的就诊风格更重视解释和说明",
                    "Spanish": "el perfil sugiere un estilo de visita más claro y explicativo",
                }[language]
            )
        if priorities["distance"]:
            reasons.append(
                {
                    "English": "it stays relatively close to the search area",
                    "Mandarin": "它离你的搜索区域相对更近",
                    "Spanish": "se mantiene relativamente cerca del área de búsqueda",
                }[language]
            )
        if priorities["trust"]:
            reasons.append(
                {
                    "English": "it has a strong trust and experience profile",
                    "Mandarin": "它的信任度和经验画像都更强",
                    "Spanish": "tiene un perfil sólido de confianza y experiencia",
                }[language]
            )

        if not reasons:
            reasons.append(
                {
                    "English": "it offers the cleanest overall balance across fit, insurance, access, and trust",
                    "Mandarin": "它在匹配度、保险、可达性和信任度之间给出了最平衡的组合",
                    "Spanish": "ofrece el equilibrio más limpio entre ajuste, seguro, acceso y confianza",
                }[language]
            )
        return reasons[0][0].upper() + reasons[0][1:] + "."

    def _suggested_prompts(self, shared: SharedDecisionContext, language: str) -> list[str]:
        prompts = {
            "English": [
                "Ask Fit Analyst to compare the top two doctors on clinical fit.",
                "Ask Coverage Checker whether the safer in-network choice changes the recommendation.",
                "Ask Decision Guide what happens if speed matters less than communication style.",
                "Ask the group which doctor is easiest for a first visit if I am anxious about the process.",
            ],
            "Mandarin": [
                "请 Fit Analyst 比较一下前两位医生在临床匹配上的差别。",
                "请 Coverage Checker 看看更稳妥的院内网络选择会不会改变推荐。",
                "请 Decision Guide 解释一下：如果速度没那么重要，沟通风格会不会改变选择。",
                "如果我是第一次看诊而且比较紧张，请问哪位医生会更容易开始？",
            ],
            "Spanish": [
                "Pide a Fit Analyst que compare a los dos mejores doctores en ajuste clínico.",
                "Pide a Coverage Checker que evalúe si la opción más segura dentro de la red cambia la recomendación.",
                "Pide a Decision Guide que explique qué pasa si la rapidez importa menos que el estilo de comunicación.",
                "Pregunta al grupo qué doctor sería más fácil para una primera visita si estoy ansioso por el proceso.",
            ],
        }[language]
        if shared.priorities["language"]:
            prompts[2] = {
                "English": "Ask Decision Guide whether language support should outweigh rating or distance.",
                "Mandarin": "请 Decision Guide 判断：语言支持是否应该比评分或距离更重要。",
                "Spanish": "Pide a Decision Guide que evalúe si el apoyo en idioma debe pesar más que la calificación o la distancia.",
            }[language]
        if shared.priorities["insurance"]:
            prompts[1] = {
                "English": "Ask Coverage Checker whether the most verified network option should become the top choice.",
                "Mandarin": "请 Coverage Checker 判断：网络核验最稳的选项是否应该升为首选。",
                "Spanish": "Pide a Coverage Checker que evalúe si la opción con red más verificada debería convertirse en la principal.",
            }[language]
        return prompts
