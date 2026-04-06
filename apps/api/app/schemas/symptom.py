from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Location(BaseModel):
    latitude: float
    longitude: float


class SymptomTriageRequest(BaseModel):
    symptom_text: str
    duration_days: int | None = 1
    age: int | None = None
    existing_conditions: list[str] = Field(default_factory=list)
    location: Location | None = None


class TriageRecommendation(BaseModel):
    urgency_level: Literal["self-care", "routine", "soon", "urgent", "emergency"]
    care_type: str
    summary: str
    red_flags: list[str] = Field(default_factory=list)
    next_step: str
    safety_notice: str
    matched_specialties: list[str] = Field(default_factory=list)

