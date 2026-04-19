from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_authenticated_user,
    get_doctor_decision_service,
    get_doctor_search_service,
)
from app.models.user import User
from app.schemas.doctor import DoctorProfile, DoctorSearchRequest, DoctorSearchResponse
from app.schemas.doctor_decision import DoctorDecisionRequest, DoctorDecisionResponse
from app.services.doctor_decision_service import DoctorDecisionService
from app.services.doctor_search_service import DoctorSearchService

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.post("/search", response_model=DoctorSearchResponse)
def search_doctors(
    request: DoctorSearchRequest,
    doctor_search_service: DoctorSearchService = Depends(get_doctor_search_service),
) -> DoctorSearchResponse:
    return doctor_search_service.search(request)


@router.get("/{doctor_id}", response_model=DoctorProfile)
def get_doctor(
    doctor_id: str,
    doctor_search_service: DoctorSearchService = Depends(get_doctor_search_service),
) -> DoctorProfile:
    return doctor_search_service.get_doctor(doctor_id)


@router.post("/advisor/message", response_model=DoctorDecisionResponse)
def doctor_decision_message(
    request: DoctorDecisionRequest,
    _current_user: User = Depends(get_authenticated_user),
    doctor_decision_service: DoctorDecisionService = Depends(get_doctor_decision_service),
) -> DoctorDecisionResponse:
    return doctor_decision_service.reply(request)
