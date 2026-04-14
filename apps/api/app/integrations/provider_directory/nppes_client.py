from __future__ import annotations

from typing import Any

import httpx

from app.integrations.provider_directory.base import ProviderDirectoryClient
from app.integrations.provider_directory.census_geocoder import CensusGeocoderClient
from app.integrations.provider_directory.schemas import (
    ProviderClinicPayload,
    ProviderDirectorySnapshot,
    ProviderDoctorPayload,
)


class NPPESProviderDirectoryClient(ProviderDirectoryClient):
    def __init__(
        self,
        base_url: str,
        geocoder: CensusGeocoderClient,
        timeout_seconds: float = 15.0,
        city: str | None = None,
        state: str | None = None,
        taxonomy_description: str | None = None,
        limit: int = 25,
        default_latitude: float = 34.0224,
        default_longitude: float = -118.2851,
    ) -> None:
        self.base_url = base_url
        self.geocoder = geocoder
        self.timeout_seconds = timeout_seconds
        self.city = city
        self.state = state
        self.taxonomy_description = taxonomy_description
        self.limit = limit
        self.default_latitude = default_latitude
        self.default_longitude = default_longitude

    def fetch_snapshot(self) -> ProviderDirectorySnapshot:
        params = {
            "version": "2.1",
            "limit": self.limit,
            "enumeration_type": "NPI-1",
        }
        if self.city:
            params["city"] = self.city
        if self.state:
            params["state"] = self.state
        if self.taxonomy_description:
            params["taxonomy_description"] = self.taxonomy_description

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(self.base_url, params=params)
            response.raise_for_status()
            payload = response.json()

        return self._transform_payload(payload)

    def _transform_payload(self, payload: dict[str, Any]) -> ProviderDirectorySnapshot:
        clinics: list[ProviderClinicPayload] = []
        doctors: list[ProviderDoctorPayload] = []

        for result in payload.get("results", []):
            doctor, clinic = self._transform_result(result)
            if doctor is None or clinic is None:
                continue
            clinics.append(clinic)
            doctors.append(doctor)

        return ProviderDirectorySnapshot(
            source="cms_nppes",
            clinics=clinics,
            doctors=doctors,
        )

    def _transform_result(
        self, result: dict[str, Any]
    ) -> tuple[ProviderDoctorPayload | None, ProviderClinicPayload | None]:
        npi = str(result.get("number") or "").strip()
        basic = result.get("basic") or {}
        if not npi:
            return None, None

        address = self._select_location_address(result.get("addresses") or [])
        if address is None:
            return None, None

        specialty = self._select_primary_taxonomy_description(result.get("taxonomies") or [])
        doctor_name = self._build_doctor_name(basic)
        if not doctor_name:
            return None, None

        clinic_external_id = f"npi-{npi}-location"
        location_name = (
            basic.get("organization_name")
            or address.get("location")
            or f"{specialty} Clinic"
        )
        full_address = self._format_address(address)
        try:
            coordinates = self.geocoder.geocode(full_address)
        except httpx.HTTPError:
            coordinates = None
        latitude, longitude = coordinates if coordinates else (
            self.default_latitude,
            self.default_longitude,
        )

        clinic = ProviderClinicPayload(
            external_id=clinic_external_id,
            name=str(location_name),
            care_types=self._care_types_for_specialty(specialty),
            address=full_address,
            city=str(address.get("city") or ""),
            state=str(address.get("state") or ""),
            zip=str(address.get("postal_code") or ""),
            latitude=latitude,
            longitude=longitude,
            languages=[],
            open_weekends=False,
            urgent_care="urgent care" in specialty.lower(),
            phone=str(address.get("telephone_number") or ""),
        )

        doctor = ProviderDoctorPayload(
            external_id=npi,
            name=doctor_name,
            specialty=specialty,
            care_types=self._care_types_for_specialty(specialty),
            clinic_external_id=clinic_external_id,
            years_experience=0,
            languages=[],
            rating=4.2,
            review_count=0,
            accepted_insurance=[],
            availability_days=3,
            telehealth=False,
            gender=self._normalize_gender(str(basic.get("gender") or "")),
            profile_blurb=f"Imported from CMS NPPES provider directory with specialty {specialty}.",
        )
        return doctor, clinic

    @staticmethod
    def _select_location_address(addresses: list[dict[str, Any]]) -> dict[str, Any] | None:
        for address in addresses:
            if str(address.get("address_purpose") or "").upper() == "LOCATION":
                return address
        return addresses[0] if addresses else None

    @staticmethod
    def _select_primary_taxonomy_description(taxonomies: list[dict[str, Any]]) -> str:
        for taxonomy in taxonomies:
            if taxonomy.get("primary"):
                return str(taxonomy.get("desc") or taxonomy.get("taxonomy_description") or "General Practice")
        if taxonomies:
            taxonomy = taxonomies[0]
            return str(taxonomy.get("desc") or taxonomy.get("taxonomy_description") or "General Practice")
        return "General Practice"

    @staticmethod
    def _build_doctor_name(basic: dict[str, Any]) -> str:
        first = str(basic.get("first_name") or "").strip()
        last = str(basic.get("last_name") or "").strip()
        credential = str(basic.get("credential") or "").strip()
        base_name = " ".join(part for part in [first, last] if part)
        if not base_name:
            return ""
        if not base_name.lower().startswith("dr."):
            base_name = f"Dr. {base_name}"
        if credential:
            return f"{base_name}, {credential}"
        return base_name

    @staticmethod
    def _format_address(address: dict[str, Any]) -> str:
        parts = [
            str(address.get("address_1") or "").strip(),
            str(address.get("address_2") or "").strip(),
            " ".join(
                part
                for part in [
                    str(address.get("city") or "").strip(),
                    str(address.get("state") or "").strip(),
                    str(address.get("postal_code") or "").strip(),
                ]
                if part
            ),
        ]
        return ", ".join(part for part in parts if part)

    @staticmethod
    def _normalize_gender(gender: str) -> str:
        normalized = gender.strip().lower()
        if normalized == "m":
            return "Male"
        if normalized == "f":
            return "Female"
        return "Not specified"

    @staticmethod
    def _care_types_for_specialty(specialty: str) -> list[str]:
        normalized = specialty.lower()
        if "family" in normalized or "primary" in normalized:
            return ["general_practitioner", "primary_care"]
        if "internal medicine" in normalized:
            return ["general_practitioner", "adult_primary_care"]
        if "urgent care" in normalized:
            return ["urgent_care", "same_day"]
        if "dermat" in normalized:
            return ["specialist", "dermatology"]
        if "otolaryng" in normalized or "ent" in normalized:
            return ["specialist", "ent"]
        return ["specialist", normalized.replace(" ", "_")]
