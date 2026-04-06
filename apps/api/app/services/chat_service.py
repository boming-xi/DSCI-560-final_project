from __future__ import annotations

from app.ai.prompt_templates import CHAT_SYSTEM_PROMPT
from app.ai.llm_client import LLMClient
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.symptom import SymptomTriageRequest
from app.services.insurance_service import InsuranceService
from app.services.triage_service import TriageService


class ChatService:
    def __init__(
        self,
        triage_service: TriageService,
        insurance_service: InsuranceService,
        llm_client: LLMClient,
    ) -> None:
        self.triage_service = triage_service
        self.insurance_service = insurance_service
        self.llm_client = llm_client

    def reply(self, request: ChatRequest) -> ChatResponse:
        symptom_text = request.symptom_text or request.message
        triage = self.triage_service.triage(
            SymptomTriageRequest(symptom_text=symptom_text, duration_days=1)
        )
        insurance_summary = self.insurance_service.summarize_query(request.insurance_query)
        insurance_note = (
            f"Insurance match: {insurance_summary.provider} {insurance_summary.plan_name}."
            if insurance_summary and insurance_summary.matched
            else "Insurance details are still unclear."
        )
        conversation_history = "\n".join(
            f"{turn.role}: {turn.content}" for turn in request.conversation[-6:]
        ) or "No earlier conversation."
        reply = self.llm_client.complete(
            system_prompt=CHAT_SYSTEM_PROMPT,
            user_prompt=(
                "Use the context below to answer as a cautious healthcare navigation assistant.\n\n"
                f"Triage summary: {triage.summary}\n"
                f"Urgency: {triage.urgency_level}\n"
                f"Suggested next step: {triage.next_step}\n"
                f"{insurance_note}\n"
                f"Relevant specialties: {', '.join(triage.matched_specialties)}\n\n"
                f"Recent conversation:\n{conversation_history}\n\n"
                f"Current user message: {request.message}"
            ),
        )
        return ChatResponse(
            reply=reply,
            cited_items=triage.matched_specialties,
            suggested_next_actions=[
                triage.next_step,
                "Review the doctor recommendations page for ranked options.",
            ],
        )
