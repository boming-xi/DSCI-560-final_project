from __future__ import annotations

from typing import Protocol

from app.integrations.scheduling.schemas import SchedulingSnapshot


class SchedulingClient(Protocol):
    def fetch_snapshot(self) -> SchedulingSnapshot:
        ...
