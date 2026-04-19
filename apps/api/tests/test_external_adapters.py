from __future__ import annotations

from app.integrations.provider_directory.nppes_client import NPPESProviderDirectoryClient
from app.integrations.scheduling.fhir_client import FHIRSchedulingClient


class StubGeocoder:
    def geocode(self, address: str) -> tuple[float, float] | None:
        assert "Los Angeles" in address
        return (34.05, -118.25)


def test_nppes_client_transforms_results_to_internal_snapshot() -> None:
    client = NPPESProviderDirectoryClient(
        base_url="https://npiregistry.cms.hhs.gov/api/",
        geocoder=StubGeocoder(),
    )
    payload = {
        "results": [
            {
                "number": "1234567890",
                "basic": {
                    "first_name": "Maria",
                    "last_name": "Lopez",
                    "credential": "MD",
                    "gender": "F",
                    "organization_name": "Sunset Family Health",
                },
                "taxonomies": [{"desc": "Family Medicine", "primary": True}],
                "addresses": [
                    {
                        "address_purpose": "LOCATION",
                        "address_1": "900 Sunset Blvd",
                        "city": "Los Angeles",
                        "state": "CA",
                        "postal_code": "90026",
                        "telephone_number": "(213) 555-0900",
                    }
                ],
            }
        ]
    }

    snapshot = client._transform_payload(payload)

    assert snapshot.source == "cms_nppes"
    assert snapshot.clinics[0].external_id == "npi-1234567890-location"
    assert snapshot.clinics[0].latitude == 34.05
    assert snapshot.doctors[0].external_id == "1234567890"
    assert snapshot.doctors[0].name == "Dr. Maria Lopez, MD"
    assert snapshot.doctors[0].specialty == "Family Medicine"


def test_fhir_scheduling_client_transforms_bundle_to_slots() -> None:
    client = FHIRSchedulingClient(base_url="http://hapi.fhir.org/baseR4/Slot")
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {
                "resource": {
                    "resourceType": "Slot",
                    "id": "slot-1",
                    "schedule": {"reference": "Schedule/schedule-1"},
                    "status": "free",
                    "start": "2026-04-20T09:00:00-07:00",
                    "end": "2026-04-20T09:30:00-07:00",
                    "comment": "Bring insurance card",
                    "appointmentType": {"text": "In person"},
                }
            },
            {
                "resource": {
                    "resourceType": "Schedule",
                    "id": "schedule-1",
                    "actor": [
                        {"reference": "Practitioner/practitioner-1"},
                        {"reference": "Location/location-1"},
                    ],
                }
            },
            {
                "resource": {
                    "resourceType": "Practitioner",
                    "id": "practitioner-1",
                    "name": [
                        {
                            "given": ["Maria"],
                            "family": "Lopez",
                        }
                    ],
                    "identifier": [
                        {
                            "system": "http://hl7.org/fhir/sid/us-npi",
                            "value": "1234567890",
                        }
                    ],
                }
            },
            {
                "resource": {
                    "resourceType": "Location",
                    "id": "location-1",
                }
            },
        ],
    }

    snapshot = client._transform_bundle(bundle)

    assert snapshot.source == "fhir_scheduling"
    assert len(snapshot.slots) == 1
    assert snapshot.slots[0].doctor_external_id == "1234567890"
    assert snapshot.slots[0].doctor_name == "Dr. Maria Lopez"
    assert snapshot.slots[0].clinic_external_id == "location-1"
    assert snapshot.slots[0].appointment_mode == "In person"
