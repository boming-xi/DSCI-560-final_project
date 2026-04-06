from __future__ import annotations

from collections import Counter
import logging
from typing import Protocol

from openai import OpenAI

from app.utils.parsers import tokenize

logger = logging.getLogger(__name__)

VOCAB = [
    "fever",
    "throat",
    "cough",
    "rash",
    "skin",
    "stomach",
    "nausea",
    "sinus",
    "ear",
    "pain",
    "urgent",
    "insurance",
    "doctor",
    "referral",
    "booking",
]


class EmbeddingClient(Protocol):
    provider_name: str

    def embed_text(self, text: str) -> list[float]:
        ...


class DemoEmbeddingClient:
    provider_name = "demo"

    def embed_text(self, text: str) -> list[float]:
        counts = Counter(tokenize(text))
        total = max(sum(counts.values()), 1)
        return [round(counts.get(token, 0) / total, 4) for token in VOCAB]


class OpenAIEmbeddingClient:
    provider_name = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def embed_text(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=text.strip() or " ",
            encoding_format="float",
        )
        return [float(value) for value in response.data[0].embedding]


class ResilientEmbeddingClient:
    def __init__(self, primary: EmbeddingClient, fallback: EmbeddingClient) -> None:
        self.primary = primary
        self.fallback = fallback
        self.provider_name = primary.provider_name

    def embed_text(self, text: str) -> list[float]:
        try:
            return self.primary.embed_text(text)
        except Exception as exc:
            logger.warning("OpenAI embedding failed, falling back to demo embedding: %s", exc)
            self.provider_name = self.fallback.provider_name
            return self.fallback.embed_text(text)
