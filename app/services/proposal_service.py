"""
제안 관련 비즈니스 로직 서비스
"""
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.models.proposal import Proposal, ProposalStatus
from app.models.portfolio import Portfolio
from app.models.model import Model
from app.models.user import User
from app.utils.db_helpers import get_or_404, require_ownership_or_admin
import uuid


def create_proposal(
    db: Session,
    proposer_id: str,
    brand_name: str,
    shooting_date: date,
    reply_deadline: date,
    target_portfolio_id: Optional[str] = None,
    target_model_id: Optional[str] = None,
    fee: Optional[int] = None,
    is_fee_negotiable: bool = False,
    shooting_time: Optional[str] = None,
    location: Optional[str] = None,
    content: Optional[str] = None
) -> Proposal:
    """
    제안 생성
    
    Args:
        db: 데이터베이스 세션
        proposer_id: 제안자 ID
        brand_name: 브랜드명
        shooting_date: 촬영일
        reply_deadline: 답변 마감일
        target_portfolio_id: 대상 포트폴리오 ID (선택)
        target_model_id: 대상 모델 ID (선택)
        fee: 수수료
        is_fee_negotiable: 수수료 협상 가능 여부
        shooting_time: 촬영 시간
        location: 장소
        content: 내용
    
    Returns:
        생성된 제안 인스턴스
    
    Raises:
        HTTPException: 포트폴리오/모델을 찾을 수 없는 경우
    """
    target_showhost_id = None
    
    # 포트폴리오 또는 모델 확인
    if target_portfolio_id:
        portfolio = get_or_404(
            db,
            Portfolio,
            lambda q: q.filter(Portfolio.id == target_portfolio_id),
            error_key="NOT_FOUND"
        )
        target_showhost_id = portfolio.user_id
    elif target_model_id:
        model = get_or_404(
            db,
            Model,
            lambda q: q.filter(Model.id == target_model_id),
            error_key="NOT_FOUND"
        )
        target_showhost_id = model.user_id
    else:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "VALIDATION_ERROR",
                "message": "포트폴리오 ID 또는 모델 ID 중 하나는 필수입니다.",
                "userMessage": "포트폴리오 또는 모델을 선택해주세요.",
            }
        )
    
    # 제안 생성
    proposal = Proposal(
        id=str(uuid.uuid4()),
        target_portfolio_id=target_portfolio_id,
        target_model_id=target_model_id,
        proposer_id=proposer_id,
        target_showhost_id=target_showhost_id,
        brand_name=brand_name,
        fee=fee,
        is_fee_negotiable=is_fee_negotiable,
        shooting_date=shooting_date,
        shooting_time=shooting_time,
        location=location,
        reply_deadline=reply_deadline,
        content=content,
        status=ProposalStatus.PENDING
    )
    
    db.add(proposal)
    db.refresh(proposal)
    
    return proposal


def get_sent_proposals(
    db: Session,
    proposer_id: str,
    status_filter: Optional[str] = None,
    page: int = 1,
    limit: int = 10
) -> tuple[list[Proposal], int]:
    """
    보낸 제안 목록 조회
    
    Args:
        db: 데이터베이스 세션
        proposer_id: 제안자 ID
        status_filter: 상태 필터
        page: 페이지 번호
        limit: 페이지당 항목 수
    
    Returns:
        (제안 리스트, 전체 개수) 튜플
    """
    skip = (page - 1) * limit
    
    query = db.query(Proposal).options(
        joinedload(Proposal.target_showhost)
    ).filter(Proposal.proposer_id == proposer_id)
    
    if status_filter:
        query = query.filter(Proposal.status == status_filter)
    
    total_items = query.count()
    proposals = query.order_by(desc(Proposal.created_at)).offset(skip).limit(limit).all()
    
    return proposals, total_items


def get_received_proposals(
    db: Session,
    showhost_id: str,
    status_filter: Optional[str] = None,
    page: int = 1,
    limit: int = 10
) -> tuple[list[Proposal], int]:
    """
    받은 제안 목록 조회
    
    Args:
        db: 데이터베이스 세션
        showhost_id: 쇼호스트 ID
        status_filter: 상태 필터
        page: 페이지 번호
        limit: 페이지당 항목 수
    
    Returns:
        (제안 리스트, 전체 개수) 튜플
    """
    skip = (page - 1) * limit
    
    query = db.query(Proposal).filter(Proposal.target_showhost_id == showhost_id)
    
    if status_filter:
        query = query.filter(Proposal.status == status_filter)
    
    total_items = query.count()
    proposals = query.order_by(desc(Proposal.created_at)).offset(skip).limit(limit).all()
    
    return proposals, total_items


def withdraw_proposal(
    db: Session,
    proposal_id: str,
    proposer_id: str
) -> Proposal:
    """
    제안 철회
    
    Args:
        db: 데이터베이스 세션
        proposal_id: 제안 ID
        proposer_id: 제안자 ID
    
    Returns:
        철회된 제안 인스턴스
    
    Raises:
        HTTPException: 제안을 찾을 수 없거나 권한이 없거나 상태가 맞지 않는 경우
    """
    proposal = get_or_404(
        db,
        Proposal,
        lambda q: q.filter(Proposal.id == proposal_id),
        error_key="NOT_FOUND"
    )
    
    # 소유권 확인
    if proposal.proposer_id != proposer_id:
        from fastapi import HTTPException, status
        from app.utils.error_messages import get_error_message
        error = get_error_message("FORBIDDEN")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "FORBIDDEN",
                "message": error["message"],
                "userMessage": "제안을 철회할 권한이 없습니다.",
            }
        )
    
    # 상태 확인
    if proposal.status != ProposalStatus.PENDING:
        from fastapi import HTTPException, status
        from app.utils.error_messages import get_error_message
        error = get_error_message("BAD_REQUEST")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "BAD_REQUEST",
                "message": error["message"],
                "userMessage": "대기중인 제안만 철회할 수 있습니다.",
            }
        )
    
    proposal.status = ProposalStatus.WITHDRAWN
    
    return proposal

