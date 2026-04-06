from __future__ import annotations

from app.models.user import User


class UserRepository:
    def get_demo_user(self) -> User:
        return User(
            id="demo-user",
            name="Demo Patient",
            email="demo@example.com",
        )

