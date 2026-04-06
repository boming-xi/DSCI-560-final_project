from __future__ import annotations

from typing import Annotated

from fastapi import Header, HTTPException, status

DEMO_TOKEN = "demo-token"


def get_current_user(authorization: Annotated[str | None, Header()] = None) -> dict[str, str]:
    if authorization is None:
        return {"id": "guest-user", "role": "guest"}
    if authorization == f"Bearer {DEMO_TOKEN}":
        return {"id": "demo-user", "role": "demo"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid demo token.",
    )

