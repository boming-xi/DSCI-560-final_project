from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_triage_service
from app.schemas.symptom import SymptomTriageRequest, TriageRecommendation
from app.services.triage_service import TriageService

router = APIRouter(prefix="/symptoms", tags=["symptoms"])


@router.post("/triage", response_model=TriageRecommendation)
def triage_symptoms(
    request: SymptomTriageRequest,
    triage_service: TriageService = Depends(get_triage_service),
) -> TriageRecommendation:
    return triage_service.triage(request)

