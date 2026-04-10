from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class DocumentExplainRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    document_type: str = "medical_report"
    document_id: str | None = None
    focus_question: str = "What matters most?"

    @model_validator(mode="after")
    def validate_source(self) -> DocumentExplainRequest:
        if not self.content and not self.document_id:
            raise ValueError("Either content or document_id must be provided.")
        return self


class DocumentExplainResponse(BaseModel):
    document_id: str
    indexed_now: bool = False
    vector_store_backend: str
    supporting_chunks: list[str] = Field(default_factory=list)
    summary: str
    important_terms: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    disclaimer: str


class DocumentExtractResponse(BaseModel):
    title: str
    document_type: str
    source_file_name: str
    source_mime_type: str
    extraction_method: str
    extracted_text: str
    extracted_preview: str
    warnings: list[str] = Field(default_factory=list)
