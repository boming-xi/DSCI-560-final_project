from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header

from app.api.deps import get_auth_service
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/demo-login", response_model=AuthResponse)
def demo_login(auth_service: AuthService = Depends(get_auth_service)) -> AuthResponse:
    return auth_service.demo_login()


@router.post("/register", response_model=AuthResponse)
def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    return auth_service.register(request)


@router.post("/login", response_model=AuthResponse)
def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    return auth_service.login(request)


@router.get("/me", response_model=User)
def me(
    authorization: Annotated[str | None, Header()] = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    token = authorization.removeprefix("Bearer ").strip() if authorization else None
    return auth_service.get_current_user(token)
