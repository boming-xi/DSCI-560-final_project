from __future__ import annotations

from app.models.appointment import AppointmentRecord


class BookingRepository:
    def __init__(self) -> None:
        self._appointments: list[AppointmentRecord] = []

    def create(self, appointment: AppointmentRecord) -> AppointmentRecord:
        self._appointments.append(appointment)
        return appointment

    def list_all(self) -> list[AppointmentRecord]:
        return list(self._appointments)

