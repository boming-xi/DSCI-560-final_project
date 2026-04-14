from __future__ import annotations

import httpx

from app.integrations.scheduling.base import SchedulingClient
from app.integrations.scheduling.schemas import SchedulingSnapshot


class HTTPSchedulingClient(SchedulingClient):
    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        api_key_header: str = "Authorization",
        timeout_seconds: float = 15.0,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.api_key_header = api_key_header
        self.timeout_seconds = timeout_seconds

    def fetch_snapshot(self) -> SchedulingSnapshot:
        headers: dict[str, str] = {}
        if self.api_key:
            if self.api_key_header.lower() == "authorization" and not self.api_key.startswith("Bearer "):
                headers[self.api_key_header] = f"Bearer {self.api_key}"
            else:
                headers[self.api_key_header] = self.api_key

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(self.base_url, headers=headers)
            response.raise_for_status()
            payload = response.json()

        return SchedulingSnapshot.model_validate(payload)
