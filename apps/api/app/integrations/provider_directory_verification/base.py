from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.models.doctor import ClinicRecord, DoctorRecord


@dataclass(slots=True)
class OfficialDirectoryMatch:
    label: str
    reason: str
    evidence: list[str]
    network_url: str | None
    source: str


class ProviderDirectoryVerificationClient(Protocol):
    def verify(
        self,
        *,
        plan_context: Any,
        doctor: DoctorRecord,
        clinic: ClinicRecord,
    ) -> OfficialDirectoryMatch | None: ...
