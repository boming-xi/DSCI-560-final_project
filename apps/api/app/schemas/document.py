from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentExplainRequest(BaseModel):
    title: str | None = None
    content: str
    document_type: str = "medical_report"


class DocumentExplainResponse(BaseModel):
    summary: str
    important_terms: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    disclaimer: str

