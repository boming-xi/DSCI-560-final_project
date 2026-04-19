from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.integrations.provider_directory_verification.base import (
    OfficialDirectoryMatch,
    ProviderDirectoryVerificationClient,
)
from app.models.doctor import ClinicRecord, DoctorRecord
from app.utils.parsers import normalize_text, tokenize


@dataclass(slots=True)
class JSONProviderDirectoryVerificationClient(ProviderDirectoryVerificationClient):
    url: str
    source_label: str
    timeout_seconds: float = 8.0
    api_key: str | None = None
    api_key_header: str = "Authorization"
    api_key_query_param: str | None = None

    def verify(
        self,
        *,
        plan_context: Any,
        doctor: DoctorRecord,
        clinic: ClinicRecord,
    ) -> OfficialDirectoryMatch | None:
        headers = {"Accept": "application/json"}
        params: dict[str, str] = {}
        if self.api_key:
            if self.api_key_query_param:
                params[self.api_key_query_param] = self.api_key
            else:
                headers[self.api_key_header] = self.api_key
        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = client.get(self.url, headers=headers, params=params)
            response.raise_for_status()
            payload = response.json()

        for record in self._iter_records(payload):
            if not self._name_matches(record, doctor.name):
                continue
            if not self._location_matches(record, clinic):
                continue
            if not self._specialty_matches(record, doctor.specialty):
                continue
            return OfficialDirectoryMatch(
                label="Real-time official directory match",
                reason=(
                    f"Verified this doctor against the live {self.source_label} provider directory feed."
                ),
                evidence=[
                    f"Matched provider name: {self._record_name(record)}",
                    f"Matched provider location to {clinic.city} {clinic.zip}",
                    f"Matched specialty to {doctor.specialty}",
                ],
                network_url=plan_context.network_url,
                source=f"official_provider_directory_api:{self.source_label}",
            )
        return None

    def _iter_records(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []
        for key in ["providers", "results", "items", "data", "entries"]:
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [payload]

    def _record_name(self, record: dict[str, Any]) -> str:
        for key in ["name", "providerName", "displayName", "fullName"]:
            value = record.get(key)
            if isinstance(value, str) and value.strip():
                return value
        if isinstance(record.get("provider"), dict):
            nested = record["provider"]
            for key in ["name", "displayName", "fullName"]:
                value = nested.get(key)
                if isinstance(value, str) and value.strip():
                    return value
        first = record.get("firstName") or record.get("first_name") or ""
        last = record.get("lastName") or record.get("last_name") or ""
        return " ".join(part for part in [str(first).strip(), str(last).strip()] if part)

    def _name_matches(self, record: dict[str, Any], doctor_name: str) -> bool:
        record_tokens = set(tokenize(self._record_name(record)))
        doctor_tokens = set(tokenize(doctor_name))
        return bool(record_tokens) and doctor_tokens.issubset(record_tokens)

    def _location_matches(self, record: dict[str, Any], clinic: ClinicRecord) -> bool:
        target_zip = normalize_text(clinic.zip)
        target_city = normalize_text(clinic.city)
        for address in self._addresses(record):
            city = normalize_text(address.get("city"))
            postal_code = normalize_text(address.get("zip") or address.get("postalCode"))
            if postal_code and postal_code.startswith(target_zip):
                return True
            if city and city == target_city:
                return True
        return False

    def _specialty_matches(self, record: dict[str, Any], doctor_specialty: str) -> bool:
        specialty_tokens = set(tokenize(doctor_specialty))
        for specialty in self._specialties(record):
            if specialty_tokens.intersection(tokenize(specialty)):
                return True
        return False

    def _addresses(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        for key in ["addresses", "locations"]:
            value = record.get(key)
            if isinstance(value, list):
                candidates.extend(item for item in value if isinstance(item, dict))
        if isinstance(record.get("address"), dict):
            candidates.append(record["address"])
        if isinstance(record.get("location"), dict):
            candidates.append(record["location"])
        return candidates

    def _specialties(self, record: dict[str, Any]) -> list[str]:
        collected: list[str] = []
        for key in ["specialty", "specialties"]:
            value = record.get(key)
            if isinstance(value, str) and value.strip():
                collected.append(value)
            elif isinstance(value, list):
                collected.extend(item for item in value if isinstance(item, str))
        return collected
