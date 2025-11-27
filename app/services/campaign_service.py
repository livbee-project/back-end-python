"""
캠페인 관련 비즈니스 로직 서비스
"""
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.campaign import Campaign, ProductItem, Question
from app.models.application import Application
from app.utils.db_helpers import get_or_404, require_ownership_or_admin
import uuid


def get_campaign_by_id(
    db: Session,
    campaign_id: str
) -> Campaign:
    """
    캠페인 ID로 조회
    
    Args:
        db: 데이터베이스 세션
        campaign_id: 캠페인 ID
    
    Returns:
        캠페인 인스턴스
    
    Raises:
        HTTPException: 캠페인을 찾을 수 없는 경우
    """
    return get_or_404(
        db,
        Campaign,
        lambda q: q.filter(Campaign.id == campaign_id),
        error_key="NOT_FOUND"
    )


def get_user_campaigns(
    db: Session,
    user_id: str
) -> list[Campaign]:
    """
    사용자가 생성한 캠페인 목록 조회
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
    
    Returns:
        캠페인 리스트
    """
    return db.query(Campaign).filter(
        Campaign.created_by == user_id
    ).order_by(desc(Campaign.created_at)).all()


def check_campaign_ownership(
    db: Session,
    campaign_id: str,
    user_id: str,
    user_role: Optional[str] = None
) -> Campaign:
    """
    캠페인 소유권 확인
    
    Args:
        db: 데이터베이스 세션
        campaign_id: 캠페인 ID
        user_id: 사용자 ID
        user_role: 사용자 역할
    
    Returns:
        캠페인 인스턴스
    
    Raises:
        HTTPException: 캠페인을 찾을 수 없거나 권한이 없는 경우
    """
    campaign = get_campaign_by_id(db, campaign_id)
    require_ownership_or_admin(
        campaign,
        user_id,
        user_role,
        owner_field="created_by",
        error_key="FORBIDDEN"
    )
    return campaign


def check_application_exists(
    db: Session,
    campaign_id: str,
    user_id: str
) -> bool:
    """
    사용자가 해당 캠페인에 지원했는지 확인
    
    Args:
        db: 데이터베이스 세션
        campaign_id: 캠페인 ID
        user_id: 사용자 ID
    
    Returns:
        지원 여부
    """
    application = db.query(Application).filter(
        Application.user_id == user_id,
        Application.campaign_id == campaign_id
    ).first()
    return application is not None

