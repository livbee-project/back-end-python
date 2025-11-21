"""
Proposal 라우트
제안 관리
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.role import require_role
from app.models.proposal import Proposal, ProposalStatus
from app.models.portfolio import Portfolio
from app.models.user import User, UserRole
from app.utils.response import success_response, fail_response
from app.utils.common import format_date
import uuid

router = APIRouter(prefix="/proposals", tags=["proposals"])


class ProposalCreate(BaseModel):
    target_portfolio_id: str = Field(..., alias="targetPortfolioId")
    brand_name: str = Field(..., alias="brandName")
    fee: Optional[int] = None
    is_fee_negotiable: bool = Field(False, alias="isFeeNegotiable")
    shooting_date: date = Field(..., alias="shootingDate")
    shooting_time: Optional[str] = Field(None, alias="shootingTime")
    location: Optional[str] = None
    reply_deadline: date = Field(..., alias="replyDeadline")
    content: Optional[str] = Field(None, max_length=800)

    class Config:
        populate_by_name = True


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_proposal(
    request: ProposalCreate,
    current_user: dict = Depends(require_role(UserRole.BRAND.value)),
    db: Session = Depends(get_db)
):
    """
    쇼호스트에게 새로운 섭외 제안 생성
    """
    proposer_id = current_user.get("sub")

    # 포트폴리오 확인
    portfolio = db.query(Portfolio).filter(Portfolio.id == request.target_portfolio_id).first()
    if not portfolio:
        return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND, {
            "userMessage": "제안 대상을 찾을 수 없습니다."
        })

    # 제안 생성
    proposal = Proposal(
        id=str(uuid.uuid4()),
        target_portfolio_id=request.target_portfolio_id,
        proposer_id=proposer_id,
        target_showhost_id=portfolio.user_id,
        brand_name=request.brand_name,
        fee=request.fee,
        is_fee_negotiable=request.is_fee_negotiable,
        shooting_date=request.shooting_date,
        shooting_time=request.shooting_time,
        location=request.location,
        reply_deadline=request.reply_deadline,
        content=request.content,
        status=ProposalStatus.PENDING
    )

    db.add(proposal)
    db.commit()
    db.refresh(proposal)

    return success_response(
        {"message": "제안이 성공적으로 전송되었습니다."},
        status_code=status.HTTP_201_CREATED
    )


@router.get("/sent")
async def get_sent_proposals(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    current_user: dict = Depends(require_role(UserRole.BRAND.value)),
    db: Session = Depends(get_db)
):
    """
    현재 로그인된 브랜드 회원이 보낸 모든 제안 목록 조회
    """
    proposer_id = current_user.get("sub")
    skip = (page - 1) * limit

    query = db.query(Proposal).filter(Proposal.proposer_id == proposer_id)

    if status_filter:
        query = query.filter(Proposal.status == status_filter)

    total_items = query.count()
    proposals = query.order_by(desc(Proposal.created_at)).offset(skip).limit(limit).all()

    items = []
    for p in proposals:
        # 쇼호스트 정보 조회
        showhost = db.query(User).filter(User.id == p.target_showhost_id).first()
        items.append({
            "id": p.id,
            "recipient": {
                "name": showhost.name if showhost else "알 수 없음",
                "portfolioId": p.target_portfolio_id,
            },
            "content": p.content,
            "status": p.status.value,
            "sentAt": p.created_at.isoformat() if p.created_at else None,
            "fee": p.fee,
            "isFeeNegotiable": p.is_fee_negotiable,
            "schedule": f"{format_date(p.shooting_date)}. {p.shooting_time or ''} / {p.location or ''}",
            "replyDeadline": format_date(p.reply_deadline),
        })

    total_pages = (total_items + limit - 1) // limit

    return success_response({
        "items": items,
        "currentPage": page,
        "totalPages": total_pages,
        "totalItems": total_items,
    })


@router.get("/received")
async def get_received_proposals(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db)
):
    """
    현재 로그인된 쇼호스트가 받은 모든 제안 목록 조회
    """
    showhost_id = current_user.get("sub")
    skip = (page - 1) * limit

    query = db.query(Proposal).filter(Proposal.target_showhost_id == showhost_id)

    if status_filter:
        query = query.filter(Proposal.status == status_filter)

    total_items = query.count()
    proposals = query.order_by(desc(Proposal.created_at)).offset(skip).limit(limit).all()

    items = []
    for p in proposals:
        items.append({
            "id": p.id,
            "sender": {
                "brandName": p.brand_name,
            },
            "content": p.content,
            "status": p.status.value,
            "sentAt": p.created_at.isoformat() if p.created_at else None,
            "fee": p.fee,
            "isFeeNegotiable": p.is_fee_negotiable,
            "schedule": f"{format_date(p.shooting_date)}. {p.shooting_time or ''} / {p.location or ''}",
            "replyDeadline": format_date(p.reply_deadline),
        })

    total_pages = (total_items + limit - 1) // limit

    return success_response({
        "items": items,
        "currentPage": page,
        "totalPages": total_pages,
        "totalItems": total_items,
    })


@router.patch("/{proposal_id}/withdraw")
async def withdraw_proposal(
    proposal_id: str,
    current_user: dict = Depends(require_role(UserRole.BRAND.value)),
    db: Session = Depends(get_db)
):
    """
    브랜드가 보낸 제안을 철회
    """
    proposer_id = current_user.get("sub")

    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND)

    if proposal.proposer_id != proposer_id:
        return fail_response("FORBIDDEN", status.HTTP_403_FORBIDDEN, {
            "userMessage": "제안을 철회할 권한이 없습니다."
        })

    if proposal.status != ProposalStatus.PENDING:
        return fail_response("BAD_REQUEST", status.HTTP_400_BAD_REQUEST, {
            "userMessage": "대기중인 제안만 철회할 수 있습니다."
        })

    proposal.status = ProposalStatus.WITHDRAWN
    db.commit()

    return success_response({"message": "제안이 성공적으로 철회되었습니다."})

