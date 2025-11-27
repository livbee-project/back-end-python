"""
포트폴리오 관련 비즈니스 로직 서비스
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.portfolio import Portfolio
from app.utils.db_helpers import get_or_404, require_ownership_or_admin


def get_portfolio_by_id(
    db: Session,
    portfolio_id: str,
    user_id: Optional[str] = None,
    user_role: Optional[str] = None
) -> Portfolio:
    """
    포트폴리오 ID로 조회
    
    Args:
        db: 데이터베이스 세션
        portfolio_id: 포트폴리오 ID
        user_id: 사용자 ID (소유권 확인용, 선택적)
        user_role: 사용자 역할 (소유권 확인용, 선택적)
    
    Returns:
        포트폴리오 인스턴스
    
    Raises:
        HTTPException: 포트폴리오를 찾을 수 없거나 권한이 없는 경우
    """
    portfolio = get_or_404(
        db,
        Portfolio,
        lambda q: q.filter(Portfolio.id == portfolio_id),
        error_key="NOT_FOUND"
    )
    
    # 소유권 확인이 필요한 경우
    if user_id:
        require_ownership_or_admin(
            portfolio,
            user_id,
            user_role,
            owner_field="user_id",
            error_key="PORTFOLIO_FORBIDDEN_EDIT"
        )
    
    return portfolio


def get_user_portfolios(
    db: Session,
    user_id: str
) -> list[Portfolio]:
    """
    사용자의 포트폴리오 목록 조회
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
    
    Returns:
        포트폴리오 리스트
    """
    return db.query(Portfolio).filter(
        Portfolio.user_id == user_id
    ).order_by(desc(Portfolio.created_at)).all()


def get_public_portfolios(
    db: Session,
    page: int = 1,
    limit: int = 20
) -> tuple[list[Portfolio], int]:
    """
    공개된 포트폴리오 목록 조회
    
    Args:
        db: 데이터베이스 세션
        page: 페이지 번호
        limit: 페이지당 항목 수
    
    Returns:
        (포트폴리오 리스트, 전체 개수) 튜플
    """
    skip = (page - 1) * limit
    
    query = db.query(Portfolio).filter(
        Portfolio.public_scope == "전체공개",
        Portfolio.status == "published"
    )
    
    total_items = query.count()
    portfolios = query.order_by(desc(Portfolio.created_at)).offset(skip).limit(limit).all()
    
    return portfolios, total_items

