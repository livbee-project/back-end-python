"""
Application 라우트
지원서 관리
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.role import require_role
from app.models.application import Application, ApplicationStatus
from app.models.campaign import Campaign
from app.models.chat import ChatMessage, ChatMessageType, ChatRoom
from app.models.model import Model
from app.models.portfolio import Portfolio
from app.models.user import User, UserRole
from app.schemas.applications import ApplicationCreate, ApplicationStatusUpdate
from app.services.application_service import (
    create_application as create_application_svc,
)
from app.services.application_service import (
    get_application_by_campaign_and_user,
    get_applications_by_campaign,
)
from app.services.application_service import (
    update_application_status as update_application_status_service,
)
from app.utils.common import model_to_dict, models_to_list
from app.utils.response import success_response

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("/mine")
async def get_my_application(
    campaign_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    내 지원 단건 조회
    """
    user_id = current_user.get("sub")

    application = get_application_by_campaign_and_user(db, campaign_id=campaign_id, user_id=user_id)

    if not application:
        return success_response({"data": None})

    data = model_to_dict(application)
    return success_response({"data": data})


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_application(
    request: ApplicationCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    지원 생성
    """
    user_id = current_user.get("sub")

    # portfolio_id 또는 model_id 우선 사용, 없으면 profile_ref 사용 (하위 호환성)
    portfolio_id = request.portfolio_id
    model_id = request.model_id
    profile_ref = request.profile_ref

    # profile_ref가 있고 portfolio_id/model_id가 없으면 profile_ref를 portfolio_id로 사용 (하위 호환성)
    if profile_ref and not portfolio_id and not model_id:
        portfolio_id = profile_ref

    # 서비스를 통한 지원서 생성
    application = create_application_svc(
        db,
        campaign_id=request.campaign_id,
        user_id=user_id,
        profile_ref=profile_ref,  # 하위 호환성 유지
        portfolio_id=portfolio_id,
        model_id=model_id,
        message=request.message,
        available_date=request.available_date,
        available_time=request.available_time,
    )

    # 채팅방 조회
    chat_room = db.query(ChatRoom).filter(ChatRoom.application_id == application.id).first()

    data = model_to_dict(application)
    return success_response(
        {"data": data, "chatRoomId": chat_room.id if chat_room else None},
        status_code=status.HTTP_201_CREATED,
    )


@router.get("")
async def get_applications(
    campaign_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    특정 캠페인 지원자 목록 (오너/관리자 전용)
    """
    user_id = current_user.get("sub")
    user_role = current_user.get("role")

    # 서비스를 통한 지원서 목록 조회
    applications = get_applications_by_campaign(
        db, campaign_id=campaign_id, user_id=user_id, user_role=user_role
    )

    items = models_to_list(applications)
    return success_response({"items": items})


@router.patch("/{application_id}")
async def update_application_status(
    application_id: str,
    request: ApplicationStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    지원서 상태 변경 (오너/관리자 전용)
    """
    user_id = current_user.get("sub")
    user_role = current_user.get("role")

    # 서비스를 통한 지원서 상태 변경
    application = update_application_status_service(
        db,
        application_id=application_id,
        new_status=request.status,
        user_id=user_id,
        user_role=user_role,
    )

    campaign = application.campaign
    old_status = application.status

    # 채팅방 조회
    chat_room = db.query(ChatRoom).filter(ChatRoom.application_id == application_id).first()

    # WebSocket 이벤트 전송
    if chat_room:
        await _send_application_status_update(db, application, campaign, chat_room.id)

        # 수락 시 결제 요청 메시지 생성 및 전송
        if (
            request.status == ApplicationStatus.ACCEPTED
            and old_status != ApplicationStatus.ACCEPTED
        ):
            await _create_payment_request_message(db, application, campaign, user_id, chat_room.id)

    # 응답 형식
    response_data = {
        "applicationId": application.id,
        "status": (
            "accepted"
            if request.status == ApplicationStatus.ACCEPTED
            else ("rejected" if request.status == ApplicationStatus.REJECTED else "pending")
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
):
    """
    지원서 거절 (브랜드/관리자 전용)
    """
    return await _update_application_status_internal(
        application_id, ApplicationStatus.REJECTED, current_user, db
    )


async def _update_application_status_internal(
    application_id: str, new_status: ApplicationStatus, current_user: dict, db: Session
):
    """지원서 상태 변경 내부 함수"""
    user_id = current_user.get("sub")
    user_role = current_user.get("role")

    # 서비스를 통한 지원서 상태 변경
    application = update_application_status_service(
        db,
        application_id=application_id,
        new_status=new_status,
        user_id=user_id,
        user_role=user_role,
    )

    campaign = application.campaign
    old_status = application.status

    # 채팅방 조회
    chat_room = db.query(ChatRoom).filter(ChatRoom.application_id == application_id).first()

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
    db: Session, application: Application, campaign: Campaign, room_id: Optional[str] = None
):
    """지원서 상태 변경 WebSocket 이벤트 전송"""
    # 순환 참조 방지를 위해 함수 내부에서 import
    from app.routes.chat import connection_manager

    if not room_id:
        chat_room = db.query(ChatRoom).filter(ChatRoom.application_id == application.id).first()
        if not chat_room:
            return
        room_id = chat_room.id

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
            "availableDate": (
                application.available_date.isoformat() if application.available_date else None
            ),
            "availableTime": application.available_time,
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
    room_id: Optional[str] = None,
):
    """결제 요청 메시지 생성 및 전송"""
    # 순환 참조 방지를 위해 함수 내부에서 import
    from app.routes.chat import _message_payload, connection_manager

    if not room_id:
        chat_room = db.query(ChatRoom).filter(ChatRoom.application_id == application.id).first()
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
            "availableDate": (
                application.available_date.isoformat() if application.available_date else None
            ),
            "availableTime": application.available_time,
        },
    )
    db.add(message)
    db.flush()

    # 채팅방 정보 업데이트
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if chat_room:
        chat_room.last_message_id = message.id
        chat_room.last_message_at = now

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
