from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation: list[ChatTurn] = Field(default_factory=list)
    symptom_text: str | None = None
    insurance_query: str | None = None


class ChatResponse(BaseModel):
    reply: str
    cited_items: list[str] = Field(default_factory=list)
    suggested_next_actions: list[str] = Field(default_factory=list)

