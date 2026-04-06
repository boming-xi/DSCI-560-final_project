from __future__ import annotations

from pydantic import BaseModel


class User(BaseModel):
    id: str
    name: str
    email: str
    role: str = "demo"
