from __future__ import annotations

from fastapi import HTTPException, status

from app.core.security import (
    DEMO_TOKEN,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest


class AuthService:
    def __init__(self, user_repo: UserRepository, auth_secret: str) -> None:
        self.user_repo = user_repo
        self.auth_secret = auth_secret

    def demo_login(self) -> AuthResponse:
        user = self.user_repo.get_demo_user()
        return AuthResponse(access_token=DEMO_TOKEN, user=user)

    def register(self, request: RegisterRequest) -> AuthResponse:
        if self.user_repo.get_by_email(request.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with that email already exists.",
            )
        password_hash, password_salt = hash_password(request.password)
        user = self.user_repo.create_user(
            name=request.name,
            email=request.email,
            password_hash=password_hash,
            password_salt=password_salt,
        )
        return self._build_auth_response(user)

    def login(self, request: LoginRequest) -> AuthResponse:
        stored_user = self.user_repo.get_by_email(request.email)
        if stored_user is None or not verify_password(
            request.password,
            password_hash=stored_user.password_hash,
            password_salt=stored_user.password_salt,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
            )
        return self._build_auth_response(self.user_repo.to_public_user(stored_user))

    def get_current_user(self, token: str | None) -> User:
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
            )
        if token == DEMO_TOKEN:
            return self.user_repo.get_demo_user()
        payload = decode_access_token(token, secret=self.auth_secret)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token.",
            )
        user = self.user_repo.get_by_id(payload.get("user_id", ""))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found for this token.",
            )
        return self.user_repo.to_public_user(user)

    def _build_auth_response(self, user: User) -> AuthResponse:
        token = create_access_token(
            {
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
            },
            secret=self.auth_secret,
        )
        return AuthResponse(access_token=token, user=user)
