from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ProviderClinicPayload(BaseModel):
    id: str | None = None
    external_id: str | None = None
    name: str
    care_types: list[str] = Field(default_factory=list)
    address: str
    city: str
    state: str
    zip: str
    latitude: float
    longitude: float
    languages: list[str] = Field(default_factory=list)
    open_weekends: bool = False
    urgent_care: bool = False
    phone: str = ""


class ProviderDoctorPayload(BaseModel):
    id: str | None = None
    external_id: str | None = None
    name: str
    specialty: str
    care_types: list[str] = Field(default_factory=list)
    clinic_id: str | None = None
    clinic_external_id: str | None = None
    years_experience: int = 0
    languages: list[str] = Field(default_factory=list)
    rating: float = 0.0
    review_count: int = 0
    accepted_insurance: list[str] = Field(default_factory=list)
    availability_days: int = 7
    telehealth: bool = False
    gender: str = "Not specified"
    profile_blurb: str = ""

    @model_validator(mode="after")
    def validate_clinic_reference(self) -> "ProviderDoctorPayload":
        if not self.clinic_id and not self.clinic_external_id:
            raise ValueError("Provider doctors must include clinic_id or clinic_external_id.")
        return self


class ProviderDirectorySnapshot(BaseModel):
    source: str = "external_provider_directory"
    clinics: list[ProviderClinicPayload] = Field(default_factory=list)
    doctors: list[ProviderDoctorPayload] = Field(default_factory=list)
