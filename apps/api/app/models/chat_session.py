from __future__ import annotations

from pydantic import BaseModel, Field


class ChatSessionRecord(BaseModel):
    session_id: str
    turns: list[dict[str, str]] = Field(default_factory=list)

