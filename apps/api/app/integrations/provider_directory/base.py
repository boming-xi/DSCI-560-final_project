from __future__ import annotations

from typing import Protocol

from app.integrations.provider_directory.schemas import ProviderDirectorySnapshot


class ProviderDirectoryClient(Protocol):
    def fetch_snapshot(self) -> ProviderDirectorySnapshot:
        ...
