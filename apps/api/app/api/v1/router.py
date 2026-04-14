from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import get_settings
from app.db.session import database_is_available
from app.api.v1 import auth, booking, chat, doctors, documents, insurance, providers, symptoms

router = APIRouter()

router.include_router(auth.router)
router.include_router(symptoms.router)
router.include_router(insurance.router)
router.include_router(doctors.router)
router.include_router(booking.router)
router.include_router(chat.router)
router.include_router(documents.router)
router.include_router(providers.router)


@router.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    settings = get_settings()
    backend = "postgres" if database_is_available(settings.postgres_url) else "json_fallback"
    return {"status": "ok", "reference_data_backend": backend}
