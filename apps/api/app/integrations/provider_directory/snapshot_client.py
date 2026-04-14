from __future__ import annotations

import json
from pathlib import Path

from app.integrations.provider_directory.base import ProviderDirectoryClient
from app.integrations.provider_directory.schemas import ProviderDirectorySnapshot


class SnapshotProviderDirectoryClient(ProviderDirectoryClient):
    def __init__(self, snapshot_file: Path) -> None:
        self.snapshot_file = snapshot_file

    def fetch_snapshot(self) -> ProviderDirectorySnapshot:
        payload = json.loads(self.snapshot_file.read_text())
        return ProviderDirectorySnapshot.model_validate(payload)
