"""
캠페인 관련 비즈니스 로직 서비스
"""
from typing import Optional, Set
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
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


def get_campaigns_with_applied_status(
    db: Session,
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    sort: Optional[str] = None,
    user_id: Optional[str] = None
) -> tuple[list[Campaign], int, Set[str]]:
    """
    캠페인 목록 조회 (지원 여부 포함, 쿼리 최적화)
    
    Args:
        db: 데이터베이스 세션
        page: 페이지 번호
        limit: 페이지당 항목 수
        search: 검색어
        sort: 정렬 방식
        user_id: 사용자 ID (지원 여부 확인용)
    
    Returns:
        (캠페인 리스트, 전체 개수, 지원한 캠페인 ID 집합) 튜플
    """
    skip = (page - 1) * limit
    
    query = db.query(Campaign).filter(
        Campaign.is_public == True,
        Campaign.close_at >= date.today()
    )
    
    # 검색 조건
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Campaign.title.ilike(search_term),
                Campaign.content.ilike(search_term),
                Campaign.brand_name.ilike(search_term)
            )
        )
    
    # 정렬
    if sort == "deadline":
        query = query.order_by(Campaign.close_at.asc())
    else:
        query = query.order_by(desc(Campaign.created_at))
    
    total_items = query.count()
    campaigns = query.offset(skip).limit(limit).all()
    
    # 지원 여부 확인 (배치 쿼리로 N+1 방지)
    applied_campaign_ids: Set[str] = set()
    if user_id and campaigns:
        campaign_ids = [c.id for c in campaigns]
        applications = db.query(Application.campaign_id).filter(
            Application.user_id == user_id,
            Application.campaign_id.in_(campaign_ids)
        ).all()
        applied_campaign_ids = {app.campaign_id for app in applications}
    
    return campaigns, total_items, applied_campaign_ids

