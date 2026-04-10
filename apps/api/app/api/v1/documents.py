from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import get_authenticated_user, get_document_service
from app.models.user import User
from app.schemas.document import (
    DocumentExplainRequest,
    DocumentExplainResponse,
    DocumentExtractResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/extract", response_model=DocumentExtractResponse)
async def extract_document(
    file: UploadFile = File(...),
    document_type: str = Form("medical_report"),
    title: str | None = Form(None),
    current_user: User = Depends(get_authenticated_user),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentExtractResponse:
    return await document_service.extract_upload(
        current_user,
        file,
        document_type=document_type,
        title=title,
    )


@router.post("/explain", response_model=DocumentExplainResponse)
def explain_document(
    request: DocumentExplainRequest,
    current_user: User = Depends(get_authenticated_user),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentExplainResponse:
    return document_service.explain(current_user, request)
