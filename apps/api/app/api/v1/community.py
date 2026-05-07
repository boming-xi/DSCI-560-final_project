from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_authenticated_user, get_community_service
from app.models.user import User
from app.schemas.community import (
    CommunityCreateRoomRequest,
    CommunityDiscoverRequest,
    CommunityJoinRequest,
    CommunityRoomCatalogResponse,
    CommunityMessageRequest,
    CommunityRoomResponse,
)
from app.services.community_service import CommunityService

router = APIRouter(prefix="/community", tags=["community"])


@router.post("/discover", response_model=CommunityRoomCatalogResponse)
def discover_rooms(
    request: CommunityDiscoverRequest,
    user: User = Depends(get_authenticated_user),
    community_service: CommunityService = Depends(get_community_service),
) -> CommunityRoomCatalogResponse:
    del user
    return community_service.discover_rooms(request)


@router.post("/rooms", response_model=CommunityRoomResponse)
def create_room(
    request: CommunityCreateRoomRequest,
    user: User = Depends(get_authenticated_user),
    community_service: CommunityService = Depends(get_community_service),
) -> CommunityRoomResponse:
    return community_service.create_room(user, request)


@router.post("/rooms/{room_id}/join", response_model=CommunityRoomResponse)
def join_room(
    room_id: str,
    request: CommunityJoinRequest,
    user: User = Depends(get_authenticated_user),
    community_service: CommunityService = Depends(get_community_service),
) -> CommunityRoomResponse:
    try:
        return community_service.join_room(user, room_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/rooms/{room_id}", response_model=CommunityRoomResponse)
def get_room(
    room_id: str,
    ui_language: str | None = None,
    user: User = Depends(get_authenticated_user),
    community_service: CommunityService = Depends(get_community_service),
) -> CommunityRoomResponse:
    try:
        return community_service.get_room(user, room_id, ui_language=ui_language)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/rooms/{room_id}/messages", response_model=CommunityRoomResponse)
def post_message(
    room_id: str,
    request: CommunityMessageRequest,
    user: User = Depends(get_authenticated_user),
    community_service: CommunityService = Depends(get_community_service),
) -> CommunityRoomResponse:
    try:
        return community_service.post_message(user, room_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
