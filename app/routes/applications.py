"""
Application 라우트
지원서 관리
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from datetime import date, datetime, timezone
from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.role import require_role
from app.models.application import Application, ApplicationStatus
from app.models.campaign import Campaign
from app.models.user import User, UserRole
from app.models.chat import ChatRoom, ChatMessage, ChatMessageType
from app.models.portfolio import Portfolio
from app.utils.response import success_response, fail_response
from app.services.chat_service import ensure_chat_room
import uuid

router = APIRouter(prefix="/applications", tags=["applications"])


class ApplicationCreate(BaseModel):
    campaign_id: str = Field(..., alias="campaignId")
    profile_ref: Optional[str] = Field(None, alias="portfolioId")
    message: Optional[str] = None
    available_date: Optional[date] = Field(None, alias="availableDate")
    available_time: Optional[str] = Field(None, alias="availableTime")

    class Config:
        populate_by_name = True


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


@router.get("/mine")
async def get_my_application(
    campaign_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    내 지원 단건 조회
    """
    user_id = current_user.get("sub")

    application = db.query(Application).filter(
        Application.campaign_id == campaign_id,
        Application.user_id == user_id
    ).first()

    if not application:
        return success_response({"data": None})

    data = {"id": application.id, **{k: v for k, v in application.__dict__.items() if not k.startswith("_")}}
    return success_response({"data": data})


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_application(
    request: ApplicationCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    지원 생성
    """
    user_id = current_user.get("sub")

    # 캠페인 확인
    campaign = db.query(Campaign).filter(Campaign.id == request.campaign_id).first()
    if not campaign:
        return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND)

    # 마감일 확인
    if campaign.close_at < date.today():
        return fail_response("DEADLINE_PASSED", status.HTTP_409_CONFLICT)

    # 중복 지원 확인
    existing = db.query(Application).filter(
        Application.campaign_id == request.campaign_id,
        Application.user_id == user_id
    ).first()

    if existing:
        return fail_response("ALREADY_APPLIED", status.HTTP_409_CONFLICT)

    # 지원서 생성
    application = Application(
        id=str(uuid.uuid4()),
        campaign_id=request.campaign_id,
        user_id=user_id,
        profile_ref=request.profile_ref,
        message=request.message,
        status=ApplicationStatus.SUBMITTED
    )

    db.add(application)
    db.flush()

    chat_room = ensure_chat_room(
        db,
        campaign_id=campaign.id,
        brand_user_id=campaign.created_by,
        showhost_user_id=user_id,
        application_id=application.id,
    )

    db.commit()
    db.refresh(application)
    db.refresh(chat_room)

    data = {"id": application.id, **{k: v for k, v in application.__dict__.items() if not k.startswith("_")}}
    return success_response(
        {"data": data, "chatRoomId": chat_room.id},
        status_code=status.HTTP_201_CREATED,
    )


@router.get("")
async def get_applications(
    campaign_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 캠페인 지원자 목록 (오너/관리자 전용)
    """
    user_id = current_user.get("sub")

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND)

    # 오너 확인
    is_owner = campaign.created_by == user_id
    if not is_owner and current_user.get("role") != "admin":
        return fail_response("FORBIDDEN", status.HTTP_403_FORBIDDEN)

    applications = db.query(Application).filter(
        Application.campaign_id == campaign_id
    ).order_by(desc(Application.created_at)).all()

    items = [{"id": app.id, **{k: v for k, v in app.__dict__.items() if not k.startswith("_")}} for app in applications]
    return success_response({"items": items})


@router.patch("/{application_id}")
async def update_application_status(
    application_id: str,
    request: ApplicationStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    지원서 상태 변경 (오너/관리자 전용)
    """
    user_id = current_user.get("sub")

    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND)

    campaign = db.query(Campaign).filter(Campaign.id == application.campaign_id).first()
    if not campaign:
        return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND)

    # 오너 확인
    is_owner = campaign.created_by == user_id
    if not is_owner and current_user.get("role") != "admin":
        return fail_response("FORBIDDEN", status.HTTP_403_FORBIDDEN)

    old_status = application.status
    application.status = request.status
    db.commit()
    db.refresh(application)

    # 채팅방 조회
    chat_room = (
        db.query(ChatRoom)
        .filter(ChatRoom.application_id == application_id)
        .first()
    )

    # WebSocket 이벤트 전송
    if chat_room:
        await _send_application_status_update(db, application, campaign, chat_room.id)

        # 수락 시 결제 요청 메시지 생성 및 전송
        if request.status == ApplicationStatus.ACCEPTED and old_status != ApplicationStatus.ACCEPTED:
            await _create_payment_request_message(db, application, campaign, user_id, chat_room.id)

    # 응답 형식
    response_data = {
        "applicationId": application.id,
        "status": "accepted" if request.status == ApplicationStatus.ACCEPTED else (
            "rejected" if request.status == ApplicationStatus.REJECTED else "pending"
        ),
    }
    
    if request.status == ApplicationStatus.ACCEPTED:
        response_data["paymentRequest"] = {
            "amount": float(campaign.fee) if campaign.fee else 0,
            "currency": "KRW",
        }

    return success_response({"data": response_data})


@router.post("/{application_id}/accept")
async def accept_application(
    application_id: str,
    current_user: dict = Depends(require_role(UserRole.BRAND.value, "admin")),
    db: Session = Depends(get_db)
):
    """
    지원서 수락 (브랜드/관리자 전용)
    """
    return await _update_application_status_internal(
        application_id, ApplicationStatus.ACCEPTED, current_user, db
    )


@router.post("/{application_id}/reject")
async def reject_application(
    application_id: str,
    current_user: dict = Depends(require_role(UserRole.BRAND.value, "admin")),
    db: Session = Depends(get_db)
):
    """
    지원서 거절 (브랜드/관리자 전용)
    """
    return await _update_application_status_internal(
        application_id, ApplicationStatus.REJECTED, current_user, db
    )


async def _update_application_status_internal(
    application_id: str,
    new_status: ApplicationStatus,
    current_user: dict,
    db: Session
):
    """지원서 상태 변경 내부 함수"""
    user_id = current_user.get("sub")

    application = (
        db.query(Application)
        .options(joinedload(Application.campaign))
        .filter(Application.id == application_id)
        .first()
    )
    if not application:
        return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND)

    campaign = application.campaign
    if not campaign:
        return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND)

    # 오너 확인
    is_owner = campaign.created_by == user_id
    if not is_owner and current_user.get("role") != "admin":
        return fail_response("FORBIDDEN", status.HTTP_403_FORBIDDEN)

    old_status = application.status
    application.status = new_status
    db.commit()
    db.refresh(application)

    # 채팅방 조회
    chat_room = (
        db.query(ChatRoom)
        .filter(ChatRoom.application_id == application_id)
        .first()
    )

    # WebSocket 이벤트 전송
    if chat_room:
        await _send_application_status_update(db, application, campaign, chat_room.id)

        # 수락 시 결제 요청 메시지 생성 및 전송
        if new_status == ApplicationStatus.ACCEPTED and old_status != ApplicationStatus.ACCEPTED:
            await _create_payment_request_message(db, application, campaign, user_id, chat_room.id)

    # 응답 형식
    response_data = {
        "applicationId": application.id,
        "status": "accepted" if new_status == ApplicationStatus.ACCEPTED else "rejected",
    }
    
    if new_status == ApplicationStatus.ACCEPTED:
        response_data["paymentRequest"] = {
            "amount": float(campaign.fee) if campaign.fee else 0,
            "currency": "KRW",
        }

    return success_response({"data": response_data})


async def _send_application_status_update(
    db: Session,
    application: Application,
    campaign: Campaign,
    room_id: Optional[str] = None
):
    """지원서 상태 변경 WebSocket 이벤트 전송"""
    # 순환 참조 방지를 위해 함수 내부에서 import
    from app.routes.chat import connection_manager
    
    if not room_id:
        chat_room = (
            db.query(ChatRoom)
            .filter(ChatRoom.application_id == application.id)
            .first()
        )
        if not chat_room:
            return
        room_id = chat_room.id

    # 포트폴리오 정보 조회
    portfolio_title = None
    if application.profile_ref:
        portfolio = db.query(Portfolio).filter(Portfolio.id == application.profile_ref).first()
        if portfolio:
            portfolio_title = portfolio.nickname or portfolio.one_line_intro

    # 상태 매핑
    status_map = {
        ApplicationStatus.SUBMITTED: "pending",
        ApplicationStatus.REVIEWING: "pending",
        ApplicationStatus.SHORTLISTED: "pending",
        ApplicationStatus.ACCEPTED: "accepted",
        ApplicationStatus.REJECTED: "rejected",
    }
    mapped_status = status_map.get(application.status, "pending")

    payload = {
        "application": {
            "applicationId": application.id,
            "status": mapped_status,
            "campaignTitle": campaign.title,
            "portfolioTitle": portfolio_title,
            "availableDate": None,  # DB에 저장되지 않음
            "availableTime": None,  # DB에 저장되지 않음
            "message": application.message,
        }
    }

    await connection_manager.broadcast(
        room_id,
        {"type": "application.status.updated", "payload": payload},
        exclude_user_id=None,
    )


async def _create_payment_request_message(
    db: Session,
    application: Application,
    campaign: Campaign,
    brand_user_id: str,
    room_id: Optional[str] = None
):
    """결제 요청 메시지 생성 및 전송"""
    # 순환 참조 방지를 위해 함수 내부에서 import
    from app.routes.chat import connection_manager, _message_payload
    
    if not room_id:
        chat_room = (
            db.query(ChatRoom)
            .filter(ChatRoom.application_id == application.id)
            .first()
        )
        if not chat_room:
            return
        room_id = chat_room.id

    # 브랜드 사용자 정보 조회
    brand_user = db.query(User).filter(User.id == brand_user_id).first()
    if not brand_user:
        return

    # 결제 요청 메시지 생성
    now = datetime.now(timezone.utc)
    message = ChatMessage(
        id=str(uuid.uuid4()),
        room_id=room_id,
        sender_id=brand_user_id,
        message_type=ChatMessageType.SYSTEM,
        content="결제 요청",
        extra_metadata={
            "type": "payment_request",
            "applicationId": application.id,
            "amount": float(campaign.fee) if campaign.fee else 0,
            "campaignTitle": campaign.title,
            "availableDate": None,  # DB에 저장되지 않음
            "availableTime": None,  # DB에 저장되지 않음
        },
    )
    db.add(message)
    db.flush()

    # 채팅방 정보 업데이트
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if chat_room:
        chat_room.last_message_id = message.id
        chat_room.last_message_at = now

    db.commit()
    db.refresh(message)

    # 메시지 전송 이벤트
    created_message = (
        db.query(ChatMessage)
        .options(joinedload(ChatMessage.sender))
        .filter(ChatMessage.id == message.id)
        .first()
    )
    
    if created_message:
        payload = _message_payload(created_message)
        await connection_manager.broadcast(
            room_id,
            {"type": "message.new", "payload": {"message": payload}},
            exclude_user_id=None,
        )

