from __future__ import annotations

from pydantic import BaseModel


class UploadedDocumentRecord(BaseModel):
    title: str
    document_type: str
    content: str

