from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_authenticated_user, get_document_service
from app.models.user import User
from app.schemas.document import DocumentExplainRequest, DocumentExplainResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/explain", response_model=DocumentExplainResponse)
def explain_document(
    request: DocumentExplainRequest,
    _current_user: User = Depends(get_authenticated_user),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentExplainResponse:
    return document_service.explain(request)
