"""
지원서 관련 비즈니스 로직 서비스
"""
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.models.application import Application, ApplicationStatus
from app.models.campaign import Campaign
from app.models.chat import ChatRoom, ChatMessage, ChatMessageType
from app.models.portfolio import Portfolio
from app.models.model import Model
from app.models.user import User
from app.services.chat_service import ensure_chat_room
from app.utils.db_helpers import get_or_404, require_ownership_or_admin
import uuid
from datetime import datetime, timezone


def create_application(
    db: Session,
    campaign_id: str,
    user_id: str,
    profile_ref: Optional[str] = None,
    portfolio_id: Optional[str] = None,
    model_id: Optional[str] = None,
    message: Optional[str] = None,
    available_date: Optional[date] = None,
    available_time: Optional[str] = None,
) -> Application:
    """
    지원서 생성
    
    Args:
        db: 데이터베이스 세션
        campaign_id: 캠페인 ID
        user_id: 사용자 ID
        profile_ref: 포트폴리오 참조
        message: 지원 메시지
    
    Returns:
        생성된 지원서 인스턴스
    
    Raises:
        HTTPException: 캠페인을 찾을 수 없거나, 마감일이 지났거나, 이미 지원한 경우
    """
    # 캠페인 확인
    campaign = get_or_404(
        db,
        Campaign,
        lambda q: q.filter(Campaign.id == campaign_id),
        error_key="NOT_FOUND"
    )
    
    # 마감일 확인
    if campaign.close_at < date.today():
        from fastapi import HTTPException, status
        from app.utils.error_messages import get_error_message
        error = get_error_message("DEADLINE_PASSED")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "DEADLINE_PASSED",
                "message": error["message"],
                "userMessage": error["userMessage"],
            }
        )
    
    # 중복 지원 확인
    existing = db.query(Application).filter(
        Application.campaign_id == campaign_id,
        Application.user_id == user_id
    ).first()
    
    if existing:
        from fastapi import HTTPException, status
        from app.utils.error_messages import get_error_message
        error = get_error_message("ALREADY_APPLIED")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "ALREADY_APPLIED",
                "message": error["message"],
                "userMessage": error["userMessage"],
            }
        )
    
    # 지원서 생성
    application = Application(
        id=str(uuid.uuid4()),
        campaign_id=campaign_id,
        user_id=user_id,
        profile_ref=profile_ref,  # 하위 호환성 유지
        portfolio_id=portfolio_id,
        model_id=model_id,
        message=message,
        available_date=available_date,
        available_time=available_time,
        status=ApplicationStatus.SUBMITTED
    )
    
    db.add(application)
    db.flush()
    
    # 채팅방 생성/재사용
    chat_room = ensure_chat_room(
        db,
        campaign_id=campaign.id,
        brand_user_id=campaign.created_by,
        showhost_user_id=user_id,
        application_id=application.id,
    )
    
    db.refresh(application)
    db.refresh(chat_room)
    
    return application


def get_application_by_campaign_and_user(
    db: Session,
    campaign_id: str,
    user_id: str
) -> Optional[Application]:
    """
    캠페인과 사용자로 지원서 조회
    
    Args:
        db: 데이터베이스 세션
        campaign_id: 캠페인 ID
        user_id: 사용자 ID
    
    Returns:
        지원서 인스턴스 또는 None
    """
    return db.query(Application).filter(
        Application.campaign_id == campaign_id,
        Application.user_id == user_id
    ).first()


def get_applications_by_campaign(
    db: Session,
    campaign_id: str,
    user_id: str,
    user_role: str
) -> list[Application]:
    """
    캠페인의 지원서 목록 조회 (오너/관리자 전용)
    
    Args:
        db: 데이터베이스 세션
        campaign_id: 캠페인 ID
        user_id: 사용자 ID
        user_role: 사용자 역할
    
    Returns:
        지원서 리스트
    
    Raises:
        HTTPException: 캠페인을 찾을 수 없거나 권한이 없는 경우
    """
    campaign = get_or_404(
        db,
        Campaign,
        lambda q: q.filter(Campaign.id == campaign_id),
        error_key="NOT_FOUND"
    )
    
    # 오너 확인
    require_ownership_or_admin(
        campaign,
        user_id,
        user_role,
        owner_field="created_by",
        error_key="FORBIDDEN"
    )
    
    return db.query(Application).filter(
        Application.campaign_id == campaign_id
    ).order_by(desc(Application.created_at)).all()


def update_application_status(
    db: Session,
    application_id: str,
    new_status: ApplicationStatus,
    user_id: str,
    user_role: str
) -> Application:
    """
    지원서 상태 변경
    
    Args:
        db: 데이터베이스 세션
        application_id: 지원서 ID
        new_status: 새로운 상태
        user_id: 사용자 ID
        user_role: 사용자 역할
    
    Returns:
        업데이트된 지원서 인스턴스
    
    Raises:
        HTTPException: 지원서를 찾을 수 없거나 권한이 없는 경우
    """
    application = get_or_404(
        db,
        Application,
        lambda q: q.options(joinedload(Application.campaign)).filter(Application.id == application_id),
        error_key="NOT_FOUND"
    )
    
    campaign = application.campaign
    if not campaign:
        from fastapi import HTTPException, status
        from app.utils.error_messages import get_error_message
        error = get_error_message("NOT_FOUND")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NOT_FOUND",
                "message": error["message"],
                "userMessage": error["userMessage"],
            }
        )
    
    # 오너 확인
    require_ownership_or_admin(
        campaign,
        user_id,
        user_role,
        owner_field="created_by",
        error_key="FORBIDDEN"
    )
    
    application.status = new_status
    db.refresh(application)
    
    return application

