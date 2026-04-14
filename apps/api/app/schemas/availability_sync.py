from __future__ import annotations

from pydantic import BaseModel


class AvailabilitySyncResponse(BaseModel):
    source: str
    mode: str
    slots_upserted: int
    reference_data_backend: str
