"""
Proposal 라우트
제안 관리
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.role import require_role
from app.models.user import UserRole
from app.schemas.proposals import ProposalCreate
from app.services.proposal_service import (
    create_proposal,
    get_received_proposals,
    get_sent_proposals,
    withdraw_proposal,
)
from app.utils.common import format_date
from app.utils.response import success_response

router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_proposal(
    request: ProposalCreate,
    current_user: dict = Depends(require_role(UserRole.BRAND.value)),
    db: Session = Depends(get_db),
):
    """
    쇼호스트에게 새로운 섭외 제안 생성
    """
    proposer_id = current_user.get("sub")

    # 포트폴리오 ID 또는 모델 ID 중 하나는 필수
    if not request.target_portfolio_id and not request.target_model_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "VALIDATION_ERROR",
                "message": "포트폴리오 ID 또는 모델 ID 중 하나는 필수입니다.",
                "userMessage": "포트폴리오 또는 모델을 선택해주세요.",
            },
        )

    # 서비스를 통한 제안 생성
    proposal = create_proposal(
        db,
        target_portfolio_id=request.target_portfolio_id,
        target_model_id=request.target_model_id,
        proposer_id=proposer_id,
        brand_name=request.brand_name,
        shooting_date=request.shooting_date,
        reply_deadline=request.reply_deadline,
        fee=request.fee,
        is_fee_negotiable=request.is_fee_negotiable,
        shooting_time=request.shooting_time,
        location=request.location,
        content=request.content,
    )

    return success_response(
        {"message": "제안이 성공적으로 전송되었습니다."}, status_code=status.HTTP_201_CREATED
    )


@router.get("/sent")
async def get_sent_proposals(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    current_user: dict = Depends(require_role(UserRole.BRAND.value)),
    db: Session = Depends(get_db),
):
    """
    현재 로그인된 브랜드 회원이 보낸 모든 제안 목록 조회
    """
    proposer_id = current_user.get("sub")

    # 서비스를 통한 보낸 제안 목록 조회 (쿼리 최적화: joinedload 사용)
    proposals, total_items = get_sent_proposals(
        db, proposer_id=proposer_id, status_filter=status_filter, page=page, limit=limit
    )

    items = []
    for p in proposals:
        # joinedload로 이미 로드된 showhost 사용
        showhost = p.target_showhost
        items.append(
            {
                "id": p.id,
                "recipient": {
                    "name": showhost.name if showhost else "알 수 없음",
                    "portfolioId": p.target_portfolio_id,
                    "modelId": p.target_model_id,
                },
                "content": p.content,
                "status": p.status.value,
                "sentAt": p.created_at.isoformat() if p.created_at else None,
                "fee": p.fee,
                "isFeeNegotiable": p.is_fee_negotiable,
                "schedule": f"{format_date(p.shooting_date)}. {p.shooting_time or ''} / {p.location or ''}",
                "replyDeadline": format_date(p.reply_deadline),
            }
        )

    total_pages = (total_items + limit - 1) // limit

    return success_response(
        {
            "items": items,
            "currentPage": page,
            "totalPages": total_pages,
            "totalItems": total_items,
        }
    )


@router.get("/received")
async def get_received_proposals(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db),
):
    """
    현재 로그인된 쇼호스트가 받은 모든 제안 목록 조회
    """
    showhost_id = current_user.get("sub")

    # 서비스를 통한 받은 제안 목록 조회
    proposals, total_items = get_received_proposals(
        db, showhost_id=showhost_id, status_filter=status_filter, page=page, limit=limit
    )

    items = []
    for p in proposals:
        items.append(
            {
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
            }
        )

    total_pages = (total_items + limit - 1) // limit

    return success_response(
        {
            "items": items,
            "currentPage": page,
            "totalPages": total_pages,
            "totalItems": total_items,
        }
    )


@router.patch("/{proposal_id}/withdraw")
async def withdraw_proposal(
    proposal_id: str,
    current_user: dict = Depends(require_role(UserRole.BRAND.value)),
    db: Session = Depends(get_db),
):
    """
    브랜드가 보낸 제안을 철회
    """
    proposer_id = current_user.get("sub")

    # 서비스를 통한 제안 철회
    withdraw_proposal(db, proposal_id, proposer_id)

    return success_response({"message": "제안이 성공적으로 철회되었습니다."})
