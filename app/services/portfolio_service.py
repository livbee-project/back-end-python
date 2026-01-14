"""
포트폴리오 관련 비즈니스 로직 서비스
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.portfolio import Portfolio
from app.utils.db_helpers import get_or_404, require_ownership_or_admin
import uuid


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


def get_published_portfolios(
    db: Session,
    page: int = 1,
    limit: int = 10
) -> tuple[list[Portfolio], int]:
    """
    published 상태의 포트폴리오 목록 조회
    
    Args:
        db: 데이터베이스 세션
        page: 페이지 번호
        limit: 페이지당 항목 수
    
    Returns:
        (포트폴리오 리스트, 전체 개수) 튜플
    """
    skip = (page - 1) * limit
    
    query = db.query(Portfolio).filter(
        Portfolio.status == "published"
    )
    
    total_items = query.count()
    portfolios = query.order_by(desc(Portfolio.created_at)).offset(skip).limit(limit).all()
    
    return portfolios, total_items


def check_user_has_portfolio(
    db: Session,
    user_id: str
) -> bool:
    """
    사용자가 포트폴리오를 가지고 있는지 확인
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
    
    Returns:
        포트폴리오 존재 여부
    """
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
    return portfolio is not None


def create_portfolio(
    db: Session,
    user_id: str,
    portfolio_data: Dict[str, Any]
) -> Portfolio:
    """
    포트폴리오 생성
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        portfolio_data: 포트폴리오 데이터
    
    Returns:
        생성된 포트폴리오 인스턴스
    
    Raises:
        HTTPException: 이미 포트폴리오가 있는 경우
    """
    # 중복 체크
    if check_user_has_portfolio(db, user_id):
        from fastapi import HTTPException, status
        from app.utils.error_messages import get_error_message
        error = get_error_message("PORTFOLIO_DUP")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "PORTFOLIO_DUP",
                "message": error["message"],
                "userMessage": error["userMessage"],
            }
        )
    
    portfolio_data["id"] = str(uuid.uuid4())
    portfolio_data["user_id"] = user_id
    
    portfolio = Portfolio(**portfolio_data)
    db.add(portfolio)
    db.flush()  # 세션 변경사항을 DB에 반영 (커밋은 아님)
    db.refresh(portfolio)
    
    return portfolio


def update_portfolio(
    db: Session,
    portfolio_id: str,
    user_id: str,
    user_role: Optional[str] = None,
    update_data: Optional[Dict[str, Any]] = None
) -> Portfolio:
    """
    포트폴리오 수정
    
    Args:
        db: 데이터베이스 세션
        portfolio_id: 포트폴리오 ID
        user_id: 사용자 ID
        user_role: 사용자 역할
        update_data: 업데이트할 데이터
    
    Returns:
        수정된 포트폴리오 인스턴스
    
    Raises:
        HTTPException: 포트폴리오를 찾을 수 없거나 권한이 없는 경우
    """
    portfolio = get_portfolio_by_id(db, portfolio_id, user_id, user_role)
    
    if update_data:
        for key, value in update_data.items():
            setattr(portfolio, key, value)
    
    db.refresh(portfolio)
    
    return portfolio


def delete_portfolio(
    db: Session,
    portfolio_id: str,
    user_id: str,
    user_role: Optional[str] = None
) -> None:
    """
    포트폴리오 삭제
    
    Args:
        db: 데이터베이스 세션
        portfolio_id: 포트폴리오 ID
        user_id: 사용자 ID
        user_role: 사용자 역할
    
    Raises:
        HTTPException: 포트폴리오를 찾을 수 없거나 권한이 없는 경우
    """
    portfolio = get_portfolio_by_id(db, portfolio_id, user_id, user_role)
    db.delete(portfolio)

