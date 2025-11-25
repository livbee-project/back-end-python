"""
채팅 관련 모델 정의
"""
import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Enum as SQLEnum,
    DateTime,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ChatRoomStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class ChatMessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    SYSTEM = "system"


class ChatMessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


class ChatParticipantRole(str, enum.Enum):
    BRAND = "brand"
    SHOWHOST = "showhost"


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(String, primary_key=True, default=_uuid)
    campaign_id = Column(String, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    showhost_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(String, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(SQLEnum(ChatRoomStatus), nullable=False, default=ChatRoomStatus.ACTIVE)
    last_message_id = Column(String, ForeignKey("chat_messages.id", ondelete="SET NULL"), nullable=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    campaign = relationship("Campaign", back_populates="chat_rooms")
    brand_user = relationship("User", foreign_keys=[brand_user_id], back_populates="brand_chat_rooms")
    showhost_user = relationship("User", foreign_keys=[showhost_user_id], back_populates="showhost_chat_rooms")
    application = relationship("Application", back_populates="chat_room", foreign_keys=[application_id])
    last_message = relationship("ChatMessage", foreign_keys=[last_message_id], post_update=True)
    participants = relationship("ChatParticipant", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan", foreign_keys="ChatMessage.room_id")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=_uuid)
    room_id = Column(String, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    message_type = Column(SQLEnum(ChatMessageType), nullable=False, default=ChatMessageType.TEXT)
    content = Column(Text, nullable=False)
    extra_metadata = Column("metadata", JSON, nullable=True)
    status = Column(SQLEnum(ChatMessageStatus), nullable=False, default=ChatMessageStatus.SENT)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=func.now(), nullable=False)

    room = relationship("ChatRoom", back_populates="messages", foreign_keys=[room_id])
    sender = relationship("User", foreign_keys=[sender_id])


class ChatParticipant(Base):
    __tablename__ = "chat_participants"

    id = Column(String, primary_key=True, default=_uuid)
    room_id = Column(String, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(SQLEnum(ChatParticipantRole), nullable=False)
    last_read_message_id = Column(String, ForeignKey("chat_messages.id", ondelete="SET NULL"), nullable=True)
    last_read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    room = relationship("ChatRoom", back_populates="participants", foreign_keys=[room_id])
    user = relationship("User", back_populates="chat_participations", foreign_keys=[user_id])
    last_read_message = relationship("ChatMessage", foreign_keys=[last_read_message_id])


