from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ClinicORM(Base):
    __tablename__ = "clinics"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    care_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    zip_code: Mapped[str] = mapped_column("zip", String(20), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    languages: Mapped[list[str]] = mapped_column(JSON, default=list)
    open_weekends: Mapped[bool] = mapped_column(Boolean, default=False)
    urgent_care: Mapped[bool] = mapped_column(Boolean, default=False)
    phone: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="mock_data")
    source_record_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    doctors: Mapped[list["DoctorORM"]] = relationship(back_populates="clinic")


class DoctorORM(Base):
    __tablename__ = "doctors"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialty: Mapped[str] = mapped_column(String(120), nullable=False)
    care_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    clinic_id: Mapped[str] = mapped_column(ForeignKey("clinics.id"), nullable=False, index=True)
    years_experience: Mapped[int] = mapped_column(Integer, nullable=False)
    languages: Mapped[list[str]] = mapped_column(JSON, default=list)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False)
    accepted_insurance: Mapped[list[str]] = mapped_column(JSON, default=list)
    availability_days: Mapped[int] = mapped_column(Integer, nullable=False)
    telehealth: Mapped[bool] = mapped_column(Boolean, default=False)
    gender: Mapped[str] = mapped_column(String(32), nullable=False)
    profile_blurb: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="mock_data")
    source_record_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    clinic: Mapped[ClinicORM] = relationship(back_populates="doctors")
    availability_slots: Mapped[list["AvailabilitySlotORM"]] = relationship(
        back_populates="doctor", cascade="all, delete-orphan"
    )


class InsurancePlanORM(Base):
    __tablename__ = "insurance_plans"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_type: Mapped[str] = mapped_column(String(64), nullable=False)
    referral_required_for_specialists: Mapped[bool] = mapped_column(Boolean, default=False)
    primary_care_copay: Mapped[int] = mapped_column(Integer, nullable=False)
    specialist_copay: Mapped[int] = mapped_column(Integer, nullable=False)
    urgent_care_copay: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="mock_data")
    source_record_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AvailabilitySlotORM(Base):
    __tablename__ = "availability_slots"

    id: Mapped[str] = mapped_column(String(140), primary_key=True)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctors.id"), nullable=False, index=True)
    clinic_id: Mapped[str | None] = mapped_column(ForeignKey("clinics.id"), nullable=True, index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    appointment_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="external_scheduling")
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    doctor: Mapped[DoctorORM] = relationship(back_populates="availability_slots")
