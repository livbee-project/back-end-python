"""
채팅 REST & WebSocket 라우트
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List
import uuid

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
    WebSocket,
    WebSocketDisconnect,
)
from starlette.websockets import WebSocketState
from pydantic import BaseModel, Field
from sqlalchemy import func, desc
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db, SessionLocal
from app.core.security import decode_token
from app.middleware.role import require_role
from app.models.user import User, UserRole
from app.models.campaign import Campaign
from app.models.application import Application, ApplicationStatus
from app.models.portfolio import Portfolio
from app.models.model import Model
from app.models.chat import ChatRoom, ChatParticipant, ChatMessage, ChatMessageType, ChatRoomStatus
from app.services.chat_service import ensure_chat_room
from app.utils.response import success_response, fail_response

router = APIRouter(prefix="/chat", tags=["chat"])


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


class ChatConnectionManager:
    """WebSocket 연결 관리"""

    def __init__(self):
        self._connections: Dict[str, Dict[str, WebSocket]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    async def connect(self, room_id: str, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if room_id not in self._connections:
            self._connections[room_id] = {}
        self._connections[room_id][user_id] = websocket
        if room_id not in self._locks:
            self._locks[room_id] = asyncio.Lock()

    def disconnect(self, room_id: str, user_id: str) -> None:
        room = self._connections.get(room_id)
        if not room:
            return
        websocket = room.pop(user_id, None)
        if websocket and websocket.application_state == WebSocketState.CONNECTED:
            try:
                asyncio.create_task(websocket.close())
            except RuntimeError:
                pass
        if not room:
            self._connections.pop(room_id, None)
            self._locks.pop(room_id, None)

    async def broadcast(
        self,
        room_id: str,
        payload: Dict[str, Any],
        exclude_user_id: Optional[str] = None,
    ) -> None:
        room = self._connections.get(room_id)
        if not room:
            return
        lock = self._locks.get(room_id)
        if lock:
            async with lock:
                await self._send(room_id, payload, exclude_user_id)
        else:
            await self._send(room_id, payload, exclude_user_id)

    async def _send(
        self,
        room_id: str,
        payload: Dict[str, Any],
        exclude_user_id: Optional[str],
    ) -> None:
        room = self._connections.get(room_id, {})
        disconnect_ids: List[str] = []
        for uid, websocket in room.items():
            if exclude_user_id and uid == exclude_user_id:
                continue
            try:
                await websocket.send_json(payload)
            except Exception:
                disconnect_ids.append(uid)
        for uid in disconnect_ids:
            self.disconnect(room_id, uid)


connection_manager = ChatConnectionManager()


def _user_summary(user: Optional[User]) -> Optional[Dict[str, Any]]:
    if not user:
        return None
    role_value = user.role.value if hasattr(user.role, "value") else user.role
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": role_value,
        "brandName": getattr(user, "brand_name", None),
        "nickname": getattr(user, "nickname", None),
    }


def _message_payload(message: ChatMessage) -> Dict[str, Any]:
    return {
        "id": message.id,
        "roomId": message.room_id,
        "senderId": message.sender_id,
        "messageType": message.message_type.value if hasattr(message.message_type, "value") else message.message_type,
        "content": message.content,
        "metadata": message.extra_metadata,
        "status": message.status.value if hasattr(message.status, "value") else message.status,
        "createdAt": message.created_at.isoformat() if message.created_at else None,
        "updatedAt": message.updated_at.isoformat() if message.updated_at else None,
        "sender": _user_summary(message.sender),
    }


def _application_payload(
    application: Optional[Application],
    db: Session,
) -> Optional[Dict[str, Any]]:
    """지원서 정보를 응답 형식으로 변환"""
    if not application:
        return None
    
    # 포트폴리오/모델 정보 조회
    portfolio_title = None
    if application.portfolio_id:
        portfolio = db.query(Portfolio).filter(Portfolio.id == application.portfolio_id).first()
        if portfolio:
            portfolio_title = portfolio.nickname or portfolio.one_line_intro
    elif application.model_id:
        model = db.query(Model).filter(Model.id == application.model_id).first()
        if model:
            portfolio_title = model.nickname or model.one_line_intro
    elif application.profile_ref:  # 하위 호환성
        portfolio = db.query(Portfolio).filter(Portfolio.id == application.profile_ref).first()
        if portfolio:
            portfolio_title = portfolio.nickname or portfolio.one_line_intro
    
    # 상태 매핑 (ApplicationStatus -> 프론트엔드 기대 형식)
    status_map = {
        ApplicationStatus.SUBMITTED: "pending",
        ApplicationStatus.REVIEWING: "pending",
        ApplicationStatus.SHORTLISTED: "pending",
        ApplicationStatus.ACCEPTED: "accepted",
        ApplicationStatus.REJECTED: "rejected",
    }
    status_value = application.status.value if hasattr(application.status, "value") else application.status
    mapped_status = status_map.get(application.status, "pending")
    
    return {
        "applicationId": application.id,
        "campaignTitle": application.campaign.title if application.campaign else None,
        "portfolioTitle": portfolio_title,
        "availableDate": application.available_date.isoformat() if application.available_date else None,
        "availableTime": application.available_time,
        "message": application.message,
        "status": mapped_status,
        "createdAt": application.created_at.isoformat() if application.created_at else None,
    }


def _room_payload(
    room: ChatRoom,
    *,
    current_user_id: str,
    unread_count: int,
) -> Dict[str, Any]:
    me = next((p for p in room.participants if p.user_id == current_user_id), None)
    other = next((p for p in room.participants if p.user_id != current_user_id), None)
    return {
        "roomId": room.id,
        "campaign": {
            "id": room.campaign_id,
            "title": room.campaign.title if room.campaign else None,
            "brandName": room.campaign.brand_name if room.campaign else None,
        },
        "brandUser": _user_summary(room.brand_user),
        "showhostUser": _user_summary(room.showhost_user),
        "lastMessage": _message_payload(room.last_message) if room.last_message else None,
        "createdAt": room.created_at.isoformat() if room.created_at else None,
        "updatedAt": room.last_message_at.isoformat() if room.last_message_at else None,
        "status": room.status.value if hasattr(room.status, "value") else room.status,
        "unreadCount": unread_count,
        "me": {
            "userId": current_user_id,
            "role": me.role.value if me and hasattr(me.role, "value") else (me.role if me else None),
            "lastReadMessageId": me.last_read_message_id if me else None,
            "lastReadAt": me.last_read_at.isoformat() if me and me.last_read_at else None,
        },
        "counterpart": {
            "userId": other.user_id if other else None,
            "role": other.role.value if other and hasattr(other.role, "value") else (other.role if other else None),
        },
    }


def _load_room(db: Session, room_id: str) -> Optional[ChatRoom]:
    return (
        db.query(ChatRoom)
        .options(
            joinedload(ChatRoom.campaign),
            joinedload(ChatRoom.brand_user),
            joinedload(ChatRoom.showhost_user),
            joinedload(ChatRoom.last_message).joinedload(ChatMessage.sender),
            joinedload(ChatRoom.participants).joinedload(ChatParticipant.user),
            joinedload(ChatRoom.application),
        )
        .filter(ChatRoom.id == room_id)
        .first()
    )


def _get_participant(db: Session, room_id: str, user_id: str) -> Optional[ChatParticipant]:
    return (
        db.query(ChatParticipant)
        .filter(ChatParticipant.room_id == room_id, ChatParticipant.user_id == user_id)
        .first()
    )


def _calculate_unread_count(
    db: Session,
    room_id: str,
    participant: Optional[ChatParticipant],
) -> int:
    if not participant:
        return 0
    query = db.query(func.count(ChatMessage.id)).filter(ChatMessage.room_id == room_id)
    if participant.last_read_at:
        query = query.filter(ChatMessage.created_at > participant.last_read_at)
    query = query.filter(ChatMessage.sender_id != participant.user_id)
    return query.scalar() or 0


@router.get("/rooms")
async def list_chat_rooms(
    current_user: dict = Depends(require_role(UserRole.BRAND.value, UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db),
):
    """
    사용자가 참여 중인 채팅방 목록
    """
    user_id = current_user.get("sub")
    rooms = (
        db.query(ChatRoom)
        .join(ChatParticipant, ChatParticipant.room_id == ChatRoom.id)
        .options(
            joinedload(ChatRoom.campaign),
            joinedload(ChatRoom.brand_user),
            joinedload(ChatRoom.showhost_user),
            joinedload(ChatRoom.last_message).joinedload(ChatMessage.sender),
            joinedload(ChatRoom.participants),
        )
        .filter(ChatParticipant.user_id == user_id)
        .order_by(desc(ChatRoom.last_message_at))
        .all()
    )

    items = []
    for room in rooms:
        participant = next((p for p in room.participants if p.user_id == user_id), None)
        unread = _calculate_unread_count(db, room.id, participant)
        items.append(_room_payload(room, current_user_id=user_id, unread_count=unread))

    return success_response({"items": items})


@router.get("/rooms/{room_id}")
async def get_chat_room_history(
    room_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role(UserRole.BRAND.value, UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db),
):
    """
    특정 방의 메시지 히스토리 조회 (페이지네이션)
    """
    user_id = current_user.get("sub")
    participant = _get_participant(db, room_id, user_id)
    if not participant:
        return fail_response("CHAT_ROOM_FORBIDDEN", status.HTTP_403_FORBIDDEN)

    room = _load_room(db, room_id)
    if not room:
        return fail_response("CHAT_ROOM_NOT_FOUND", status.HTTP_404_NOT_FOUND)

    query = (
        db.query(ChatMessage)
        .options(joinedload(ChatMessage.sender))
        .filter(ChatMessage.room_id == room_id)
        .order_by(ChatMessage.created_at.desc())
    )
    total = query.count()
    messages = query.offset((page - 1) * limit).limit(limit).all()
    messages.reverse()

    items = [_message_payload(message) for message in messages]
    unread = _calculate_unread_count(db, room_id, participant)

    # 지원서 정보 조회
    application_payload = None
    if room.application:
        application_payload = _application_payload(room.application, db)

    response_data = {
        "room": _room_payload(room, current_user_id=user_id, unread_count=unread),
        "items": items,
        "pagination": {"page": page, "limit": limit, "total": total},
    }
    
    if application_payload:
        response_data["application"] = application_payload

    return success_response(response_data)


@router.post("/rooms", status_code=status.HTTP_201_CREATED)
async def create_or_get_chat_room(
    request: ChatRoomCreateRequest,
    current_user: dict = Depends(require_role(UserRole.BRAND.value, UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db),
):
    """
    캠페인/참가자 조합으로 채팅방 생성 또는 재사용
    """
    campaign = db.query(Campaign).filter(Campaign.id == request.campaign_id).first()
    if not campaign:
        return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND)

    user_role = current_user.get("role")
    user_id = current_user.get("sub")

    showhost_user_id: Optional[str] = None
    brand_user_id: Optional[str] = None
    application: Optional[Application] = None

    if request.application_id:
        application = (
            db.query(Application)
            .filter(
                Application.id == request.application_id,
                Application.campaign_id == request.campaign_id,
            )
            .first()
        )
        if not application:
            return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND)
        showhost_user_id = application.user_id

    if user_role == UserRole.SHOWHOST.value:
        showhost_user_id = showhost_user_id or user_id
        if request.showhost_user_id and request.showhost_user_id != user_id:
            return fail_response("CHAT_INVALID_PARTICIPANT", status.HTTP_403_FORBIDDEN)
        brand_user_id = campaign.created_by
    elif user_role == UserRole.BRAND.value:
        brand_user_id = user_id
        showhost_user_id = showhost_user_id or request.showhost_user_id
        if not showhost_user_id:
            return fail_response("VALIDATION_MISSING_FIELDS", status.HTTP_422_UNPROCESSABLE_ENTITY)
        if campaign.created_by != user_id:
            return fail_response("CHAT_ROOM_FORBIDDEN", status.HTTP_403_FORBIDDEN)
    else:
        return fail_response("AUTH_FORBIDDEN_ROLE", status.HTTP_403_FORBIDDEN)

    room = ensure_chat_room(
        db,
        campaign_id=request.campaign_id,
        brand_user_id=brand_user_id,
        showhost_user_id=showhost_user_id,
        application_id=request.application_id,
    )

    loaded_room = _load_room(db, room.id)
    participant = _get_participant(db, room.id, user_id)
    unread = _calculate_unread_count(db, room.id, participant)
    return success_response(
        {"data": _room_payload(loaded_room, current_user_id=user_id, unread_count=unread)},
        status_code=status.HTTP_201_CREATED,
    )


@router.post("/rooms/{room_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_chat_message(
    room_id: str,
    request: ChatMessageCreateRequest,
    current_user: dict = Depends(require_role(UserRole.BRAND.value, UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db),
):
    """
    채팅 메시지 전송
    """
    content = request.content.strip()
    if not content:
        return fail_response("CHAT_MESSAGE_EMPTY", status.HTTP_400_BAD_REQUEST)

    user_id = current_user.get("sub")
    participant = _get_participant(db, room_id, user_id)
    if not participant:
        return fail_response("CHAT_ROOM_FORBIDDEN", status.HTTP_403_FORBIDDEN)

    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        return fail_response("CHAT_ROOM_NOT_FOUND", status.HTTP_404_NOT_FOUND)

    now = datetime.now(timezone.utc)
    message = ChatMessage(
        id=str(uuid.uuid4()),
        room_id=room_id,
        sender_id=user_id,
        message_type=request.message_type or ChatMessageType.TEXT,
        content=content,
        extra_metadata=request.metadata,
    )
    db.add(message)
    db.flush()  # 메시지를 먼저 DB에 flush하여 ID 확정

    participant.last_read_message_id = message.id
    participant.last_read_at = now
    room.last_message_id = message.id
    room.last_message_at = now

    created_message = (
        db.query(ChatMessage)
        .options(joinedload(ChatMessage.sender))
        .filter(ChatMessage.id == message.id)
        .first()
    )
    payload = _message_payload(created_message)
    await connection_manager.broadcast(
        room_id,
        {"type": "message.new", "payload": payload},
        exclude_user_id=None,
    )
    return success_response({"data": {"message": payload}}, status_code=status.HTTP_201_CREATED)


@router.post("/rooms/{room_id}/read")
async def mark_chat_room_as_read(
    room_id: str,
    request: ChatReadRequest,
    current_user: dict = Depends(require_role(UserRole.BRAND.value, UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db),
):
    """
    채팅방 읽음 처리
    """
    user_id = current_user.get("sub")
    participant = _get_participant(db, room_id, user_id)
    if not participant:
        return fail_response("CHAT_ROOM_FORBIDDEN", status.HTTP_403_FORBIDDEN)

    message = None
    if request.last_message_id:
        message = (
            db.query(ChatMessage)
            .filter(ChatMessage.id == request.last_message_id, ChatMessage.room_id == room_id)
            .first()
        )
        if not message:
            return fail_response("CHAT_MESSAGE_NOT_FOUND", status.HTTP_404_NOT_FOUND)
        participant.last_read_message_id = message.id
        participant.last_read_at = message.created_at
    else:
        participant.last_read_message_id = None
        participant.last_read_at = datetime.now(timezone.utc)

    payload = {
        "roomId": room_id,
        "userId": user_id,
        "lastReadMessageId": participant.last_read_message_id,
        "lastReadAt": participant.last_read_at.isoformat() if participant.last_read_at else None,
    }
    await connection_manager.broadcast(
        room_id,
        {"type": "message.read", "payload": payload},
        exclude_user_id=None,
    )
    return success_response({"data": payload})


@router.delete("/rooms/{room_id}")
async def delete_chat_room(
    room_id: str,
    current_user: dict = Depends(require_role(UserRole.BRAND.value, UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db),
):
    """
    채팅방 삭제 (하드 삭제: DB 레코드 완전 삭제)
    """
    user_id = current_user.get("sub")
    
    # 채팅방 조회 및 권한 확인
    room = _load_room(db, room_id)
    if not room:
        return fail_response("ROOM_NOT_FOUND", status.HTTP_404_NOT_FOUND, additional_data={"code": "ROOM_NOT_FOUND"})
    
    # 참여자 확인 (권한 체크)
    participant = _get_participant(db, room_id, user_id)
    if not participant:
        return fail_response("FORBIDDEN", status.HTTP_403_FORBIDDEN, additional_data={"code": "FORBIDDEN"})
    
    # 참여자 정보 저장 (WebSocket 이벤트 전송용)
    participant_user_ids = [p.user_id for p in room.participants]
    
    # 하드 삭제: DB 레코드 완전 삭제 (CASCADE로 메시지, 참가자도 자동 삭제됨)
    db.delete(room)
    
    # WebSocket 이벤트 브로드캐스트 (삭제 전에 전송)
    await connection_manager.broadcast(
        room_id,
        {
            "type": "room.deleted",
            "payload": {
                "roomId": room_id,
                "deletedBy": user_id,
            },
        },
        exclude_user_id=None,
    )
    
    # WebSocket 연결 종료
    # 모든 참여자의 연결을 끊음
    for participant_user_id in participant_user_ids:
        connection_manager.disconnect(room_id, participant_user_id)
    
    return success_response({
        "success": True,
        "message": "채팅방이 삭제되었습니다.",
    })


@router.websocket("/{room_id}")
async def websocket_chat(room_id: str, websocket: WebSocket):
    """
    채팅 WebSocket 엔드포인트
    """
    token = websocket.query_params.get("token")
    if not token:
        auth_header = websocket.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1]

    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return

    payload = decode_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid token")
        return

    user_id = payload.get("sub")
    user_role = payload.get("role")
    if not user_id or not user_role:
        await websocket.close(code=1008, reason="Invalid token payload")
        return

    if user_role not in {UserRole.BRAND.value, UserRole.SHOWHOST.value, "admin"}:
        await websocket.close(code=1008, reason="Forbidden role")
        return

    db = SessionLocal()
    try:
        participant = _get_participant(db, room_id, user_id)
        if not participant:
            await websocket.close(code=1008, reason="Forbidden")
            return
    finally:
        db.close()

    await connection_manager.connect(room_id, user_id, websocket)
    await websocket.send_json({"type": "connection", "payload": {"roomId": room_id, "userId": user_id}})

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
    except WebSocketDisconnect:
        connection_manager.disconnect(room_id, user_id)
    except Exception:
        connection_manager.disconnect(room_id, user_id)
        await websocket.close(code=1011, reason="Internal error")


