from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from app.core.config import get_settings
from app.models.user import User
from app.repositories.community_repo import CommunityRepository
from app.schemas.community import (
    CommunityCreateRoomRequest,
    CommunityDiscoverRequest,
    CommunityJoinRequest,
    CommunityMatchRequest,
    CommunityMessageRequest,
)
from app.services.community_service import CommunityService


def build_test_service(tmp_path: Path) -> CommunityService:
    settings = replace(
        get_settings(),
        community_rooms_file=tmp_path / "community_rooms.json",
    )
    return CommunityService(CommunityRepository(settings))


def test_similar_users_join_same_room_and_share_messages(tmp_path: Path) -> None:
    service = build_test_service(tmp_path)
    user_a = User(id="user-a", name="Alice", email="alice@example.com")
    user_b = User(id="user-b", name="Bruno", email="bruno@example.com")
    request = CommunityMatchRequest(
        symptom_text="I have a sore throat, cough, and mild fever.",
        care_path="primary_care",
        urgency_band="soon",
        preferred_language="English",
        region="Los Angeles",
        ui_language="English",
    )

    first_room = service.match_room(user_a, request)
    second_room = service.match_room(user_b, request)

    assert first_room.room.id == second_room.room.id
    assert second_room.room.member_count == 2
    assert second_room.your_alias != first_room.your_alias

    updated_room = service.post_message(
        user_a,
        first_room.room.id,
        CommunityMessageRequest(
            content="Urgent care ended up being slower than expected, but the clinic accepted walk-ins.",
            ui_language="English",
        ),
    )

    assert updated_room.room.message_count >= 2
    assert any("walk-ins" in message.content for message in updated_room.messages)

    refreshed_room = service.get_room(user_b, first_room.room.id, ui_language="English")

    assert refreshed_room.room.member_count == 2
    assert any(message.display_name == first_room.your_alias for message in refreshed_room.messages)
    assert refreshed_room.safety_notice
    assert refreshed_room.starter_topics


def test_discover_rooms_and_join_selected_room(tmp_path: Path) -> None:
    service = build_test_service(tmp_path)
    user = User(id="user-a", name="Alice", email="alice@example.com")
    catalog = service.discover_rooms(
        CommunityDiscoverRequest(
            symptom_text="I have a sore throat, fever, and cold symptoms.",
            care_path="general_care",
            urgency_band="routine",
            preferred_language="English",
            region="Los Angeles",
            ui_language="English",
        )
    )

    assert catalog.recommended_rooms
    assert catalog.browse_rooms
    assert "recommend rooms first" in catalog.selected_context_summary
    assert catalog.recommended_rooms[0].preview_topics

    selected_room = catalog.recommended_rooms[0]
    joined_room = service.join_room(
        user,
        selected_room.id,
        CommunityJoinRequest(
            symptom_text="I have a sore throat, fever, and cold symptoms.",
            care_path="general_care",
            urgency_band="routine",
            preferred_language="English",
            region="Los Angeles",
            ui_language="English",
        ),
    )

    assert joined_room.room.id == selected_room.id
    assert joined_room.room.member_count == 1
    assert joined_room.room.title
    assert joined_room.room.preview_topics
    assert joined_room.messages[0].display_name == "Room Guide"


def test_room_strings_localize_to_current_ui_language(tmp_path: Path) -> None:
    service = build_test_service(tmp_path)
    user = User(id="user-a", name="Alice", email="alice@example.com")
    request = CommunityMatchRequest(
        symptom_text="I have a sore throat and mild fever.",
        care_path="general_care",
        urgency_band="routine",
        preferred_language="Mandarin",
        region="Los Angeles",
        ui_language="English",
    )

    room = service.match_room(user, request)
    localized_room = service.get_room(user, room.room.id, ui_language="Mandarin")

    assert "经验交流" in localized_room.room.title
    assert localized_room.room.care_path == "一般就诊"
    assert localized_room.room.urgency_band == "常规"
    assert localized_room.room.language == "中文"
    assert localized_room.messages[0].display_name == "房间向导"
    assert "欢迎来到匿名互助讨论室" in localized_room.messages[0].content
    assert localized_room.matching_summary.startswith("这个房间按")


def test_create_room_is_saved_and_seeded(tmp_path: Path) -> None:
    service = build_test_service(tmp_path)
    owner = User(id="owner-1", name="Ava", email="ava@example.com")

    created = service.create_room(
        owner,
        CommunityCreateRoomRequest(
            title="Student plan confusion before first visit",
            focus="I want a room for people comparing student insurance, first primary care visits, and what to prepare before booking.",
            symptom_text="sore throat and student insurance confusion",
            care_path="primary_care",
            urgency_band="routine",
            preferred_language="English",
            region="Los Angeles",
            ui_language="English",
        ),
    )

    assert created.room.title == "Student plan confusion before first visit"
    assert created.room.description
    assert created.room.member_count == 1
    assert created.room.message_count >= 3
    assert any(message.user_id.startswith("peer-") for message in created.messages)

    catalog = service.discover_rooms(
        CommunityDiscoverRequest(
            preferred_language="English",
            region="Los Angeles",
            ui_language="English",
        )
    )

    assert any(
        room.id == created.room.id and room.title == created.room.title
        for room in catalog.browse_rooms
    )
