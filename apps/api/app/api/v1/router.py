from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, booking, chat, doctors, documents, insurance, symptoms

router = APIRouter()

router.include_router(auth.router)
router.include_router(symptoms.router)
router.include_router(insurance.router)
router.include_router(doctors.router)
router.include_router(booking.router)
router.include_router(chat.router)
router.include_router(documents.router)


@router.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

