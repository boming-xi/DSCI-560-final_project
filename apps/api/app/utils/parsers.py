from __future__ import annotations

import re


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    lowered = value.lower().strip()
    return re.sub(r"\s+", " ", lowered)


def tokenize(value: str | None) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", normalize_text(value)) if token]


def sentence_split(value: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", value.strip())
    return [part.strip() for part in parts if part.strip()]

