from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.models.user import User
from app.repositories.community_repo import CommunityRepository
from app.schemas.community import (
    CommunityCreateRoomRequest,
    CommunityDiscoverRequest,
    CommunityJoinRequest,
    CommunityMatchRequest,
    CommunityMessage,
    CommunityMessageRequest,
    CommunityRoomCatalogResponse,
    CommunityRoomResponse,
    CommunityRoomSummary,
)


@dataclass
class RoomMatch:
    room_id: str
    care_path: str
    urgency_band: str
    symptom_tags: list[str]
    language: str
    region: str


@dataclass(frozen=True)
class RoomTemplate:
    key: str
    care_path: str
    urgency_band: str
    symptom_tags: tuple[str, ...]


class CommunityService:
    def __init__(self, repo: CommunityRepository) -> None:
        self.repo = repo

    def discover_rooms(self, request: CommunityDiscoverRequest) -> CommunityRoomCatalogResponse:
        language = self._normalize_language(request.preferred_language or request.ui_language)
        region = self._normalize_region(request.region)
        care_path = self._normalize_care_path(request.care_path)
        urgency_band = self._normalize_urgency(request.urgency_band)
        symptom_tags = (
            self._extract_symptom_tags(request.symptom_text or "")
            if request.symptom_text
            else ["general-care"]
        )
        ui_language = request.ui_language or "English"
        rooms = self._load_rooms_with_seed_examples()

        recommended_rooms: list[CommunityRoomSummary] = []
        seen_ids: set[str] = set()

        if request.symptom_text:
            exact_match = self._match_room_descriptor(
                CommunityMatchRequest(
                    symptom_text=request.symptom_text,
                    care_path=request.care_path,
                    urgency_band=request.urgency_band,
                    preferred_language=request.preferred_language,
                    region=request.region,
                    ui_language=request.ui_language,
                )
            )
            summary = self._build_summary_from_match(
                match=exact_match,
                rooms=rooms,
                ui_language=ui_language,
                description=self._room_description(
                    "exact-match",
                    ui_language,
                    exact_match.symptom_tags,
                    exact_match.care_path,
                ),
                match_reason=self._exact_match_reason(
                    ui_language,
                    exact_match.symptom_tags,
                    exact_match.care_path,
                ),
            )
            recommended_rooms.append(summary)
            seen_ids.add(summary.id)

        for template in self._recommended_templates(symptom_tags, care_path, urgency_band):
            summary = self._build_template_summary(
                template=template,
                language=language,
                region=region,
                ui_language=ui_language,
                rooms=rooms,
                match_reason=self._template_match_reason(
                    template.key,
                    ui_language,
                    symptom_tags,
                    care_path,
                ),
            )
            if summary.id in seen_ids:
                continue
            recommended_rooms.append(summary)
            seen_ids.add(summary.id)
            if len(recommended_rooms) >= 3:
                break

        browse_rooms = [
            self._build_summary_from_existing_room(room, ui_language)
            for room in rooms
            if room.get("source") == "custom" and room.get("id") not in seen_ids
        ]
        seen_ids.update(room.id for room in browse_rooms)

        browse_rooms.extend(
            self._build_template_summary(
                template=template,
                language=language,
                region=region,
                ui_language=ui_language,
                rooms=rooms,
                match_reason=None,
            )
            for template in self._room_templates()
            if self._build_template_room_id(template, language, region) not in seen_ids
        )

        return CommunityRoomCatalogResponse(
            selected_context_summary=self._selected_context_summary(
                ui_language=ui_language,
                symptom_text=request.symptom_text,
                symptom_tags=symptom_tags,
                care_path=care_path,
                urgency_band=urgency_band,
                language=language,
                region=region,
            ),
            recommended_rooms=recommended_rooms,
            browse_rooms=browse_rooms,
        )

    def match_room(self, user: User, request: CommunityMatchRequest) -> CommunityRoomResponse:
        match = self._match_room_descriptor(request)
        rooms = self._load_rooms_with_seed_examples()
        room = next((room for room in rooms if room.get("id") == match.room_id), None)
        if room is None:
            room = self._new_room(match)
            room = self.repo.upsert_room(room)

        room = self._ensure_membership(room, user)
        self.repo.upsert_room(room)
        return self._serialize_room(
            room=room,
            user=user,
            ui_language=request.ui_language or "English",
            symptom_text=request.symptom_text,
        )

    def create_room(
        self,
        user: User,
        request: CommunityCreateRoomRequest,
    ) -> CommunityRoomResponse:
        room = self._new_custom_room(user, request)
        room = self._ensure_membership(room, user)
        room = self.repo.upsert_room(room)
        return self._serialize_room(
            room=room,
            user=user,
            ui_language=request.ui_language or "English",
            symptom_text=request.symptom_text or request.focus,
        )

    def join_room(
        self,
        user: User,
        room_id: str,
        request: CommunityJoinRequest,
    ) -> CommunityRoomResponse:
        rooms = self._load_rooms_with_seed_examples()
        room = next((item for item in rooms if item.get("id") == room_id), None)
        if room is None:
            language = self._normalize_language(request.preferred_language or request.ui_language)
            region = self._normalize_region(request.region)
            template = self._template_for_room_id(room_id)
            if template is not None:
                room = self._new_template_room(template, language, region)
                room = self.repo.upsert_room(room)
            elif request.symptom_text:
                match = self._match_room_descriptor(
                    CommunityMatchRequest(
                        symptom_text=request.symptom_text,
                        care_path=request.care_path,
                        urgency_band=request.urgency_band,
                        preferred_language=request.preferred_language,
                        region=request.region,
                        ui_language=request.ui_language,
                    )
                )
                room = self._new_room(match)
                room = self.repo.upsert_room(room)
            else:
                raise ValueError("We could not find that support room.")

        room = self._ensure_membership(room, user)
        self.repo.upsert_room(room)
        return self._serialize_room(
            room=room,
            user=user,
            ui_language=request.ui_language or "English",
            symptom_text=request.symptom_text,
        )

    def get_room(self, user: User, room_id: str, ui_language: str | None = None) -> CommunityRoomResponse:
        rooms = self._load_rooms_with_seed_examples()
        room = next((item for item in rooms if item.get("id") == room_id), None)
        if room is None:
            raise ValueError("We could not find that support room.")

        room = self._ensure_membership(room, user)
        self.repo.upsert_room(room)
        return self._serialize_room(
            room=room,
            user=user,
            ui_language=ui_language or "English",
            symptom_text=None,
        )

    def post_message(
        self,
        user: User,
        room_id: str,
        request: CommunityMessageRequest,
    ) -> CommunityRoomResponse:
        content = self._sanitize_message(request.content)
        if not content:
            raise ValueError("Please share a little more before sending your message.")

        def updater(room: dict[str, Any]) -> dict[str, Any]:
            next_room = self._ensure_membership(room, user)
            messages = list(next_room.get("messages", []))
            messages.append(
                {
                    "id": f"msg-{datetime.now(timezone.utc).timestamp():.6f}".replace(".", ""),
                    "user_id": user.id,
                    "display_name": self._alias_for_room(next_room, user.id),
                    "content": content,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            next_room["messages"] = messages[-80:]
            return next_room

        updated_room = self.repo.update_room(room_id, updater)
        if updated_room is None:
            raise ValueError("We could not find that support room.")

        return self._serialize_room(
            room=updated_room,
            user=user,
            ui_language=request.ui_language or "English",
            symptom_text=None,
        )

    def _match_room_descriptor(self, request: CommunityMatchRequest) -> RoomMatch:
        language = self._normalize_language(request.preferred_language)
        care_path = self._normalize_care_path(request.care_path)
        urgency_band = self._normalize_urgency(request.urgency_band)
        symptom_tags = self._extract_symptom_tags(request.symptom_text)
        region = self._normalize_region(request.region)
        slug = "-".join(
            [
                region.lower().replace(" ", "-"),
                language.lower(),
                urgency_band.lower().replace(" ", "-"),
                care_path.lower().replace(" ", "-"),
                "-".join(symptom_tags[:2]) if symptom_tags else "general-care",
            ]
        )
        return RoomMatch(
            room_id=f"room-{slug}",
            care_path=care_path,
            urgency_band=urgency_band,
            symptom_tags=symptom_tags,
            language=language,
            region=region,
        )

    def _new_room(self, match: RoomMatch) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "id": match.room_id,
            "title": self._room_title(
                "English",
                match.urgency_band,
                match.care_path,
                match.symptom_tags,
                match.region,
            ),
            "care_path": match.care_path,
            "urgency_band": match.urgency_band,
            "symptom_tags": match.symptom_tags,
            "language": match.language,
            "region": match.region,
            "source": "system",
            "memberships": [],
            "messages": self._build_seed_messages(
                ui_language=match.language,
                symptom_tags=match.symptom_tags,
                care_path=match.care_path,
                room_key="exact-match",
                created_at=now,
            ),
            "created_at": now,
            "updated_at": now,
        }

    def _new_template_room(self, template: RoomTemplate, language: str, region: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "id": self._build_template_room_id(template, language, region),
            "title": self._template_title(template.key, "English", region),
            "care_path": template.care_path,
            "urgency_band": template.urgency_band,
            "symptom_tags": list(template.symptom_tags),
            "language": language,
            "region": region,
            "source": "system",
            "memberships": [],
            "messages": self._build_seed_messages(
                ui_language=language,
                symptom_tags=list(template.symptom_tags),
                care_path=template.care_path,
                room_key=template.key,
                created_at=now,
            ),
            "created_at": now,
            "updated_at": now,
        }

    def _new_custom_room(
        self,
        user: User,
        request: CommunityCreateRoomRequest,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        language = self._normalize_language(request.preferred_language or request.ui_language)
        region = self._normalize_region(request.region)
        care_path = self._normalize_care_path(request.care_path)
        urgency_band = self._normalize_urgency(request.urgency_band)
        symptom_source = " ".join(
            part.strip()
            for part in [request.symptom_text or "", request.title, request.focus]
            if part and part.strip()
        )
        symptom_tags = self._extract_symptom_tags(symptom_source)
        room_id = self._build_custom_room_id(request.title, user.id)
        return {
            "id": room_id,
            "title": request.title.strip(),
            "description": request.focus.strip(),
            "care_path": care_path,
            "urgency_band": urgency_band,
            "symptom_tags": symptom_tags,
            "language": language,
            "region": region,
            "source": "custom",
            "memberships": [],
            "messages": self._build_seed_messages(
                ui_language=language,
                symptom_tags=symptom_tags,
                care_path=care_path,
                room_key="custom",
                created_at=now,
                focus=request.focus.strip(),
            ),
            "created_at": now,
            "updated_at": now,
        }

    def _ensure_membership(self, room: dict[str, Any], user: User) -> dict[str, Any]:
        memberships = list(room.get("memberships", []))
        if not any(member.get("user_id") == user.id for member in memberships):
            memberships.append(
                {
                    "user_id": user.id,
                    "display_name": self._generate_alias(user.id, len(memberships) + 1),
                    "joined_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            room["memberships"] = memberships
        return room

    def _serialize_room(
        self,
        *,
        room: dict[str, Any],
        user: User,
        ui_language: str,
        symptom_text: str | None,
    ) -> CommunityRoomResponse:
        memberships = room.get("memberships", [])
        localized_title = (
            str(room.get("title") or "")
            if room.get("source") == "custom"
            else self._room_title(
                ui_language,
                str(room["urgency_band"]),
                str(room["care_path"]),
                [str(tag) for tag in room.get("symptom_tags", [])],
                str(room["region"]),
            )
        )
        template = self._template_for_room_id(str(room["id"]))
        room_key = self._room_key_for_room(room, template)
        messages = [
            CommunityMessage(
                id=message["id"],
                user_id=message["user_id"],
                display_name=(
                    self._moderator_display_name(ui_language)
                    if message["user_id"] == "moderator"
                    else (
                        self._seed_peer_display_name(ui_language, message["user_id"])
                        if str(message["id"]).startswith("msg-seed-")
                        else message["display_name"]
                    )
                ),
                content=(
                    self._seed_message(ui_language)
                    if message["user_id"] == "moderator" and message["id"] == "msg-welcome"
                    else (
                        self._seed_peer_messages(
                            ui_language=ui_language,
                            room_key=room_key,
                            symptom_tags=[str(tag) for tag in room.get("symptom_tags", [])],
                            care_path=str(room["care_path"]),
                            focus=str(room.get("description") or ""),
                        )[max(int(str(message["id"]).split("-")[-1]) - 1, 0)]
                        if str(message["id"]).startswith("msg-seed-")
                        else message["content"]
                    )
                ),
                created_at=datetime.fromisoformat(message["created_at"]),
                is_current_user=message["user_id"] == user.id,
            )
            for message in room.get("messages", [])
        ]
        summary = CommunityRoomSummary(
            id=room["id"],
            title=localized_title,
            description=(
                str(room.get("description") or "").strip()
                or self._room_description(
                    room_key,
                    ui_language,
                    [str(tag) for tag in room.get("symptom_tags", [])],
                    str(room["care_path"]),
                )
            ),
            match_reason=None,
            preview_topics=self._preview_topics(
                ui_language,
                room_key,
                [str(tag) for tag in room.get("symptom_tags", [])],
                str(room["care_path"]),
            ),
            care_path=self._localize_care_path(str(room["care_path"]), ui_language),
            urgency_band=self._localize_urgency(str(room["urgency_band"]), ui_language),
            symptom_tags=[
                self._localize_symptom_tag(str(tag), ui_language)
                for tag in room.get("symptom_tags", [])
            ],
            language=self._localize_language_name(str(room["language"]), ui_language),
            region=room["region"],
            member_count=len(memberships),
            message_count=len(messages),
            latest_activity_at=datetime.fromisoformat(room["updated_at"]),
        )
        return CommunityRoomResponse(
            room=summary,
            messages=messages,
            your_alias=self._alias_for_room(room, user.id),
            safety_notice=self._safety_notice(ui_language),
            moderation_notice=self._moderation_notice(ui_language),
            entry_prompt=self._entry_prompt(ui_language, summary),
            matching_summary=self._matching_summary(ui_language, summary, symptom_text),
            starter_topics=self._starter_topics(ui_language),
        )

    def _build_summary_from_existing_room(
        self,
        room: dict[str, Any],
        ui_language: str,
    ) -> CommunityRoomSummary:
        template = self._template_for_room_id(str(room["id"]))
        room_key = self._room_key_for_room(room, template)
        title = (
            str(room.get("title") or "")
            if room.get("source") == "custom"
            else self._room_title(
                ui_language,
                str(room["urgency_band"]),
                str(room["care_path"]),
                [str(tag) for tag in room.get("symptom_tags", [])],
                str(room["region"]),
            )
        )
        return CommunityRoomSummary(
            id=room["id"],
            title=title,
            description=(
                str(room.get("description") or "").strip()
                or self._room_description(
                    room_key,
                    ui_language,
                    [str(tag) for tag in room.get("symptom_tags", [])],
                    str(room["care_path"]),
                )
            ),
            match_reason=None,
            preview_topics=self._preview_topics(
                ui_language,
                room_key,
                [str(tag) for tag in room.get("symptom_tags", [])],
                str(room["care_path"]),
            ),
            care_path=self._localize_care_path(str(room["care_path"]), ui_language),
            urgency_band=self._localize_urgency(str(room["urgency_band"]), ui_language),
            symptom_tags=[
                self._localize_symptom_tag(str(tag), ui_language)
                for tag in room.get("symptom_tags", [])
            ],
            language=self._localize_language_name(str(room["language"]), ui_language),
            region=str(room["region"]),
            member_count=len(room.get("memberships", [])),
            message_count=len(room.get("messages", [])),
            latest_activity_at=datetime.fromisoformat(str(room["updated_at"])),
        )

    def _load_rooms_with_seed_examples(self) -> list[dict[str, Any]]:
        rooms = self.repo.load_rooms()
        changed = False
        next_rooms: list[dict[str, Any]] = []
        for room in rooms:
            next_room = self._ensure_seed_examples(room)
            if next_room is not room:
                changed = True
            next_rooms.append(next_room)
        if changed:
            self.repo.save_rooms(next_rooms)
        return next_rooms

    def _ensure_seed_examples(self, room: dict[str, Any]) -> dict[str, Any]:
        messages = list(room.get("messages", []))
        peer_messages = [message for message in messages if message.get("user_id") != "moderator"]
        if peer_messages:
            return room

        now = datetime.now(timezone.utc).isoformat()
        template = self._template_for_room_id(str(room["id"]))
        room_key = self._room_key_for_room(room, template)
        seeded = self._build_seed_messages(
            ui_language=str(room.get("language") or "English"),
            symptom_tags=[str(tag) for tag in room.get("symptom_tags", [])],
            care_path=str(room.get("care_path") or "General care"),
            room_key=room_key,
            created_at=now,
            focus=str(room.get("description") or ""),
        )
        next_room = dict(room)
        next_room["messages"] = seeded
        next_room["updated_at"] = now
        return next_room

    def _room_key_for_room(
        self,
        room: dict[str, Any],
        template: RoomTemplate | None,
    ) -> str:
        if room.get("source") == "custom":
            return "custom"
        if template is not None:
            return template.key
        return "exact-match"

    def _build_custom_room_id(self, title: str, user_id: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", title.strip().lower()).strip("-") or "support-room"
        suffix = hashlib.sha1(
            f"{title}-{user_id}-{datetime.now(timezone.utc).timestamp()}".encode("utf-8")
        ).hexdigest()[:8]
        return f"room-custom-{slug[:36]}-{suffix}"

    def _build_seed_messages(
        self,
        *,
        ui_language: str,
        symptom_tags: list[str],
        care_path: str,
        room_key: str,
        created_at: str,
        focus: str = "",
    ) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = [
            {
                "id": "msg-welcome",
                "user_id": "moderator",
                "display_name": "Room Guide",
                "content": self._seed_message(ui_language),
                "created_at": created_at,
            }
        ]
        for index, content in enumerate(
            self._seed_peer_messages(
                ui_language=ui_language,
                room_key=room_key,
                symptom_tags=symptom_tags,
                care_path=care_path,
                focus=focus,
            ),
            start=1,
        ):
            messages.append(
                {
                    "id": f"msg-seed-{index}",
                    "user_id": f"peer-{index}",
                    "display_name": self._seed_peer_display_name(ui_language, f"peer-{index}"),
                    "content": content,
                    "created_at": created_at,
                }
            )
        return messages

    def _build_summary_from_match(
        self,
        *,
        match: RoomMatch,
        rooms: list[dict[str, Any]],
        ui_language: str,
        description: str,
        match_reason: str | None,
    ) -> CommunityRoomSummary:
        existing_room = next((room for room in rooms if room.get("id") == match.room_id), None)
        latest = (
            datetime.fromisoformat(str(existing_room["updated_at"]))
            if existing_room
            else datetime.now(timezone.utc)
        )
        member_count = len(existing_room.get("memberships", [])) if existing_room else 0
        message_count = len(existing_room.get("messages", [])) if existing_room else 0
        return CommunityRoomSummary(
            id=match.room_id,
            title=self._room_title(
                ui_language,
                match.urgency_band,
                match.care_path,
                match.symptom_tags,
                match.region,
            ),
            description=description,
            match_reason=match_reason,
            preview_topics=self._preview_topics(
                ui_language,
                "exact-match",
                match.symptom_tags,
                match.care_path,
            ),
            care_path=self._localize_care_path(match.care_path, ui_language),
            urgency_band=self._localize_urgency(match.urgency_band, ui_language),
            symptom_tags=[self._localize_symptom_tag(tag, ui_language) for tag in match.symptom_tags],
            language=self._localize_language_name(match.language, ui_language),
            region=match.region,
            member_count=member_count,
            message_count=message_count,
            latest_activity_at=latest,
        )

    def _build_template_summary(
        self,
        *,
        template: RoomTemplate,
        language: str,
        region: str,
        ui_language: str,
        rooms: list[dict[str, Any]],
        match_reason: str | None,
    ) -> CommunityRoomSummary:
        room_id = self._build_template_room_id(template, language, region)
        existing_room = next((room for room in rooms if room.get("id") == room_id), None)
        latest = (
            datetime.fromisoformat(str(existing_room["updated_at"]))
            if existing_room
            else datetime.now(timezone.utc)
        )
        member_count = len(existing_room.get("memberships", [])) if existing_room else 0
        message_count = len(existing_room.get("messages", [])) if existing_room else 0
        return CommunityRoomSummary(
            id=room_id,
            title=self._template_title(template.key, ui_language, region),
            description=self._room_description(
                template.key,
                ui_language,
                list(template.symptom_tags),
                template.care_path,
            ),
            match_reason=match_reason,
            preview_topics=self._preview_topics(
                ui_language,
                template.key,
                list(template.symptom_tags),
                template.care_path,
            ),
            care_path=self._localize_care_path(template.care_path, ui_language),
            urgency_band=self._localize_urgency(template.urgency_band, ui_language),
            symptom_tags=[
                self._localize_symptom_tag(tag, ui_language)
                for tag in template.symptom_tags
            ],
            language=self._localize_language_name(language, ui_language),
            region=region,
            member_count=member_count,
            message_count=message_count,
            latest_activity_at=latest,
        )

    def _room_templates(self) -> list[RoomTemplate]:
        return [
            RoomTemplate(
                key="cold-flu-support",
                care_path="General care",
                urgency_band="Routine",
                symptom_tags=("sore-throat", "fever", "cough"),
            ),
            RoomTemplate(
                key="urgent-next-step",
                care_path="Urgent care",
                urgency_band="Urgent",
                symptom_tags=("general-care",),
            ),
            RoomTemplate(
                key="primary-care-first-visit",
                care_path="Primary care",
                urgency_band="Routine",
                symptom_tags=("general-care",),
            ),
            RoomTemplate(
                key="headache-fatigue-support",
                care_path="General care",
                urgency_band="Routine",
                symptom_tags=("headache", "fatigue"),
            ),
            RoomTemplate(
                key="stomach-issues-support",
                care_path="General care",
                urgency_band="Routine",
                symptom_tags=("stomach",),
            ),
            RoomTemplate(
                key="insurance-questions",
                care_path="General care",
                urgency_band="Routine",
                symptom_tags=("general-care",),
            ),
            RoomTemplate(
                key="doctor-choice",
                care_path="General care",
                urgency_band="Soon",
                symptom_tags=("general-care",),
            ),
            RoomTemplate(
                key="booking-prep",
                care_path="General care",
                urgency_band="Soon",
                symptom_tags=("general-care",),
            ),
        ]

    def _recommended_templates(
        self,
        symptom_tags: list[str],
        care_path: str,
        urgency_band: str,
    ) -> list[RoomTemplate]:
        recommended_keys: list[str] = []
        tags = set(symptom_tags)
        if {"sore-throat", "fever", "cough"} & tags:
            recommended_keys.append("cold-flu-support")
        if {"headache", "fatigue"} & tags:
            recommended_keys.append("headache-fatigue-support")
        if "stomach" in tags:
            recommended_keys.append("stomach-issues-support")
        if care_path == "Urgent care" or urgency_band in {"Urgent", "Soon"}:
            recommended_keys.append("urgent-next-step")
        if care_path in {"Primary care", "General care"}:
            recommended_keys.append("primary-care-first-visit")
        recommended_keys.extend(["doctor-choice", "booking-prep"])

        seen: set[str] = set()
        template_map = {template.key: template for template in self._room_templates()}
        ordered: list[RoomTemplate] = []
        for key in recommended_keys:
            if key in seen or key not in template_map:
                continue
            seen.add(key)
            ordered.append(template_map[key])
        return ordered

    def _template_for_room_id(self, room_id: str) -> RoomTemplate | None:
        if "-template-" not in room_id:
            return None
        template_key = room_id.split("-template-", 1)[1]
        for template in self._room_templates():
            if template.key == template_key:
                return template
        return None

    def _build_template_room_id(self, template: RoomTemplate, language: str, region: str) -> str:
        return (
            f"room-{region.lower().replace(' ', '-')}-{language.lower()}-template-{template.key}"
        )

    def _template_title(self, key: str, ui_language: str, region: str) -> str:
        if ui_language == "Mandarin":
            mapping = {
                "cold-flu-support": f"{region} · 感冒与喉咙痛交流室",
                "urgent-next-step": f"{region} · 紧急门诊下一步讨论室",
                "primary-care-first-visit": f"{region} · 初级保健首次就诊交流室",
                "headache-fatigue-support": f"{region} · 头痛与疲劳交流室",
                "stomach-issues-support": f"{region} · 肠胃不适交流室",
                "insurance-questions": f"{region} · 保险疑问交流室",
                "doctor-choice": f"{region} · 医生选择交流室",
                "booking-prep": f"{region} · 预约准备交流室",
            }
            return mapping.get(key, f"{region} · 互助交流室")
        if ui_language == "Spanish":
            mapping = {
                "cold-flu-support": f"{region} · chat para resfriado y garganta",
                "urgent-next-step": f"{region} · chat de siguiente paso urgente",
                "primary-care-first-visit": f"{region} · primera visita de atencion primaria",
                "headache-fatigue-support": f"{region} · chat de dolor de cabeza y fatiga",
                "stomach-issues-support": f"{region} · chat de molestias estomacales",
                "insurance-questions": f"{region} · dudas de seguro",
                "doctor-choice": f"{region} · eleccion de doctor",
                "booking-prep": f"{region} · preparacion para reserva",
            }
            return mapping.get(key, f"{region} · sala de apoyo")
        mapping = {
            "cold-flu-support": f"{region} · cold, flu, and sore throat room",
            "urgent-next-step": f"{region} · urgent care next-step room",
            "primary-care-first-visit": f"{region} · first primary care visit room",
            "headache-fatigue-support": f"{region} · headache and fatigue room",
            "stomach-issues-support": f"{region} · stomach issues room",
            "insurance-questions": f"{region} · insurance questions room",
            "doctor-choice": f"{region} · doctor choice room",
            "booking-prep": f"{region} · booking prep room",
        }
        return mapping.get(key, f"{region} · support room")

    def _room_description(
        self,
        key: str,
        ui_language: str,
        symptom_tags: list[str],
        care_path: str,
    ) -> str:
        if key == "custom":
            if ui_language == "Mandarin":
                return "这是社区成员创建的互助房间，适合围绕一个更具体的就医问题分享经验。"
            if ui_language == "Spanish":
                return "Esta es una sala creada por la comunidad para hablar de una situacion de atencion mas especifica."
            return "This is a community-created room for sharing experience around a more specific care question."
        if key == "exact-match":
            if ui_language == "Mandarin":
                return "这个房间更贴近你刚刚描述的症状场景，适合先看和你相似的人是怎么决定第一步的。"
            if ui_language == "Spanish":
                return "Esta sala se acerca más a lo que acabas de describir y sirve para ver cómo otras personas tomaron su primer paso."
            return "This room is the closest fit to the situation you just described and is a good place to see how others chose their first step."

        if ui_language == "Mandarin":
            mapping = {
                "cold-flu-support": "适合交流感冒、发烧、喉咙痛这类常见上呼吸道不适的第一步就医经验。",
                "urgent-next-step": "适合交流当你担心需要尽快看诊时，别人是如何决定 urgent care 或下一步行动的。",
                "primary-care-first-visit": "适合交流第一次找 primary care、挂号流程和看诊前准备。",
                "headache-fatigue-support": "适合交流头痛、疲劳、注意力下降这类非创伤症状的就医体验。",
                "stomach-issues-support": "适合交流恶心、胃痛、腹泻等肠胃症状的就医与准备经验。",
                "insurance-questions": "适合分享保险看不懂、copay、network 和 referral 相关经验。",
                "doctor-choice": "适合讨论在多个医生之间怎么做最后选择。",
                "booking-prep": "适合分享预约流程、官方网站跳转和看诊前准备。",
            }
            return mapping.get(key, "适合交流相似就医路径中的经验。")
        if ui_language == "Spanish":
            mapping = {
                "cold-flu-support": "Ideal para compartir experiencias sobre resfriado, fiebre y dolor de garganta, y sobre qué hacer primero.",
                "urgent-next-step": "Ideal para hablar de cómo otras personas decidieron si debían ir a urgent care o actuar rápido.",
                "primary-care-first-visit": "Ideal para hablar de la primera visita de atencion primaria, registro y preparacion.",
                "headache-fatigue-support": "Ideal para hablar de dolor de cabeza, fatiga y sintomas parecidos sin lesion.",
                "stomach-issues-support": "Ideal para compartir experiencias sobre nausea, dolor de estomago y diarrea.",
                "insurance-questions": "Ideal para hablar de red, copago, referral y partes confusas del seguro.",
                "doctor-choice": "Ideal para comparar como otras personas eligieron entre varios doctores.",
                "booking-prep": "Ideal para compartir pasos de reserva, handoff oficial y preparacion previa a la visita.",
            }
            return mapping.get(key, "Ideal para compartir experiencias de una ruta de atencion parecida.")
        mapping = {
            "cold-flu-support": "A good room for sharing first-step decisions around cold, fever, cough, and sore-throat symptoms.",
            "urgent-next-step": "A good room for comparing how other people decided when urgent care or faster action made sense.",
            "primary-care-first-visit": "A good room for first primary care visits, registration, and what to prepare before you go.",
            "headache-fatigue-support": "A good room for talking through headache, fatigue, and low-energy care experiences.",
            "stomach-issues-support": "A good room for nausea, stomach pain, and digestive issue care experiences.",
            "insurance-questions": "A good room for insurance confusion, network questions, copays, and referral stories.",
            "doctor-choice": "A good room for hearing how other people made the final choice between similar doctors.",
            "booking-prep": "A good room for booking handoff tips, visit preparation, and what to expect before the appointment.",
        }
        return mapping.get(key, "A good room for people with a similar care journey.")

    def _template_match_reason(
        self,
        key: str,
        ui_language: str,
        symptom_tags: list[str],
        care_path: str,
    ) -> str:
        if ui_language == "Mandarin":
            mapping = {
                "cold-flu-support": "你提到的症状和感冒、发烧、喉咙痛这一类交流主题比较接近。",
                "urgent-next-step": "你当前的 care path 更接近“需要尽快决定下一步”的场景。",
                "primary-care-first-visit": "你当前更像是需要先理清 primary care 第一步怎么走。",
                "headache-fatigue-support": "你的症状和头痛、疲劳这一类经验房间更接近。",
                "stomach-issues-support": "你的描述和肠胃相关经验房间更接近。",
                "insurance-questions": "如果你现在对保险也有疑问，这个房间通常会很有帮助。",
                "doctor-choice": "在进入医生推荐前后，这个房间适合交流最后怎么做选择。",
                "booking-prep": "如果你担心下一步怎么预约，这个房间通常更有准备价值。",
            }
            return mapping.get(key, "这个房间和你当前的就医情境比较接近。")
        if ui_language == "Spanish":
            mapping = {
                "cold-flu-support": "Tus sintomas se parecen a las experiencias que se comparten en esta sala.",
                "urgent-next-step": "Tu situacion suena mas cercana a una decision rapida sobre el siguiente paso.",
                "primary-care-first-visit": "Tu situacion suena parecida a la de personas que estan resolviendo su primera visita de atencion primaria.",
                "headache-fatigue-support": "Tus sintomas se parecen a los temas mas comunes de esta sala.",
                "stomach-issues-support": "Tu descripcion encaja mejor con experiencias relacionadas con el estomago.",
                "insurance-questions": "Esta sala puede ayudar si parte de tu confusion tambien viene del seguro.",
                "doctor-choice": "Esta sala puede ayudar cuando necesitas comparar opciones de doctor.",
                "booking-prep": "Esta sala puede ayudar si tu siguiente duda es como reservar y prepararte.",
            }
            return mapping.get(key, "Esta sala parece cercana a tu situacion actual.")
        mapping = {
            "cold-flu-support": "Your symptoms overlap with the kinds of cold and throat experiences shared in this room.",
            "urgent-next-step": "Your current situation sounds closer to a quick next-step decision, which this room often discusses.",
            "primary-care-first-visit": "This room fits people who are still figuring out the first primary care step.",
            "headache-fatigue-support": "Your symptoms overlap with the headache and fatigue experiences usually discussed here.",
            "stomach-issues-support": "Your situation sounds close to the stomach-related care experiences shared here.",
            "insurance-questions": "This room can help if insurance confusion is part of what is slowing you down.",
            "doctor-choice": "This room can help when you want peer perspective before choosing between doctors.",
            "booking-prep": "This room can help if your next concern is booking, timing, and what to prepare.",
        }
        return mapping.get(key, "This room looks relevant to your current situation.")

    def _selected_context_summary(
        self,
        *,
        ui_language: str,
        symptom_text: str | None,
        symptom_tags: list[str],
        care_path: str,
        urgency_band: str,
        language: str,
        region: str,
    ) -> str:
        if ui_language == "Mandarin":
            if symptom_text:
                return (
                    f"我们会优先根据你当前的症状、{self._localize_care_path(care_path, ui_language)}、"
                    f"{self._localize_urgency(urgency_band, ui_language)}、{self._localize_language_name(language, ui_language)} 和 {region} 来推荐房间。"
                )
            return f"你也可以先浏览 {region}、{self._localize_language_name(language, ui_language)} 的互助房间，再决定加入哪一个。"
        if ui_language == "Spanish":
            if symptom_text:
                return (
                    f"Primero recomendamos salas usando tus sintomas, {self._localize_care_path(care_path, ui_language)}, "
                    f"{self._localize_urgency(urgency_band, ui_language)}, {self._localize_language_name(language, ui_language)} y {region}."
                )
            return f"Tambien puedes explorar salas de apoyo en {region} y elegir la que te parezca mas util."
        if symptom_text:
            return (
                f"We recommend rooms first using your symptom context, {care_path.lower()}, "
                f"{urgency_band.lower()} urgency, {language}, and {region}."
            )
        return f"You can also browse support rooms in {region} and join the one that feels most useful."

    def _exact_match_reason(self, ui_language: str, symptom_tags: list[str], care_path: str) -> str:
        if ui_language == "Mandarin":
            return "这是和你当前描述最接近的房间。"
        if ui_language == "Spanish":
            return "Esta es la coincidencia mas cercana a lo que acabas de describir."
        return "This is the closest room match for what you just described."

    def _generate_alias(self, user_id: str, index: int) -> str:
        suffix = hashlib.sha1(user_id.encode("utf-8")).hexdigest()[:3].upper()
        return f"Member {index:02d}-{suffix}"

    def _alias_for_room(self, room: dict[str, Any], user_id: str) -> str:
        for member in room.get("memberships", []):
            if member.get("user_id") == user_id:
                return str(member.get("display_name") or "Member")
        return "Member"

    def _normalize_language(self, preferred_language: str | None) -> str:
        language = (preferred_language or "").strip().lower()
        if "mandarin" in language or "中文" in language or "chinese" in language:
            return "Mandarin"
        if "spanish" in language or "español" in language or "espanol" in language:
            return "Spanish"
        return "English"

    def _normalize_care_path(self, care_path: str | None) -> str:
        path = (care_path or "").strip().lower()
        if "urgent" in path:
            return "Urgent care"
        if "primary" in path or "family" in path:
            return "Primary care"
        if "ent" in path or "special" in path:
            return "Specialist follow-up"
        return "General care"

    def _normalize_urgency(self, urgency_band: str | None) -> str:
        urgency = (urgency_band or "").strip().lower()
        if urgency in {"emergency", "urgent", "soon", "routine", "self-care"}:
            return urgency.replace("-", " ").title()
        return "Routine"

    def _normalize_region(self, region: str | None) -> str:
        if not region:
            return "Los Angeles"
        normalized = region.strip()
        return normalized or "Los Angeles"

    def _extract_symptom_tags(self, symptom_text: str) -> list[str]:
        text = symptom_text.lower()
        buckets = [
            ("sore-throat", ["sore throat", "throat", "strep"]),
            ("fever", ["fever", "temperature", "chills"]),
            ("headache", ["headache", "migraine", "light sensitive"]),
            ("stomach", ["stomach", "nausea", "vomit", "diarrhea", "abdominal"]),
            ("cough", ["cough", "congestion", "sinus", "cold"]),
            ("fatigue", ["fatigue", "tired", "weak"]),
            ("rash", ["rash", "itch", "skin"]),
        ]
        tags = [label for label, keywords in buckets if any(keyword in text for keyword in keywords)]
        return tags[:3] or ["general-care"]

    def _room_title(
        self,
        ui_language: str,
        urgency_band: str,
        care_path: str,
        symptom_tags: list[str],
        region: str,
    ) -> str:
        localized_tag = self._localize_symptom_tag(
            symptom_tags[0] if symptom_tags else "general-care",
            ui_language,
        )
        localized_care_path = self._localize_care_path(care_path, ui_language)
        if localized_tag.lower() == localized_care_path.lower():
            if ui_language == "Mandarin":
                return f"{region} · {localized_care_path} 经验交流"
            if ui_language == "Spanish":
                return f"{region} · experiencias de {localized_care_path.lower()}"
            return f"{region} · {localized_care_path} experience room"

        if ui_language == "Mandarin":
            return f"{region} · {localized_tag} · {localized_care_path} 经验交流"
        if ui_language == "Spanish":
            return f"{region} · {localized_tag} · experiencias de {localized_care_path.lower()}"
        return f"{region} · {localized_tag} · {localized_care_path} experience room"

    def _moderator_display_name(self, ui_language: str) -> str:
        if ui_language == "Mandarin":
            return "房间向导"
        if ui_language == "Spanish":
            return "Guia de la sala"
        return "Room Guide"

    def _seed_peer_display_name(self, ui_language: str, seed_id: str) -> str:
        suffix = "A" if seed_id.endswith("1") else "B"
        if ui_language == "Mandarin":
            return f"经验分享者 {suffix}"
        if ui_language == "Spanish":
            return f"Compañero {suffix}"
        return f"Peer Member {suffix}"

    def _seed_message(self, ui_language: str) -> str:
        if ui_language == "Mandarin":
            return "欢迎来到匿名互助讨论室。这里适合分享就医流程、保险体验、预约经验和看诊前准备，不适合替别人下诊断。"
        if ui_language == "Spanish":
            return "Bienvenido al espacio anónimo de apoyo. Comparte experiencias sobre clínicas, seguro, reservas y preparación para la visita, no diagnósticos."
        return "Welcome to the anonymous support room. Share care navigation, insurance, booking, and preparation experiences here, not diagnoses."

    def _seed_peer_messages(
        self,
        *,
        ui_language: str,
        room_key: str,
        symptom_tags: list[str],
        care_path: str,
        focus: str,
    ) -> list[str]:
        normalized_tags = {tag.strip().lower() for tag in symptom_tags}
        if room_key == "custom":
            if ui_language == "Mandarin":
                return [
                    f"我加入这个房间是因为我也在处理类似“{focus or '就医决策'}”的问题，当时最有帮助的是先把想问诊所和保险的问题写下来。",
                    "如果你也是第一次处理这类情况，我建议先说清楚你卡住的是保险、选医生，还是预约流程，大家会更容易给你有用经验。",
                ]
            if ui_language == "Spanish":
                return [
                    f"Entré a esta sala porque yo también estaba resolviendo algo parecido a “{focus or 'esta decisión de atención'}”, y lo que más me ayudó fue anotar primero mis dudas sobre seguro y clínica.",
                    "Si es tu primera vez con algo así, ayuda mucho decir si tu confusión principal viene del seguro, del doctor o de la reserva.",
                ]
            return [
                f"I joined a room like this because I was also working through “{focus or 'a similar care decision'},” and the most helpful step was writing down my insurance and clinic questions first.",
                "If this is your first time dealing with something similar, it helps to say whether the confusing part is insurance, choosing a doctor, or the booking process.",
            ]

        if room_key == "booking-prep":
            if ui_language == "Mandarin":
                return [
                    "我上次是先打开官方预约页，再把保险卡、证件和想问的问题准备好，整个流程会顺很多。",
                    "如果担心第一次就诊太紧张，可以先在房间里确认别人通常会带什么、提前多久到，会安心很多。",
                ]
            if ui_language == "Spanish":
                return [
                    "La vez pasada abrí primero la página oficial de reserva y preparé mi tarjeta del seguro, identificación y preguntas antes de hacer clic.",
                    "Si te pone nervioso ir por primera vez, ayuda mucho preguntar aquí qué llevó otra gente y cuánto tiempo antes llegó.",
                ]
            return [
                "Last time I opened the official booking page first and made sure I had my insurance card, ID, and questions ready before clicking through.",
                "If you feel anxious about a first visit, it really helps to ask what other people brought and how early they arrived.",
            ]

        if room_key == "doctor-choice":
            if ui_language == "Mandarin":
                return [
                    "我最后是在两个医生之间比较语言沟通和预约时间，发现把“我最在意什么”先说清楚特别有帮助。",
                    "如果你在意解释是否清楚，可以直接问别人他们最后为什么选 A 医生而不是 B 医生。",
                ]
            if ui_language == "Spanish":
                return [
                    "Al final comparé dos doctores por idioma y disponibilidad, y me ayudó mucho decir primero qué era lo más importante para mí.",
                    "Si te importa que te expliquen bien las cosas, puedes preguntar por qué alguien eligió al doctor A y no al B.",
                ]
            return [
                "I ended up comparing two doctors mostly on communication style and availability, and it helped to say clearly what mattered most to me.",
                "If clear explanations matter to you, ask why someone chose doctor A instead of doctor B.",
            ]

        if room_key == "insurance-questions":
            if ui_language == "Mandarin":
                return [
                    "我当时最卡的是 network 和 copay，后来发现先确认是不是 in-network，能少走很多弯路。",
                    "如果 plan 名字很像，可以把你看到的保险公司和 plan type 先写出来，别人更容易分享接近的经验。",
                ]
            if ui_language == "Spanish":
                return [
                    "Lo que más me confundía era la red y el copago; primero confirmé si el doctor estaba dentro de la red y eso me ahorró mucho tiempo.",
                    "Si los nombres de los planes se parecen, ayuda escribir primero la aseguradora y el tipo de plan para que otras personas comparen mejor.",
                ]
            return [
                "The most confusing part for me was network and copay, and confirming in-network status first saved a lot of time.",
                "If your plan name looks similar to others, writing down the carrier and plan type helps people share more relevant experience.",
            ]

        if room_key == "urgent-next-step":
            if ui_language == "Mandarin":
                return [
                    "我那次是先去 urgent care，因为 primary care 太慢了。真正有帮助的是先判断自己更担心症状恶化还是单纯想快一点看上。",
                    "如果你拿不准要不要今天就去，听别人为什么选择 urgent care、又在现场遇到了什么，通常很有参考价值。",
                ]
            if ui_language == "Spanish":
                return [
                    "En mi caso fui primero a urgent care porque primary care tardaba demasiado. Lo más útil fue decidir si mi preocupación era el empeoramiento o simplemente la velocidad.",
                    "Si no sabes si debes ir hoy mismo, escuchar por qué otras personas eligieron urgent care suele ayudar bastante.",
                ]
            return [
                "I chose urgent care first because primary care was moving too slowly, and the real question was whether I was worried about symptoms getting worse or just trying to be seen faster.",
                "If you are unsure whether today is the day to go, hearing why other people chose urgent care can be really grounding.",
            ]

        if "sore-throat" in normalized_tags or "cough" in normalized_tags or "fever" in normalized_tags:
            if ui_language == "Mandarin":
                return [
                    "我之前也是喉咙痛加发烧，最后先看了一般门诊，最有帮助的是提前准备好症状持续多久、有没有发热和咳嗽这些信息。",
                    "如果你也在犹豫先去哪里，可以问问别人是怎么在“先观察一下”和“尽快去看”之间做决定的。",
                ]
            if ui_language == "Spanish":
                return [
                    "Yo también tuve dolor de garganta y fiebre; al final empecé con atención general y me ayudó llevar claro cuánto duraban los síntomas y si había tos.",
                    "Si estás dudando adónde ir primero, pregunta cómo decidió otra gente entre esperar un poco más o ir pronto.",
                ]
            return [
                "I also had a sore throat with fever, and starting with general care worked better once I had written down how long the symptoms had been going on and whether cough was involved.",
                "If you are unsure where to go first, it helps to hear how other people decided between watching symptoms a little longer and going in sooner.",
            ]

        if "headache" in normalized_tags or "fatigue" in normalized_tags:
            if ui_language == "Mandarin":
                return [
                    "我之前头痛加疲劳的时候，先去一般门诊会比较安心，因为可以先排除是不是需要更快处理。",
                    "别人最常分享的经验是：先描述头痛位置、持续时间、有没有影响看光或注意力，会更容易得到有用建议。",
                ]
            if ui_language == "Spanish":
                return [
                    "Cuando tuve dolor de cabeza y fatiga, empezar por atención general me ayudó a decidir si realmente necesitaba algo más urgente.",
                    "Mucha gente comenta que ayuda describir la zona del dolor, cuánto dura y si afecta la luz o la concentración.",
                ]
            return [
                "When I had headache plus fatigue, starting with general care helped me figure out whether it really needed faster follow-up.",
                "People usually find it helpful to describe where the headache is, how long it lasts, and whether light or concentration makes it worse.",
            ]

        if "stomach" in normalized_tags:
            if ui_language == "Mandarin":
                return [
                    "我那次肠胃不舒服的时候，先确认自己能不能正常喝水、有没有持续恶化，再决定要不要尽快去看。",
                    "别人分享得最多的是饮食准备、什么时候先去一般门诊、什么时候不要再拖。",
                ]
            if ui_language == "Spanish":
                return [
                    "Cuando tuve molestias de estómago, primero pensé si podía seguir tomando agua y si los síntomas iban empeorando antes de decidir ir.",
                    "Lo que más comparte la gente aquí es qué preparó para la visita y cuándo dejó de esperar en casa.",
                ]
            return [
                "When I was dealing with stomach symptoms, the first thing I checked was whether I could still keep fluids down and whether things were getting worse.",
                "People here usually share what they ate, what they prepared for the visit, and when they decided not to wait at home any longer.",
            ]

        if care_path == "Primary care":
            if ui_language == "Mandarin":
                return [
                    "我第一次约 primary care 的时候，最有帮助的是先在这里看别人是怎么挂号、要准备哪些保险信息。",
                    "如果你也是第一次，可以先问问大家是怎么描述症状的，通常能减少第一次就诊的紧张感。",
                ]
            if ui_language == "Spanish":
                return [
                    "En mi primera cita de primary care, lo que más me ayudó fue ver cómo se registró otra gente y qué datos del seguro preparó.",
                    "Si también es tu primera vez, preguntar cómo describió otra gente sus síntomas puede quitar bastante nervio.",
                ]
            return [
                "For my first primary care visit, the most helpful part was hearing how other people handled registration and what insurance details they prepared.",
                "If it is also your first time, asking how other people described their symptoms can make the visit feel a lot less intimidating.",
            ]

        if ui_language == "Mandarin":
            return [
                "这个房间里最有价值的通常不是“标准答案”，而是别人当时怎么判断第一步、哪里最卡住。",
                "如果你愿意，先说说你现在最犹豫的是保险、医生选择，还是预约流程，别人通常会更容易接上你的问题。",
            ]
        if ui_language == "Spanish":
            return [
                "Lo más valioso aquí no suele ser una respuesta perfecta, sino escuchar cómo otras personas decidieron su primer paso.",
                "Si quieres, empieza contando si tu duda principal es el seguro, el doctor o la reserva; así otras personas podrán responder mejor.",
            ]
        return [
            "The most useful thing here usually is not a perfect answer, but hearing how other people made their first decision.",
            "If you want, start by saying whether the sticking point is insurance, choosing a doctor, or booking; people can respond more directly.",
        ]

    def _starter_topics(self, ui_language: str) -> list[str]:
        if ui_language == "Mandarin":
            return [
                "你当时先去了哪种诊所或 care path，为什么？",
                "预约或保险里最让你困惑的一步是什么？",
                "第一次就诊前你觉得最该准备什么？",
            ]
        if ui_language == "Spanish":
            return [
                "¿A qué tipo de clínica fuiste primero y por qué?",
                "¿Qué parte del seguro o la reserva fue la más confusa?",
                "¿Qué te habría gustado preparar antes de la primera visita?",
            ]
        return [
            "What kind of clinic did you choose first, and why?",
            "What part of insurance or booking felt most confusing?",
            "What do you wish you had prepared before the first visit?",
        ]

    def _preview_topics(
        self,
        ui_language: str,
        key: str,
        symptom_tags: list[str],
        care_path: str,
    ) -> list[str]:
        normalized_tags = {tag.strip().lower() for tag in symptom_tags}
        if ui_language == "Mandarin":
            if key == "booking-prep":
                return ["预约流程", "到诊准备", "官方预约入口"]
            if key == "doctor-choice":
                return ["医生对比", "语言沟通", "保险匹配"]
            if key == "insurance-questions":
                return ["copay 困惑", "network 核对", "referral 经验"]
            if key == "urgent-next-step":
                return ["下一步去哪里", "urgent care 经验", "何时尽快就诊"]
            if "sore-throat" in normalized_tags or "cough" in normalized_tags or "fever" in normalized_tags:
                return ["感冒症状第一步", "喉咙痛经验", "发烧与咳嗽"]
            if "headache" in normalized_tags or "fatigue" in normalized_tags:
                return ["头痛经验", "疲劳与注意力", "先看哪一类门诊"]
            if "stomach" in normalized_tags:
                return ["恶心与胃痛", "饮食准备", "先看普通门诊还是 urgent care"]
            if care_path == "Primary care":
                return ["首次 primary care", "挂号流程", "看诊前准备"]
            return ["相似病程经验", "诊所选择", "看诊前准备"]

        if ui_language == "Spanish":
            if key == "booking-prep":
                return ["pasos de reserva", "preparacion para la visita", "enlace oficial"]
            if key == "doctor-choice":
                return ["comparar doctores", "comunicacion", "ajuste con seguro"]
            if key == "insurance-questions":
                return ["dudas de copago", "verificar red", "experiencias con referidos"]
            if key == "urgent-next-step":
                return ["siguiente paso", "experiencias en urgent care", "cuando ir pronto"]
            if "sore-throat" in normalized_tags or "cough" in normalized_tags or "fever" in normalized_tags:
                return ["primer paso con resfriado", "dolor de garganta", "fiebre y tos"]
            if "headache" in normalized_tags or "fatigue" in normalized_tags:
                return ["dolor de cabeza", "fatiga", "que tipo de clinica ayuda"]
            if "stomach" in normalized_tags:
                return ["nausea y estomago", "que comer antes", "clinic o urgent care"]
            if care_path == "Primary care":
                return ["primera visita primaria", "registro", "que preparar"]
            return ["experiencias parecidas", "elegir clinica", "que preparar"]

        if key == "booking-prep":
            return ["booking steps", "visit prep", "official handoff"]
        if key == "doctor-choice":
            return ["doctor comparison", "communication style", "insurance fit"]
        if key == "insurance-questions":
            return ["copay confusion", "network check", "referral stories"]
        if key == "urgent-next-step":
            return ["next-step decisions", "urgent care timing", "when to act quickly"]
        if "sore-throat" in normalized_tags or "cough" in normalized_tags or "fever" in normalized_tags:
            return ["cold first steps", "sore throat stories", "fever and cough"]
        if "headache" in normalized_tags or "fatigue" in normalized_tags:
            return ["headache experiences", "fatigue questions", "which clinic helped"]
        if "stomach" in normalized_tags:
            return ["nausea and stomach pain", "what helped first", "clinic vs urgent care"]
        if care_path == "Primary care":
            return ["first primary care visit", "registration tips", "what to prepare"]
        return ["similar journeys", "clinic choices", "visit prep"]

    def _safety_notice(self, ui_language: str) -> str:
        if ui_language == "Mandarin":
            return "这个房间用于分享经验，不用于诊断、处方或紧急医疗建议。"
        if ui_language == "Spanish":
            return "Esta sala es para compartir experiencias, no para dar diagnósticos, recetas ni consejo médico urgente."
        return "This room is for shared experience, not diagnosis, prescriptions, or urgent medical advice."

    def _moderation_notice(self, ui_language: str) -> str:
        if ui_language == "Mandarin":
            return "请不要分享电话号码、邮箱、处方剂量或他人的隐私信息。"
        if ui_language == "Spanish":
            return "No compartas teléfonos, correos, dosis de medicamentos ni información privada de otras personas."
        return "Please do not share phone numbers, email addresses, medication dosing, or other people's private details."

    def _entry_prompt(self, ui_language: str, room: CommunityRoomSummary) -> str:
        if ui_language == "Mandarin":
            return f"你现在在 {room.title}。先说说你是怎么判断该去哪里看诊的，通常最能帮助后来的人。"
        if ui_language == "Spanish":
            return f"Ahora estás en {room.title}. Empezar contando cómo decidiste dónde buscar atención suele ayudar más a las personas nuevas."
        return (
            f"You are now in {room.title}. A helpful first message is how you decided where to seek care and what felt unclear at the beginning."
        )

    def _matching_summary(
        self,
        ui_language: str,
        room: CommunityRoomSummary,
        symptom_text: str | None,
    ) -> str:
        topic = room.symptom_tags[0]
        if ui_language == "Mandarin":
            symptom_part = f" 我们也参考了“{topic}”这一类症状经验来做匹配。" if symptom_text else ""
            return (
                f"这个房间按 {room.urgency_band}、{room.care_path}、{room.language} 和 {room.region} 做了分组。"
                f"{symptom_part}"
            )
        if ui_language == "Spanish":
            symptom_part = (
                f" También usamos experiencias relacionadas con {topic} para acercar mejor la coincidencia."
                if symptom_text
                else ""
            )
            return (
                f"Esta sala se agrupó por {room.urgency_band.lower()}, {room.care_path.lower()}, {room.language} y {room.region}."
                f"{symptom_part}"
            )
        symptom_part = (
            f" We also loosely matched on {topic}-style symptom experience."
            if symptom_text
            else ""
        )
        return (
            f"This room is grouped by {room.urgency_band.lower()} urgency, {room.care_path.lower()}, {room.language}, and {room.region}."
            f"{symptom_part}"
        )

    def _localize_care_path(self, care_path: str, ui_language: str) -> str:
        normalized = care_path.strip().lower()
        if ui_language == "Mandarin":
            mapping = {
                "urgent care": "紧急门诊",
                "primary care": "初级保健",
                "specialist follow-up": "专科后续就诊",
                "general care": "一般就诊",
            }
            return mapping.get(normalized, care_path)
        if ui_language == "Spanish":
            mapping = {
                "urgent care": "atencion urgente",
                "primary care": "atencion primaria",
                "specialist follow-up": "seguimiento con especialista",
                "general care": "atencion general",
            }
            return mapping.get(normalized, care_path)
        return care_path

    def _localize_urgency(self, urgency_band: str, ui_language: str) -> str:
        normalized = urgency_band.strip().lower()
        if ui_language == "Mandarin":
            mapping = {
                "emergency": "急诊",
                "urgent": "尽快",
                "soon": "尽快安排",
                "routine": "常规",
                "self-care": "居家观察",
            }
            return mapping.get(normalized, urgency_band)
        if ui_language == "Spanish":
            mapping = {
                "emergency": "emergencia",
                "urgent": "urgente",
                "soon": "pronto",
                "routine": "rutina",
                "self-care": "autocuidado",
            }
            return mapping.get(normalized, urgency_band)
        return urgency_band

    def _localize_language_name(self, language: str, ui_language: str) -> str:
        normalized = language.strip().lower()
        if ui_language == "Mandarin":
            mapping = {
                "english": "英语",
                "mandarin": "中文",
                "spanish": "西班牙语",
            }
            return mapping.get(normalized, language)
        if ui_language == "Spanish":
            mapping = {
                "english": "ingles",
                "mandarin": "mandarin",
                "spanish": "espanol",
            }
            return mapping.get(normalized, language)
        return language

    def _localize_symptom_tag(self, tag: str, ui_language: str) -> str:
        normalized = tag.strip().lower()
        if ui_language == "Mandarin":
            mapping = {
                "sore-throat": "喉咙痛",
                "fever": "发烧",
                "headache": "头痛",
                "stomach": "肠胃不适",
                "cough": "咳嗽",
                "fatigue": "疲劳",
                "rash": "皮疹",
                "general-care": "一般就诊",
            }
            return mapping.get(normalized, tag)
        if ui_language == "Spanish":
            mapping = {
                "sore-throat": "dolor de garganta",
                "fever": "fiebre",
                "headache": "dolor de cabeza",
                "stomach": "molestias estomacales",
                "cough": "tos",
                "fatigue": "fatiga",
                "rash": "sarpullido",
                "general-care": "atencion general",
            }
            return mapping.get(normalized, tag.replace("-", " "))
        return tag.replace("-", " ").title()

    def _sanitize_message(self, content: str) -> str:
        sanitized = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[contact removed]", content.strip())
        sanitized = re.sub(
            r"(\+?1[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
            "[phone removed]",
            sanitized,
        )
        return sanitized[:1200]
