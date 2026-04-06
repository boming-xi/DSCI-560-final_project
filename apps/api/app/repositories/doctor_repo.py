from __future__ import annotations

import json
from functools import cached_property

from app.core.config import Settings
from app.models.doctor import ClinicRecord, DoctorRecord


class DoctorRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @cached_property
    def clinics(self) -> list[ClinicRecord]:
        data = json.loads((self.settings.mock_data_dir / "clinics.json").read_text())
        return [ClinicRecord.model_validate(item) for item in data]

    @cached_property
    def doctors(self) -> list[DoctorRecord]:
        data = json.loads((self.settings.mock_data_dir / "doctors.json").read_text())
        return [DoctorRecord.model_validate(item) for item in data]

    def list_doctors(self) -> list[DoctorRecord]:
        return self.doctors

    def list_clinics(self) -> list[ClinicRecord]:
        return self.clinics

    def get_doctor(self, doctor_id: str) -> DoctorRecord | None:
        return next((doctor for doctor in self.doctors if doctor.id == doctor_id), None)

    def get_clinic(self, clinic_id: str) -> ClinicRecord | None:
        return next((clinic for clinic in self.clinics if clinic.id == clinic_id), None)

