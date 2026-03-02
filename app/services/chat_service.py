"""
채팅 서비스 로직
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.chat import (
    ChatParticipant,
    ChatParticipantRole,
    ChatRoom,
    ChatRoomStatus,
)


def ensure_chat_room(
    db: Session,
    *,
    campaign_id: str,
    brand_user_id: str,
    showhost_user_id: str,
    application_id: Optional[str] = None,
) -> ChatRoom:
    """
    캠페인/참가자 조합으로 채팅방을 조회하거나 생성
    """
    room = (
        db.query(ChatRoom)
        .filter(
            ChatRoom.campaign_id == campaign_id,
            ChatRoom.brand_user_id == brand_user_id,
            ChatRoom.showhost_user_id == showhost_user_id,
        )
        .first()
    )

    if room:
        if application_id and not room.application_id:
            room.application_id = application_id
        return room

    now = datetime.now(timezone.utc)
    room = ChatRoom(
        id=str(uuid.uuid4()),
        campaign_id=campaign_id,
        brand_user_id=brand_user_id,
        showhost_user_id=showhost_user_id,
        application_id=application_id,
        status=ChatRoomStatus.ACTIVE,
        last_message_at=now,
    )
    db.add(room)
    db.flush()

    _ensure_participant(
        db,
        room_id=room.id,
        user_id=brand_user_id,
        role=ChatParticipantRole.BRAND,
        last_read_at=now,
    )
    _ensure_participant(
        db,
        room_id=room.id,
        user_id=showhost_user_id,
        role=ChatParticipantRole.SHOWHOST,
    )
    return room


def _ensure_participant(
    db: Session,
    *,
    room_id: str,
    user_id: str,
    role: ChatParticipantRole,
    last_read_at: Optional[datetime] = None,
) -> ChatParticipant:
    participant = (
        db.query(ChatParticipant)
        .filter(
            ChatParticipant.room_id == room_id,
            ChatParticipant.user_id == user_id,
        )
        .first()
    )
    if participant:
        return participant

    participant = ChatParticipant(
        id=str(uuid.uuid4()),
        room_id=room_id,
        user_id=user_id,
        role=role,
        last_read_at=last_read_at,
    )
    db.add(participant)
    return participant
