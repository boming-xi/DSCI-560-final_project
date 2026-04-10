from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from app.core.config import Settings
from app.models.user import StoredUserRecord, User


def _normalize_email(email: str) -> str:
    return re.sub(r"\s+", "", email).lower().strip()


class UserRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.storage_path = settings.demo_users_file
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.write_text("[]")

    def get_demo_user(self) -> User:
        return User(
            id="demo-user",
            name="Demo Patient",
            email="demo@example.com",
        )

    def get_by_email(self, email: str) -> StoredUserRecord | None:
        normalized_email = _normalize_email(email)
        return next(
            (
                user
                for user in self._load_users()
                if _normalize_email(user.email) == normalized_email
            ),
            None,
        )

    def get_by_id(self, user_id: str) -> StoredUserRecord | None:
        return next((user for user in self._load_users() if user.id == user_id), None)

    def create_user(
        self,
        name: str,
        email: str,
        password_hash: str,
        password_salt: str,
    ) -> User:
        users = self._load_users()
        user_record = StoredUserRecord(
            id=f"user-{uuid.uuid4().hex[:10]}",
            name=name.strip(),
            email=_normalize_email(email),
            role="demo",
            password_hash=password_hash,
            password_salt=password_salt,
        )
        users.append(user_record)
        self._save_users(users)
        return self.to_public_user(user_record)

    def to_public_user(self, user_record: StoredUserRecord) -> User:
        return User(
            id=user_record.id,
            name=user_record.name,
            email=user_record.email,
            role=user_record.role,
        )

    def _load_users(self) -> list[StoredUserRecord]:
        data = json.loads(self.storage_path.read_text() or "[]")
        return [StoredUserRecord.model_validate(item) for item in data]

    def _save_users(self, users: list[StoredUserRecord]) -> None:
        payload = [user.model_dump() for user in users]
        self.storage_path.write_text(json.dumps(payload, indent=2))
