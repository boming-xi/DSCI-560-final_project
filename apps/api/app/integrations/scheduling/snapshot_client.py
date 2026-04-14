from __future__ import annotations

import json
from pathlib import Path

from app.integrations.scheduling.base import SchedulingClient
from app.integrations.scheduling.schemas import SchedulingSnapshot


class SnapshotSchedulingClient(SchedulingClient):
    def __init__(self, snapshot_file: Path) -> None:
        self.snapshot_file = snapshot_file

    def fetch_snapshot(self) -> SchedulingSnapshot:
        payload = json.loads(self.snapshot_file.read_text())
        return SchedulingSnapshot.model_validate(payload)
