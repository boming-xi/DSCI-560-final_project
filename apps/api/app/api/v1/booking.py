from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_booking_service
from app.schemas.booking import BookingConfirmation, BookingRequest, BookingSlotsResponse
from app.services.booking_service import BookingService

router = APIRouter(prefix="/booking", tags=["booking"])


@router.get("/slots/{doctor_id}", response_model=BookingSlotsResponse)
def get_slots(
    doctor_id: str,
    booking_service: BookingService = Depends(get_booking_service),
) -> BookingSlotsResponse:
    return booking_service.get_slots(doctor_id)


@router.post("/appointments", response_model=BookingConfirmation)
def create_booking(
    request: BookingRequest,
    booking_service: BookingService = Depends(get_booking_service),
) -> BookingConfirmation:
    return booking_service.create_booking(request)

