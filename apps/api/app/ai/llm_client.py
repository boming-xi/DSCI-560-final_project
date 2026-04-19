from __future__ import annotations

import logging
import re
from typing import Protocol

from openai import OpenAI

from app.utils.parsers import sentence_split

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    provider_name: str

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        ...


class DemoLLMClient:
    provider_name = "demo"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        if "Insurance advisor profile:" in user_prompt:
            missing_match = re.search(r"Missing fields:\s*(.+)\n", user_prompt)
            shortlist_match = re.search(r"Current shortlist:\s*(.+)", user_prompt)
            current_message_match = re.search(r"Current user message:\s*(.+?)\nCurrent shortlist:", user_prompt, re.DOTALL)
            missing_fields = missing_match.group(1).strip() if missing_match else "[]"
            shortlist = shortlist_match.group(1).strip() if shortlist_match else "none yet"
            current_message = (
                current_message_match.group(1).strip()
                if current_message_match
                else "the user wants help choosing insurance"
            )
            if "none" not in shortlist and shortlist != "none yet":
                return (
                    f"Thanks, that helps. I already have a preliminary shortlist: {shortlist}. "
                    "Tell me whether lower monthly cost or easier specialist access matters more so I can tighten the ranking."
                )
            return (
                f"Thanks, that gives me a better starting point. I still want to clarify {missing_fields}. "
                f"You just mentioned: {current_message}"
            )

        current_message_match = re.search(r"Current user message:\s*(.+)$", user_prompt, re.DOTALL)
        next_step_match = re.search(r"Suggested next step:\s*(.+)", user_prompt)
        if current_message_match:
            current_message = current_message_match.group(1).strip()
            next_step = (
                next_step_match.group(1).strip()
                if next_step_match
                else "Start with the recommended care path and escalate if symptoms worsen."
            )
            return (
                f"Based on what you shared, {next_step} "
                f"If symptoms get worse, new red flags appear, or you are worried about rapid changes, seek more urgent care. "
                f"You asked: {current_message}"
            )

        document_match = re.search(
            r"Document text:\n(.*?)\n\nHelpful context:",
            user_prompt,
            re.DOTALL,
        )
        if document_match:
            document_text = document_match.group(1).strip()
            sentences = sentence_split(document_text)
            summary = " ".join(sentences[:2]) if sentences else document_text
            return (
                f"{summary} This is only a plain-language summary and should be confirmed with a clinician."
            ).strip()

        return user_prompt.strip()


class OpenAILLMClient:
    provider_name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str,
        reasoning_effort: str = "low",
        max_output_tokens: int = 700,
    ) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.max_output_tokens = max_output_tokens

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        payload: dict[str, object] = {
            "model": self.model,
            "instructions": system_prompt,
            "input": user_prompt,
            "max_output_tokens": self.max_output_tokens,
        }
        if self._supports_reasoning():
            payload["reasoning"] = {"effort": self.reasoning_effort}

        response = self.client.responses.create(**payload)
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        for item in getattr(response, "output", []) or []:
            for content_part in getattr(item, "content", []) or []:
                text = getattr(content_part, "text", None)
                if isinstance(text, str) and text.strip():
                    return text.strip()

        raise RuntimeError("OpenAI response did not contain text output.")

    def _supports_reasoning(self) -> bool:
        return self.model.startswith(("gpt-5", "o1", "o3", "o4"))


class ResilientLLMClient:
    def __init__(self, primary: LLMClient, fallback: LLMClient) -> None:
        self.primary = primary
        self.fallback = fallback
        self.provider_name = primary.provider_name

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            return self.primary.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        except Exception as exc:
            logger.warning("OpenAI completion failed, falling back to demo response: %s", exc)
            self.provider_name = self.fallback.provider_name
            return self.fallback.complete(system_prompt=system_prompt, user_prompt=user_prompt)
