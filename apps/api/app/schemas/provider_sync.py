from __future__ import annotations

from pydantic import BaseModel


class ProviderSyncResponse(BaseModel):
    source: str
    mode: str
    clinics_upserted: int
    doctors_upserted: int
    reference_data_backend: str
