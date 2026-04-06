from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_document_service
from app.schemas.document import DocumentExplainRequest, DocumentExplainResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/explain", response_model=DocumentExplainResponse)
def explain_document(
    request: DocumentExplainRequest,
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentExplainResponse:
    return document_service.explain(request)

