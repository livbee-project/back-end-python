"""
Portfolio 라우트
포트폴리오 관리
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.middleware.role import require_role
from app.models.user import UserRole
from app.utils.common import model_to_dict, models_to_list
from app.utils.response import fail_response, success_response

logger = get_logger(__name__)
from app.schemas.portfolios import PortfolioCreate, PortfolioUpdate
from app.services.portfolio_service import (
    create_portfolio as create_portfolio_service,
)
from app.services.portfolio_service import (
    get_portfolio_by_id,
    get_public_portfolios,
    get_user_portfolios,
    validate_and_prepare_portfolio_create_data,
)
from app.services.portfolio_service import (
    update_portfolio as update_portfolio_service,
)

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("/my/list")
async def get_my_portfolios(
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db),
):
    """
    내 모든 포트폴리오 목록 조회
    """
    user_id = current_user.get("sub")
    portfolios = get_user_portfolios(db, user_id)

    items = models_to_list(portfolios)
    return success_response({"items": items})


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    request: PortfolioCreate,
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db),
):
    """
    새 포트폴리오 생성
    """
    user_id = current_user.get("sub")
    portfolio_data = validate_and_prepare_portfolio_create_data(request)

    try:
        portfolio = create_portfolio_service(db, user_id, portfolio_data)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"포트폴리오 생성 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "포트폴리오 생성 중 오류가 발생했습니다.",
                "userMessage": "서버에 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            },
        )

    data = model_to_dict(portfolio)
    return success_response(
        {"message": "포트폴리오가 성공적으로 생성되었습니다.", "data": data},
        status_code=status.HTTP_201_CREATED,
    )


@router.put("/{portfolio_id}")
async def update_portfolio(
    portfolio_id: str,
    request: PortfolioUpdate,
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db),
):
    """
    특정 포트폴리오 수정
    """
    user_id = current_user.get("sub")
    user_role = current_user.get("role")
    update_data = request.model_dump(exclude_unset=True, by_alias=False)

    portfolio = update_portfolio_service(db, portfolio_id, user_id, user_role, update_data)
    data = model_to_dict(portfolio)
    return success_response({"message": "성공적으로 수정되었습니다.", "data": data})


@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: str,
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db),
):
    """
    특정 포트폴리오 삭제
    """
    user_id = current_user.get("sub")
    user_role = current_user.get("role")

    # 서비스를 통한 소유권 확인
    portfolio = get_portfolio_by_id(db, portfolio_id, user_id, user_role)

    db.delete(portfolio)

    return success_response({"message": "성공적으로 삭제되었습니다."})


@router.get("")
async def get_portfolios(
    page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)
):
    """
    공개된 모든 포트폴리오 리스트 조회
    """
    # 서비스를 통한 포트폴리오 목록 조회
    portfolios, total_items = get_public_portfolios(db, page, limit)

    items = []
    for p in portfolios:
        items.append(
            {
                "id": p.id,
                "nickname": p.nickname,
                "oneLineIntro": p.one_line_intro,
                "mainThumbnailUrl": p.main_thumbnail_url,
                "experienceYears": p.experience_years,
                "detailedRegion": p.detailed_region,
                "height": p.height,
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


@router.get("/{portfolio_id}")
async def get_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    """
    특정 공개 포트폴리오 상세 조회
    """
    portfolio = get_portfolio_by_id(db, portfolio_id)

    # 공개 여부 확인
    if portfolio.public_scope != "전체공개" or portfolio.status != "published":
        return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND)

    data = model_to_dict(portfolio, to_camel_case=True)
    return success_response({"data": data})
