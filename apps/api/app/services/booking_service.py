from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status

from app.models.appointment import AppointmentRecord
from app.repositories.availability_repo import AvailabilityRepository
from app.repositories.booking_repo import BookingRepository
from app.repositories.doctor_repo import DoctorRepository
from app.schemas.booking import BookingConfirmation, BookingRequest, BookingSlotsResponse, TimeSlot


class BookingService:
    def __init__(
        self,
        doctor_repo: DoctorRepository,
        booking_repo: BookingRepository,
        availability_repo: AvailabilityRepository,
    ) -> None:
        self.doctor_repo = doctor_repo
        self.booking_repo = booking_repo
        self.availability_repo = availability_repo

    def get_slots(self, doctor_id: str) -> BookingSlotsResponse:
        doctor = self.doctor_repo.get_doctor(doctor_id)
        if doctor is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")

        if doctor.official_booking_url:
            return BookingSlotsResponse(
                doctor_id=doctor_id,
                doctor_name=doctor.name,
                slots=[],
                source="official_external_link",
                external_booking_url=doctor.official_booking_url,
                external_booking_label=doctor.official_booking_label,
                booking_system_name=doctor.booking_system_name,
                official_profile_url=doctor.official_profile_url,
            )

        synced_slots = [
            slot
            for slot in self.availability_repo.list_current_slots_for_doctor(doctor_id)
            if not self.booking_repo.is_slot_booked(doctor_id, slot.start.isoformat())
        ]
        if synced_slots:
            return BookingSlotsResponse(
                doctor_id=doctor_id,
                doctor_name=doctor.name,
                source="external_sync",
                slots=[
                    TimeSlot(
                        start=slot.start.isoformat(),
                        end=slot.end.isoformat(),
                        label=slot.label,
                        available=slot.available,
                        appointment_mode=slot.appointment_mode,
                        source=slot.source,
                        comments=slot.comments,
                    )
                    for slot in synced_slots
                ],
            )
        if self.availability_repo.has_recent_sync_for_doctor(doctor_id):
            return BookingSlotsResponse(
                doctor_id=doctor_id,
                doctor_name=doctor.name,
                slots=[],
                source="external_sync",
            )

        start_day = datetime.now(UTC) + timedelta(days=doctor.availability_days)
        slots: list[TimeSlot] = []
        for offset in range(5):
            start = start_day + timedelta(days=offset)
            start = start.replace(hour=17 if offset % 2 else 9, minute=0, second=0, microsecond=0)
            end = start + timedelta(minutes=30)
            if self.booking_repo.is_slot_booked(doctor_id, start.isoformat()):
                continue
            slots.append(
                TimeSlot(
                    start=start.isoformat(),
                    end=end.isoformat(),
                    label=start.strftime("%a %b %d, %I:%M %p"),
                    source="demo_fallback",
                )
            )

        return BookingSlotsResponse(
            doctor_id=doctor_id,
            doctor_name=doctor.name,
            slots=slots,
            source="demo_fallback",
        )

    def create_booking(self, request: BookingRequest) -> BookingConfirmation:
        doctor = self.doctor_repo.get_doctor(request.doctor_id)
        if doctor is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
        clinic = self.doctor_repo.get_clinic(doctor.clinic_id)
        if clinic is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found.")
        if self.booking_repo.is_slot_booked(request.doctor_id, request.preferred_slot):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="That slot has already been booked.")

        available_slots = self.get_slots(request.doctor_id).slots
        if request.preferred_slot not in {slot.start for slot in available_slots if slot.available}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected slot is no longer available. Please refresh and choose another time.",
            )

        appointment = AppointmentRecord(
            confirmation_id=f"APT-{uuid4().hex[:8].upper()}",
            doctor_id=doctor.id,
            patient_name=request.patient_name,
            email=request.email,
            slot=request.preferred_slot,
            notes=request.notes,
        )
        saved = self.booking_repo.create(appointment)

        return BookingConfirmation(
            confirmation_id=saved.confirmation_id,
            doctor_id=doctor.id,
            doctor_name=doctor.name,
            clinic_name=clinic.name,
            slot=request.preferred_slot,
            estimated_cost=None,
            next_steps=[
                "Bring your ID and insurance card.",
                "Arrive 10 minutes early to complete intake forms.",
                "If symptoms worsen before the appointment, seek more urgent care.",
            ],
        )
