from __future__ import annotations

from app.models.chat_session import ChatSessionRecord


class ChatRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, ChatSessionRecord] = {}

    def get_or_create(self, session_id: str) -> ChatSessionRecord:
        session = self._sessions.get(session_id)
        if session is None:
            session = ChatSessionRecord(session_id=session_id)
            self._sessions[session_id] = session
        return session

