from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.doctor import DoctorProfile


class DoctorDecisionConversationTurn(BaseModel):
    role: Literal["user", "assistant"]
    speaker: str
    content: str


class DoctorDecisionSpeakerMessage(BaseModel):
    speaker: Literal["Fit Analyst", "Coverage Checker", "Decision Guide"]
    content: str


class DoctorDecisionSharedBrief(BaseModel):
    shared_context_confirmed: bool = True
    case_summary: str
    patient_goal: str
    symptom_anchor: str | None = None
    insurance_anchor: str | None = None
    language_anchor: str | None = None
    priority_labels: list[str] = Field(default_factory=list)
    shortlist_names: list[str] = Field(default_factory=list)
    leading_doctor_name: str | None = None
    backup_doctor_name: str | None = None
    coverage_watchout: str | None = None


class DoctorDecisionRequest(BaseModel):
    message: str
    conversation: list[DoctorDecisionConversationTurn] = Field(default_factory=list)
    doctors: list[DoctorProfile] = Field(default_factory=list)
    symptom_text: str | None = None
    insurance_query: str | None = None
    preferred_language: str | None = None


class DoctorDecisionResponse(BaseModel):
    group_messages: list[DoctorDecisionSpeakerMessage] = Field(default_factory=list)
    shared_brief: DoctorDecisionSharedBrief | None = None
    suggested_prompts: list[str] = Field(default_factory=list)
    recommended_doctor_id: str | None = None
    recommended_reason: str | None = None
