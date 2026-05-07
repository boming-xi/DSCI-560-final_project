from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.core.config import Settings


class CommunityRepository:
    def __init__(self, settings: Settings) -> None:
        self.storage_path: Path = settings.community_rooms_file
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.write_text(json.dumps({"rooms": []}, indent=2))
        self._lock = threading.Lock()

    def load_rooms(self) -> list[dict[str, Any]]:
        payload = json.loads(self.storage_path.read_text() or '{"rooms": []}')
        rooms = payload.get("rooms", [])
        return rooms if isinstance(rooms, list) else []

    def save_rooms(self, rooms: list[dict[str, Any]]) -> None:
        with self._lock:
            self.storage_path.write_text(json.dumps({"rooms": rooms}, indent=2, ensure_ascii=False))

    def update_room(
        self,
        room_id: str,
        updater: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> dict[str, Any] | None:
        with self._lock:
            payload = json.loads(self.storage_path.read_text() or '{"rooms": []}')
            rooms = payload.get("rooms", [])
            updated_room: dict[str, Any] | None = None
            for index, room in enumerate(rooms):
                if room.get("id") == room_id:
                    next_room = updater(room)
                    next_room["updated_at"] = datetime.now(timezone.utc).isoformat()
                    rooms[index] = next_room
                    updated_room = next_room
                    break
            self.storage_path.write_text(
                json.dumps({"rooms": rooms}, indent=2, ensure_ascii=False)
            )
            return updated_room

    def upsert_room(self, room: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            payload = json.loads(self.storage_path.read_text() or '{"rooms": []}')
            rooms = payload.get("rooms", [])
            for index, existing in enumerate(rooms):
                if existing.get("id") == room.get("id"):
                    rooms[index] = room
                    self.storage_path.write_text(
                        json.dumps({"rooms": rooms}, indent=2, ensure_ascii=False)
                    )
                    return room
            rooms.append(room)
            self.storage_path.write_text(
                json.dumps({"rooms": rooms}, indent=2, ensure_ascii=False)
            )
            return room
