from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_authenticated_user, get_provider_sync_service
from app.models.user import User
from app.schemas.provider_sync import ProviderSyncResponse
from app.services.provider_sync_service import ProviderSyncService

router = APIRouter(prefix="/providers", tags=["providers"])


@router.post("/sync", response_model=ProviderSyncResponse)
def sync_provider_directory(
    _: User = Depends(get_authenticated_user),
    provider_sync_service: ProviderSyncService = Depends(get_provider_sync_service),
) -> ProviderSyncResponse:
    try:
        result = provider_sync_service.sync()
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return ProviderSyncResponse(
        source=result.source,
        mode=result.mode,
        clinics_upserted=result.clinics_upserted,
        doctors_upserted=result.doctors_upserted,
        reference_data_backend=result.reference_data_backend,
    )
