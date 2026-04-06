from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_user_repo
from app.core.security import DEMO_TOKEN
from app.repositories.user_repo import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/demo-login")
def demo_login(user_repo: UserRepository = Depends(get_user_repo)) -> dict[str, object]:
    user = user_repo.get_demo_user()
    return {
        "access_token": DEMO_TOKEN,
        "token_type": "bearer",
        "user": user.model_dump(),
    }

