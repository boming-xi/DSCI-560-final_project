from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_authenticated_user,
    get_insurance_advisor_service,
    get_insurance_service,
)
from app.models.user import User
from app.schemas.insurance import InsuranceParseRequest, InsuranceSummary
from app.schemas.insurance_advisor import (
    InsuranceAdvisorMessageRequest,
    InsuranceAdvisorMessageResponse,
)
from app.services.insurance_advisor_service import InsuranceAdvisorService
from app.services.insurance_service import InsuranceService

router = APIRouter(prefix="/insurance", tags=["insurance"])


@router.post("/parse", response_model=InsuranceSummary)
def parse_insurance(
    request: InsuranceParseRequest,
    insurance_service: InsuranceService = Depends(get_insurance_service),
) -> InsuranceSummary:
    return insurance_service.parse_insurance(request)


@router.post("/advisor/message", response_model=InsuranceAdvisorMessageResponse)
def insurance_advisor_message(
    request: InsuranceAdvisorMessageRequest,
    _: User = Depends(get_authenticated_user),
    insurance_advisor_service: InsuranceAdvisorService = Depends(get_insurance_advisor_service),
) -> InsuranceAdvisorMessageResponse:
    return insurance_advisor_service.reply(request)
