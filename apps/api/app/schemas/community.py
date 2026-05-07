from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


UiLanguage = Literal["English", "Mandarin", "Spanish"]


class CommunityMatchRequest(BaseModel):
    symptom_text: str = Field(min_length=2, max_length=1200)
    care_path: str | None = None
    urgency_band: str | None = None
    preferred_language: str | None = None
    region: str | None = None
    ui_language: UiLanguage | None = None


class CommunityDiscoverRequest(BaseModel):
    symptom_text: str | None = Field(default=None, min_length=2, max_length=1200)
    care_path: str | None = None
    urgency_band: str | None = None
    preferred_language: str | None = None
    region: str | None = None
    ui_language: UiLanguage | None = None


class CommunityJoinRequest(BaseModel):
    symptom_text: str | None = Field(default=None, min_length=2, max_length=1200)
    care_path: str | None = None
    urgency_band: str | None = None
    preferred_language: str | None = None
    region: str | None = None
    ui_language: UiLanguage | None = None


class CommunityCreateRoomRequest(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    focus: str = Field(min_length=8, max_length=400)
    symptom_text: str | None = Field(default=None, min_length=2, max_length=1200)
    care_path: str | None = None
    urgency_band: str | None = None
    preferred_language: str | None = None
    region: str | None = None
    ui_language: UiLanguage | None = None


class CommunityMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=1200)
    ui_language: UiLanguage | None = None


class CommunityRoomSummary(BaseModel):
    id: str
    title: str
    description: str | None = None
    match_reason: str | None = None
    preview_topics: list[str] = Field(default_factory=list)
    care_path: str
    urgency_band: str
    symptom_tags: list[str]
    language: str
    region: str
    member_count: int
    message_count: int
    latest_activity_at: datetime


class CommunityMessage(BaseModel):
    id: str
    user_id: str
    display_name: str
    content: str
    created_at: datetime
    is_current_user: bool = False


class CommunityRoomResponse(BaseModel):
    room: CommunityRoomSummary
    messages: list[CommunityMessage]
    your_alias: str
    safety_notice: str
    moderation_notice: str
    entry_prompt: str
    matching_summary: str
    starter_topics: list[str]


class CommunityRoomCatalogResponse(BaseModel):
    selected_context_summary: str
    recommended_rooms: list[CommunityRoomSummary]
    browse_rooms: list[CommunityRoomSummary]
