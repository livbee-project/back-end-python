"""
Chat 도메인 스키마
채팅 관련 요청/응답
"""
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.models.chat import ChatMessageType


class ChatRoomCreateRequest(BaseModel):
    campaign_id: str = Field(..., alias="campaignId")
    showhost_user_id: Optional[str] = Field(None, alias="showhostUserId")
    application_id: Optional[str] = Field(None, alias="applicationId")

    class Config:
        populate_by_name = True


class ChatMessageCreateRequest(BaseModel):
    content: str
    message_type: Optional[ChatMessageType] = Field(ChatMessageType.TEXT, alias="messageType")
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True


class ChatReadRequest(BaseModel):
    last_message_id: Optional[str] = Field(None, alias="lastMessageId")

    class Config:
        populate_by_name = True
