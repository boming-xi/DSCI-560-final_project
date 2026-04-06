from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_insurance_service
from app.schemas.insurance import InsuranceParseRequest, InsuranceSummary
from app.services.insurance_service import InsuranceService

router = APIRouter(prefix="/insurance", tags=["insurance"])


@router.post("/parse", response_model=InsuranceSummary)
def parse_insurance(
    request: InsuranceParseRequest,
    insurance_service: InsuranceService = Depends(get_insurance_service),
) -> InsuranceSummary:
    return insurance_service.parse_insurance(request)

