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
class FHIRProviderDirectoryVerificationClient(ProviderDirectoryVerificationClient):
    base_url: str
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
        practitioner_bundle = self._get_bundle(
            "Practitioner",
            {"name": self._doctor_name_query(doctor.name), "_count": "10"},
        )
        practitioners = self._practitioner_candidates(practitioner_bundle, doctor.name)
        if not practitioners:
            role_bundle = self._get_bundle(
                "PractitionerRole",
                {
                    "practitioner.name": self._doctor_name_query(doctor.name),
                    "_include": "PractitionerRole:location",
                    "_include:iterate": "PractitionerRole:organization",
                    "_count": "20",
                },
            )
            return self._match_roles(
                role_bundle,
                doctor=doctor,
                clinic=clinic,
                network_url=plan_context.network_url,
            )

        for practitioner in practitioners:
            practitioner_id = practitioner.get("id")
            if not practitioner_id:
                continue
            role_bundle = self._get_bundle(
                "PractitionerRole",
                {
                    "practitioner": practitioner_id,
                    "_include": "PractitionerRole:location",
                    "_include:iterate": "PractitionerRole:organization",
                    "_count": "20",
                },
            )
            match = self._match_roles(
                role_bundle,
                doctor=doctor,
                clinic=clinic,
                network_url=plan_context.network_url,
            )
            if match is not None:
                return match
        return None

    def _get_bundle(self, resource: str, params: dict[str, str]) -> dict[str, Any]:
        headers = {"Accept": "application/fhir+json"}
        if self.api_key:
            if self.api_key_query_param:
                params = {**params, self.api_key_query_param: self.api_key}
            else:
                headers[self.api_key_header] = self.api_key
        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = client.get(f"{self.base_url.rstrip('/')}/{resource}", params=params, headers=headers)
            response.raise_for_status()
            return response.json()

    def _practitioner_candidates(
        self,
        bundle: dict[str, Any],
        doctor_name: str,
    ) -> list[dict[str, Any]]:
        doctor_tokens = set(tokenize(doctor_name))
        candidates: list[dict[str, Any]] = []
        for entry in bundle.get("entry", []):
            resource = entry.get("resource") or {}
            if resource.get("resourceType") != "Practitioner":
                continue
            names = resource.get("name") or []
            text_values = [
                normalize_text(name.get("text"))
                for name in names
                if name.get("text")
            ]
            if not text_values:
                text_values = [
                    normalize_text(
                        " ".join(
                            [*(name.get("given") or []), name.get("family") or ""]
                        ).strip()
                    )
                    for name in names
                ]
            if any(doctor_tokens.issubset(set(tokenize(value))) for value in text_values if value):
                candidates.append(resource)
        return candidates

    def _match_roles(
        self,
        bundle: dict[str, Any],
        *,
        doctor: DoctorRecord,
        clinic: ClinicRecord,
        network_url: str | None,
    ) -> OfficialDirectoryMatch | None:
        included = {
            f"{resource.get('resourceType')}/{resource.get('id')}": resource
            for resource in (
                entry.get("resource") or {}
                for entry in bundle.get("entry", [])
            )
            if resource.get("id") and resource.get("resourceType")
        }

        for entry in bundle.get("entry", []):
            resource = entry.get("resource") or {}
            if resource.get("resourceType") != "PractitionerRole":
                continue
            specialty_text = " ".join(
                coding.get("display", "")
                for specialty in resource.get("specialty", [])
                for coding in specialty.get("coding", [])
            ) or resource.get("specialty", [{}])[0].get("text", "")
            location_match = self._role_location_matches(resource, included, clinic)
            specialty_match = self._specialty_matches(specialty_text, doctor.specialty)
            if location_match and specialty_match:
                evidence = [
                    f"Matched practitioner role specialty: {specialty_text or doctor.specialty}",
                    f"Matched provider directory location to {clinic.city} {clinic.zip}",
                ]
                if resource.get("organization"):
                    evidence.append(
                        f"Organization reference: {resource['organization'].get('display') or resource['organization'].get('reference', '')}"
                    )
                return OfficialDirectoryMatch(
                    label="Real-time official directory match",
                    reason=(
                        f"Verified this doctor against the live {self.source_label} provider directory using name, specialty, and clinic location."
                    ),
                    evidence=evidence,
                    network_url=network_url,
                    source=f"official_provider_directory_api:{self.source_label}",
                )
        return None

    def _role_location_matches(
        self,
        role: dict[str, Any],
        included: dict[str, dict[str, Any]],
        clinic: ClinicRecord,
    ) -> bool:
        target_zip = normalize_text(clinic.zip)
        target_city = normalize_text(clinic.city)
        target_name_tokens = set(tokenize(clinic.name))

        for location in role.get("location", []):
            resource = included.get(location.get("reference", ""))
            display = normalize_text(location.get("display"))
            if display and target_name_tokens and target_name_tokens.intersection(tokenize(display)):
                return True
            if not resource:
                continue
            name = normalize_text(resource.get("name"))
            address = resource.get("address") or {}
            city = normalize_text(address.get("city"))
            postal_code = normalize_text(address.get("postalCode"))
            if postal_code and postal_code.startswith(target_zip):
                return True
            if city and city == target_city:
                return True
            if name and target_name_tokens and target_name_tokens.intersection(tokenize(name)):
                return True
        return False

    @staticmethod
    def _specialty_matches(directory_specialty: str, doctor_specialty: str) -> bool:
        directory_tokens = set(tokenize(directory_specialty))
        doctor_tokens = set(tokenize(doctor_specialty))
        if not directory_tokens or not doctor_tokens:
            return False
        return bool(directory_tokens.intersection(doctor_tokens))

    @staticmethod
    def _doctor_name_query(doctor_name: str) -> str:
        stripped = doctor_name.replace("Dr. ", "").replace("Dr ", "").strip()
        return stripped
