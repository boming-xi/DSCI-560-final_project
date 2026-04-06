from __future__ import annotations

import logging
import re

from app.ai.llm_client import LLMClient
from app.utils.parsers import sentence_split

logger = logging.getLogger(__name__)

TERM_MAP = {
    "cbc": "A CBC is a common blood test that checks blood cells.",
    "wbc": "WBC refers to white blood cells, which can rise with infection or inflammation.",
    "hemoglobin": "Hemoglobin helps carry oxygen in your blood.",
    "cholesterol": "Cholesterol is a blood fat that can affect heart risk over time.",
    "inflammation": "Inflammation means the body may be reacting to irritation or illness.",
}


class MedicalExplainer:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client

    def explain(self, content: str, supporting_chunks: list[str] | None = None) -> tuple[str, list[str]]:
        sentences = sentence_split(content)
        summary = " ".join(sentences[:2]) if sentences else content
        if self.llm_client is not None:
            grounding = "\n".join(supporting_chunks or [])
            try:
                summary = self.llm_client.complete(
                    system_prompt=(
                        "You explain medical documents in plain language. "
                        "Do not diagnose, prescribe, or overstate certainty. "
                        "Keep the answer to 3 to 5 sentences and mention when a clinician should confirm it."
                    ),
                    user_prompt=(
                        f"Document text:\n{content[:5000]}\n\n"
                        f"Helpful context:\n{grounding[:1200]}\n\n"
                        "Explain what this likely means in patient-friendly language."
                    ),
                )
            except Exception as exc:
                logger.warning("OpenAI medical explanation failed, using deterministic summary: %s", exc)

        important_terms = [
            f"{term.upper()}: {description}"
            for term, description in TERM_MAP.items()
            if term in content.lower()
        ]
        if not important_terms:
            abbreviations = re.findall(r"\b[A-Z]{2,6}\b", content)
            important_terms = [f"{term}: Mentioned in the document and worth asking about." for term in abbreviations[:4]]
        return summary, important_terms[:4]
