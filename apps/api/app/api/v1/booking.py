from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_authenticated_user, get_availability_sync_service, get_booking_service
from app.models.user import User
from app.schemas.availability_sync import AvailabilitySyncResponse
from app.schemas.booking import BookingConfirmation, BookingRequest, BookingSlotsResponse
from app.services.availability_sync_service import AvailabilitySyncService
from app.services.booking_service import BookingService

router = APIRouter(prefix="/booking", tags=["booking"])


@router.get("/slots/{doctor_id}", response_model=BookingSlotsResponse)
def get_slots(
    doctor_id: str,
    _current_user: User = Depends(get_authenticated_user),
    booking_service: BookingService = Depends(get_booking_service),
) -> BookingSlotsResponse:
    return booking_service.get_slots(doctor_id)


@router.post("/appointments", response_model=BookingConfirmation)
def create_booking(
    request: BookingRequest,
    _current_user: User = Depends(get_authenticated_user),
    booking_service: BookingService = Depends(get_booking_service),
) -> BookingConfirmation:
    return booking_service.create_booking(request)


@router.post("/sync-slots", response_model=AvailabilitySyncResponse)
def sync_booking_slots(
    _current_user: User = Depends(get_authenticated_user),
    availability_sync_service: AvailabilitySyncService = Depends(get_availability_sync_service),
) -> AvailabilitySyncResponse:
    try:
        result = availability_sync_service.sync()
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return AvailabilitySyncResponse(
        source=result.source,
        mode=result.mode,
        slots_upserted=result.slots_upserted,
        reference_data_backend=result.reference_data_backend,
    )
