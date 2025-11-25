"""
Application 라우트
지원서 관리
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date
from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.role import require_role
from app.models.application import Application, ApplicationStatus
from app.models.campaign import Campaign
from app.models.user import User, UserRole
from app.utils.response import success_response, fail_response
from app.services.chat_service import ensure_chat_room
import uuid

router = APIRouter(prefix="/applications", tags=["applications"])


class ApplicationCreate(BaseModel):
    campaign_id: str
    profile_ref: Optional[str] = None
    message: Optional[str] = None


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

    application.status = request.status
    db.commit()
    db.refresh(application)

    data = {"id": application.id, **{k: v for k, v in application.__dict__.items() if not k.startswith("_")}}
    return success_response({"data": data})

