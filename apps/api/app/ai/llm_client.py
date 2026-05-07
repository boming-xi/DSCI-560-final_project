from __future__ import annotations

import json
import logging
import re
from typing import Protocol

from openai import OpenAI

from app.utils.parsers import sentence_split

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    provider_name: str

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        ...


class DemoLLMClient:
    provider_name = "demo"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        language = "English"
        if "Reply in Mandarin" in user_prompt or "Write the final bullets in Mandarin" in user_prompt:
            language = "Mandarin"
        elif "Reply in Spanish" in user_prompt or "Write the final bullets in Spanish" in user_prompt:
            language = "Spanish"

        if "Rewrite the following brand-level insurance explanation" in user_prompt:
            json_match = re.search(r"\{.*\}$", user_prompt, re.DOTALL)
            if json_match:
                try:
                    payload = json.loads(json_match.group(0))
                    recommendation = payload.get("recommendation", {})
                    profile = payload.get("user_profile", {})
                    provider = recommendation.get("provider") or "this carrier"
                    plan_name = recommendation.get("plan_name") or "the lead plan"
                    plan_type = recommendation.get("plan_type") or "coverage"
                    premium = recommendation.get("monthly_premium_amount")
                    deductible = recommendation.get("deductible_amount")
                    quality = recommendation.get("quality_rating")
                    network_flexibility = recommendation.get("network_flexibility") or ""
                    available_plan_count = recommendation.get("available_plan_count")
                    referral_tolerance = str(profile.get("referral_tolerance") or "")
                    care_usage_pattern = str(profile.get("care_usage_pattern") or "")
                    prescription_needs = str(profile.get("prescription_needs") or "")

                    if language == "Mandarin":
                        reasons: list[str] = [
                            f"{provider} 可以作为起点，因为代表计划 {plan_name} 让你先看到这个品牌在 {plan_type} 路径上的整体取舍。"
                        ]
                        if premium is not None:
                            reasons.append(
                                f"按当前资料看，这个品牌的代表计划月保费大约 ${premium:.0f}，便于你先判断预算舒适区。"
                            )
                        if "direct" in referral_tolerance.lower() or "avoid" in referral_tolerance.lower():
                            reasons.append("你更希望减少转诊摩擦，而这个品牌当前展示的计划路径对专科就诊更直接。")
                        elif care_usage_pattern.lower() in {"high", "regular"}:
                            reasons.append("你预计会更频繁使用医疗服务，所以先看结构更完整、解释更清楚的品牌更稳妥。")
                        else:
                            reasons.append("它先把成本、网络和可达性放在同一张卡片里，更适合作为第一轮比较对象。")
                        if quality is not None:
                            reasons.append(f"公开质量评分大约 {quality:.1f} / 5，也让它更适合作为第一批候选。")

                        tradeoffs: list[str] = []
                        if deductible is not None and deductible >= 5000:
                            tradeoffs.append(f"免赔额大约 ${deductible:.0f}，意味着真正报销前，自付压力可能仍然偏高。")
                        if network_flexibility == "tighter":
                            tradeoffs.append("这个品牌下的一些计划网络会更收紧，所以正式选定前仍要核对医生可用性。")
                        if prescription_needs.lower() in {"ongoing", "regular", "high"}:
                            tradeoffs.append("如果你有持续处方药需求，药物目录和实际 copay 仍需要到官方页面再确认一次。")
                        if premium is None:
                            tradeoffs.append("部分费用信息仍可能因年龄、补贴或地区变化而调整，需要以官方报价为准。")
                        if not tradeoffs:
                            tradeoffs.append("最终投保前，仍需要在官方页面确认网络、补贴和医生覆盖是否完全匹配。")
                    elif language == "Spanish":
                        reasons = [
                            f"{provider} es un buen punto de partida porque su plan guía, {plan_name}, te deja comparar esta marca con una ruta de {plan_type} más concreta."
                        ]
                        if premium is not None:
                            reasons.append(
                                f"Con la información actual, la prima estimada ronda los ${premium:.0f}, lo que ayuda a ubicar rápido si entra en tu zona de comodidad."
                            )
                        if "direct" in referral_tolerance.lower() or "avoid" in referral_tolerance.lower():
                            reasons.append("Dijiste que prefieres menos fricción por referidos, y esta marca mantiene un acceso más directo dentro de la comparación actual.")
                        elif care_usage_pattern.lower() in {"high", "regular"}:
                            reasons.append("Como esperas usar atención con más frecuencia, conviene empezar por una marca cuyo equilibrio entre costo y acceso sea más fácil de leer.")
                        else:
                            reasons.append("Pone costo, red y acceso en una sola vista, así que funciona bien como primera marca para comparar.")
                        if quality is not None:
                            reasons.append(f"También parte con una calificación pública cercana a {quality:.1f} / 5, lo que refuerza ese punto de partida.")

                        tradeoffs = []
                        if deductible is not None and deductible >= 5000:
                            tradeoffs.append(
                                f"El deducible ronda los ${deductible:.0f}, así que el gasto de bolsillo puede seguir siendo alto antes de que la cobertura realmente se active."
                            )
                        if network_flexibility == "tighter":
                            tradeoffs.append("Algunos planes de esta marca usan redes más estrechas, así que todavía conviene verificar doctores antes de decidir.")
                        if prescription_needs.lower() in {"ongoing", "regular", "high"}:
                            tradeoffs.append("Si dependes de recetas continuas, todavía hay que confirmar el formulario y los copagos exactos en el sitio oficial.")
                        if premium is None:
                            tradeoffs.append("Parte del costo final puede cambiar según edad, subsidios o zona, así que la última palabra la tiene la cotización oficial.")
                        if not tradeoffs:
                            tradeoffs.append("Antes de inscribirte, aún debes confirmar en el sitio oficial la red, los subsidios y el encaje con tus doctores.")
                    else:
                        reasons = [
                            f"{provider} is a strong starting point because its lead option, {plan_name}, gives you a concrete first read on this brand's {plan_type} tradeoff."
                        ]
                        if premium is not None:
                            reasons.append(
                                f"With the information you shared, the lead plan lands around ${premium:.0f} per month, which helps anchor whether this carrier fits your comfort range."
                            )
                        if "direct" in referral_tolerance.lower() or "avoid" in referral_tolerance.lower():
                            reasons.append(
                                "You said you prefer less referral friction, and this carrier's lead path keeps specialist access more direct in the current comparison."
                            )
                        elif care_usage_pattern.lower() in {"high", "regular"}:
                            reasons.append(
                                "Because you expect to use care more regularly, it helps to start with a brand whose balance of cost and access is easier to evaluate up front."
                            )
                        else:
                            reasons.append(
                                "It gives you a clean first comparison across cost, network shape, and access without forcing you into plan-level detail too early."
                            )
                        if quality is not None:
                            reasons.append(
                                f"It also comes in with a public quality signal around {quality:.1f} / 5, which makes it a steadier place to begin."
                            )

                        tradeoffs = []
                        if deductible is not None and deductible >= 5000:
                            tradeoffs.append(
                                f"The deductible is around ${deductible:.0f}, so out-of-pocket spending can still feel heavy before coverage really kicks in."
                            )
                        if network_flexibility == "tighter":
                            tradeoffs.append(
                                "Some plans under this carrier use a tighter network, so doctor verification still matters before you commit."
                            )
                        if prescription_needs.lower() in {"ongoing", "regular", "high"}:
                            tradeoffs.append(
                                "If you rely on ongoing prescriptions, the formulary and exact drug copays still need a final official check."
                            )
                        if premium is None:
                            tradeoffs.append(
                                "Final costs may still shift by age, subsidy, or service area, so the official quote remains the source of truth."
                            )
                        if not tradeoffs:
                            tradeoffs.append(
                                "Before enrolling, you still need the official site to confirm network details, subsidies, and doctor compatibility."
                            )

                    return json.dumps(
                        {
                            "reasons": reasons[:4],
                            "tradeoffs": tradeoffs[:4],
                        },
                        ensure_ascii=False,
                    )
                except Exception:
                    pass

        if "Insurance advisor profile:" in user_prompt:
            missing_match = re.search(r"Missing fields:\s*(.+)\n", user_prompt)
            shortlist_match = re.search(r"Current shortlist:\s*(.+)", user_prompt)
            current_message_match = re.search(r"Current user message:\s*(.+?)\nCurrent shortlist:", user_prompt, re.DOTALL)
            missing_fields = missing_match.group(1).strip() if missing_match else "[]"
            shortlist = shortlist_match.group(1).strip() if shortlist_match else "none yet"
            current_message = (
                current_message_match.group(1).strip()
                if current_message_match
                else "the user wants help choosing insurance"
            )
            if "none" not in shortlist and shortlist != "none yet":
                if language == "Mandarin":
                    return (
                        f"谢谢，这很有帮助。我已经有一个初步候选列表：{shortlist}。"
                        "接下来告诉我，你更在意更低的月保费，还是更直接的专科就诊路径，这样我可以进一步收紧排序。"
                    )
                if language == "Spanish":
                    return (
                        f"Gracias, esto ayuda. Ya tengo una lista preliminar: {shortlist}. "
                        "Ahora dime si te importa más una prima mensual más baja o un acceso más directo a especialistas para afinar la clasificación."
                    )
                return (
                    f"Thanks, that helps. I already have a preliminary shortlist: {shortlist}. "
                    "Tell me whether lower monthly cost or easier specialist access matters more so I can tighten the ranking."
                )
            if language == "Mandarin":
                return (
                    f"谢谢，这给了我一个更好的起点。我还想确认这些信息：{missing_fields}。"
                    f"你刚刚提到的是：{current_message}"
                )
            if language == "Spanish":
                return (
                    f"Gracias, esto me da un mejor punto de partida. Todavía quiero aclarar {missing_fields}. "
                    f"Acabas de mencionar: {current_message}"
                )
            return (
                f"Thanks, that gives me a better starting point. I still want to clarify {missing_fields}. "
                f"You just mentioned: {current_message}"
            )

        current_message_match = re.search(r"Current user message:\s*(.+)$", user_prompt, re.DOTALL)
        next_step_match = re.search(r"Suggested next step:\s*(.+)", user_prompt)
        if current_message_match:
            current_message = current_message_match.group(1).strip()
            next_step = (
                next_step_match.group(1).strip()
                if next_step_match
                else "Start with the recommended care path and escalate if symptoms worsen."
            )
            return (
                f"Based on what you shared, {next_step} "
                f"If symptoms get worse, new red flags appear, or you are worried about rapid changes, seek more urgent care. "
                f"You asked: {current_message}"
            )

        document_match = re.search(
            r"Document text:\n(.*?)\n\nHelpful context:",
            user_prompt,
            re.DOTALL,
        )
        if document_match:
            document_text = document_match.group(1).strip()
            sentences = sentence_split(document_text)
            summary = " ".join(sentences[:2]) if sentences else document_text
            return (
                f"{summary} This is only a plain-language summary and should be confirmed with a clinician."
            ).strip()

        return user_prompt.strip()


class OpenAILLMClient:
    provider_name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str,
        reasoning_effort: str = "low",
        max_output_tokens: int = 700,
    ) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.max_output_tokens = max_output_tokens

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        payload: dict[str, object] = {
            "model": self.model,
            "instructions": system_prompt,
            "input": user_prompt,
            "max_output_tokens": self.max_output_tokens,
        }
        if self._supports_reasoning():
            payload["reasoning"] = {"effort": self.reasoning_effort}

        response = self.client.responses.create(**payload)
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        for item in getattr(response, "output", []) or []:
            for content_part in getattr(item, "content", []) or []:
                text = getattr(content_part, "text", None)
                if isinstance(text, str) and text.strip():
                    return text.strip()

        raise RuntimeError("OpenAI response did not contain text output.")

    def _supports_reasoning(self) -> bool:
        return self.model.startswith(("gpt-5", "o1", "o3", "o4"))


class ResilientLLMClient:
    def __init__(self, primary: LLMClient, fallback: LLMClient) -> None:
        self.primary = primary
        self.fallback = fallback
        self.provider_name = primary.provider_name

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            return self.primary.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        except Exception as exc:
            logger.warning("OpenAI completion failed, falling back to demo response: %s", exc)
            self.provider_name = self.fallback.provider_name
            return self.fallback.complete(system_prompt=system_prompt, user_prompt=user_prompt)
