from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_doctor_search_service
from app.schemas.doctor import DoctorProfile, DoctorSearchRequest, DoctorSearchResponse
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

