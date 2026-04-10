from __future__ import annotations

import base64
from dataclasses import dataclass
import logging
from typing import Protocol, Sequence

from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class OCRImageInput:
    mime_type: str
    content: bytes
    label: str


class OCRClient(Protocol):
    provider_name: str

    def extract_text_from_images(
        self,
        images: Sequence[OCRImageInput],
        *,
        prompt: str,
    ) -> str:
        ...


class DemoOCRClient:
    provider_name = "unavailable"

    def extract_text_from_images(
        self,
        images: Sequence[OCRImageInput],
        *,
        prompt: str,
    ) -> str:
        raise RuntimeError(
            "Image OCR is not configured in this environment. Add an OpenAI API key to enable image and scanned PDF extraction."
        )


class OpenAIOCRClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        max_output_tokens: int = 2500,
    ) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.provider_name = f"openai-{model}"

    def extract_text_from_images(
        self,
        images: Sequence[OCRImageInput],
        *,
        prompt: str,
    ) -> str:
        if not images:
            return ""

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt,
                        },
                        *[
                            {
                                "type": "input_image",
                                "image_url": (
                                    f"data:{image.mime_type};base64,"
                                    f"{base64.b64encode(image.content).decode('utf-8')}"
                                ),
                                "detail": "high",
                            }
                            for image in images
                        ],
                    ],
                }
            ],
            max_output_tokens=self.max_output_tokens,
        )
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        for item in getattr(response, "output", []) or []:
            for content_part in getattr(item, "content", []) or []:
                text = getattr(content_part, "text", None)
                if isinstance(text, str) and text.strip():
                    return text.strip()

        raise RuntimeError("OpenAI OCR response did not contain text output.")


class ResilientOCRClient:
    def __init__(self, primary: OCRClient, fallback: OCRClient) -> None:
        self.primary = primary
        self.fallback = fallback
        self.provider_name = primary.provider_name
        self._fallback_active = False

    def extract_text_from_images(
        self,
        images: Sequence[OCRImageInput],
        *,
        prompt: str,
    ) -> str:
        if self._fallback_active:
            self.provider_name = self.fallback.provider_name
            return self.fallback.extract_text_from_images(images, prompt=prompt)

        try:
            text = self.primary.extract_text_from_images(images, prompt=prompt)
            self.provider_name = self.primary.provider_name
            return text
        except Exception as exc:
            logger.warning("OCR failed, falling back: %s", exc)
            self._fallback_active = True
            self.provider_name = self.fallback.provider_name
            try:
                return self.fallback.extract_text_from_images(images, prompt=prompt)
            except Exception as fallback_exc:
                raise RuntimeError(
                    "Image OCR is currently unavailable. Please try again later or upload a text-based PDF or text file."
                ) from fallback_exc
