from __future__ import annotations

from typing import Any

import httpx

from app.integrations.scheduling.base import SchedulingClient
from app.integrations.scheduling.schemas import AvailabilitySlotPayload, SchedulingSnapshot


class FHIRSchedulingClient(SchedulingClient):
    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        api_key_header: str = "Authorization",
        timeout_seconds: float = 15.0,
        count: int = 50,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.api_key_header = api_key_header
        self.timeout_seconds = timeout_seconds
        self.count = count

    def fetch_snapshot(self) -> SchedulingSnapshot:
        headers: dict[str, str] = {"Accept": "application/fhir+json"}
        if self.api_key:
            if self.api_key_header.lower() == "authorization" and not self.api_key.startswith("Bearer "):
                headers[self.api_key_header] = f"Bearer {self.api_key}"
            else:
                headers[self.api_key_header] = self.api_key

        params = {
            "status": "free",
            "_count": self.count,
            "_include": "Slot:schedule",
            "_include:iterate": "Schedule:actor",
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            payload = response.json()

        return self._transform_bundle(payload)

    def _transform_bundle(self, payload: dict[str, Any]) -> SchedulingSnapshot:
        entries = payload.get("entry", [])
        resources = [entry.get("resource") or {} for entry in entries]
        by_ref = {
            f"{resource.get('resourceType')}/{resource.get('id')}": resource
            for resource in resources
            if resource.get("resourceType") and resource.get("id")
        }

        slots: list[AvailabilitySlotPayload] = []
        for resource in resources:
            if resource.get("resourceType") != "Slot":
                continue
            slot_payload = self._transform_slot(resource, by_ref)
            if slot_payload is not None:
                slots.append(slot_payload)

        return SchedulingSnapshot(source="fhir_scheduling", slots=slots)

    def _transform_slot(
        self,
        slot: dict[str, Any],
        by_ref: dict[str, dict[str, Any]],
    ) -> AvailabilitySlotPayload | None:
        schedule_ref = (slot.get("schedule") or {}).get("reference")
        schedule = by_ref.get(schedule_ref) if schedule_ref else None
        practitioner = self._resolve_practitioner(schedule, by_ref)
        if practitioner is None:
            return None

        doctor_external_id = self._extract_npi(practitioner) or practitioner.get("id")
        clinic_external_id = self._resolve_location_id(schedule, by_ref)
        if not doctor_external_id:
            return None

        appointment_mode = None
        appointment_type = slot.get("appointmentType") or {}
        if appointment_type.get("text"):
            appointment_mode = str(appointment_type["text"])
        elif appointment_type.get("coding"):
            appointment_mode = str(appointment_type["coding"][0].get("display") or "")

        comments = slot.get("comment")
        start = slot.get("start")
        end = slot.get("end")
        if not start or not end:
            return None

        return AvailabilitySlotPayload(
            external_id=str(slot.get("id") or ""),
            doctor_external_id=str(doctor_external_id),
            clinic_external_id=str(clinic_external_id) if clinic_external_id else None,
            start=str(start),
            end=str(end),
            label=str(start),
            available=str(slot.get("status") or "").lower() == "free",
            appointment_mode=appointment_mode or None,
            comments=str(comments) if comments else None,
        )

    @staticmethod
    def _resolve_practitioner(
        schedule: dict[str, Any] | None,
        by_ref: dict[str, dict[str, Any]],
    ) -> dict[str, Any] | None:
        if schedule is None:
            return None
        for actor in schedule.get("actor") or []:
            reference = actor.get("reference")
            resource = by_ref.get(reference)
            if resource and resource.get("resourceType") == "Practitioner":
                return resource
        return None

    @staticmethod
    def _resolve_location_id(schedule: dict[str, Any] | None, by_ref: dict[str, dict[str, Any]]) -> str | None:
        if schedule is None:
            return None
        for actor in schedule.get("actor") or []:
            reference = actor.get("reference")
            resource = by_ref.get(reference)
            if resource and resource.get("resourceType") == "Location":
                return resource.get("id")
        return None

    @staticmethod
    def _extract_npi(practitioner: dict[str, Any]) -> str | None:
        for identifier in practitioner.get("identifier") or []:
            system = str(identifier.get("system") or "").lower()
            value = identifier.get("value")
            if not value:
                continue
            if "npi" in system or "2.16.840.1.113883.4.6" in system:
                return str(value)
            type_block = identifier.get("type") or {}
            for coding in type_block.get("coding") or []:
                code = str(coding.get("code") or "").upper()
                if code == "NPI":
                    return str(value)
        return None
