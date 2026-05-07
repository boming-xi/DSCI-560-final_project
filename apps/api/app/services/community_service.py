from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.models.user import User
from app.repositories.community_repo import CommunityRepository
from app.schemas.community import (
    CommunityMatchRequest,
    CommunityMessage,
    CommunityMessageRequest,
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


class CommunityService:
    def __init__(self, repo: CommunityRepository) -> None:
        self.repo = repo

    def match_room(self, user: User, request: CommunityMatchRequest) -> CommunityRoomResponse:
        match = self._match_room_descriptor(request)
        rooms = self.repo.load_rooms()
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

    def get_room(self, user: User, room_id: str, ui_language: str | None = None) -> CommunityRoomResponse:
        rooms = self.repo.load_rooms()
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
            "memberships": [],
            "messages": [
                {
                    "id": "msg-welcome",
                    "user_id": "moderator",
                    "display_name": "Room Guide",
                    "content": self._seed_message(match.language),
                    "created_at": now,
                }
            ],
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
        localized_title = self._room_title(
            ui_language,
            str(room["urgency_band"]),
            str(room["care_path"]),
            [str(tag) for tag in room.get("symptom_tags", [])],
            str(room["region"]),
        )
        messages = [
            CommunityMessage(
                id=message["id"],
                user_id=message["user_id"],
                display_name=(
                    self._moderator_display_name(ui_language)
                    if message["user_id"] == "moderator"
                    else message["display_name"]
                ),
                content=(
                    self._seed_message(ui_language)
                    if message["user_id"] == "moderator" and message["id"] == "msg-welcome"
                    else message["content"]
                ),
                created_at=datetime.fromisoformat(message["created_at"]),
                is_current_user=message["user_id"] == user.id,
            )
            for message in room.get("messages", [])
        ]
        summary = CommunityRoomSummary(
            id=room["id"],
            title=localized_title,
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

    def _seed_message(self, ui_language: str) -> str:
        if ui_language == "Mandarin":
            return "欢迎来到匿名互助讨论室。这里适合分享就医流程、保险体验、预约经验和看诊前准备，不适合替别人下诊断。"
        if ui_language == "Spanish":
            return "Bienvenido al espacio anónimo de apoyo. Comparte experiencias sobre clínicas, seguro, reservas y preparación para la visita, no diagnósticos."
        return "Welcome to the anonymous support room. Share care navigation, insurance, booking, and preparation experiences here, not diagnoses."

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
