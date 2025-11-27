"""
Portfolio 라우트
포트폴리오 관리
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.middleware.auth import get_current_user, get_optional_user
from app.middleware.role import require_role
from app.models.portfolio import Portfolio
from app.models.user import User, UserRole
from app.utils.response import success_response, fail_response
from app.utils.common import model_to_dict, models_to_list
from app.services.portfolio_service import (
    get_portfolio_by_id,
    get_user_portfolios,
    get_public_portfolios
)
import uuid

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


class PortfolioCreate(BaseModel):
    nickname: Optional[str] = None
    one_line_intro: Optional[str] = Field(None, alias="oneLineIntro")
    detailed_intro: Optional[str] = Field(None, alias="detailedIntro")
    experience_years: Optional[int] = Field(None, alias="experienceYears")
    age: Optional[int] = None
    main_thumbnail_url: Optional[str] = Field(None, alias="mainThumbnailUrl")
    background_image_url: Optional[str] = Field(None, alias="backgroundImageUrl")
    sub_thumbnail_urls: Optional[List[str]] = Field(None, alias="subThumbnailUrls")
    status: Optional[str] = "published"
    is_age_public: Optional[bool] = Field(True, alias="isAgePublic")
    is_sizing_public: Optional[bool] = Field(True, alias="isSizingPublic")
    detailed_region: Optional[str] = Field(None, alias="detailedRegion")
    gender: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    top_size: Optional[str] = Field(None, alias="topSize")
    bottom_size: Optional[str] = Field(None, alias="bottomSize")
    shoe_size: Optional[int] = Field(None, alias="shoeSize")
    website_url: Optional[str] = Field(None, alias="websiteUrl")
    instagram_url: Optional[str] = Field(None, alias="instagramUrl")
    youtube_url: Optional[str] = Field(None, alias="youtubeUrl")
    tiktok_url: Optional[str] = Field(None, alias="tiktokUrl")
    contact: Optional[str] = None
    open_chat: Optional[str] = Field(None, alias="openChat")
    registration_type: Optional[str] = Field(None, alias="registrationType")
    public_scope: Optional[str] = Field("전체공개", alias="publicScope")
    is_receiving_offers: Optional[bool] = Field(True, alias="isReceivingOffers")
    recent_lives: Optional[List[dict]] = Field(None, alias="recentLives")
    attached_file_url: Optional[str] = Field(None, alias="attachedFileUrl")

    class Config:
        populate_by_name = True


class PortfolioUpdate(BaseModel):
    nickname: Optional[str] = None
    one_line_intro: Optional[str] = Field(None, alias="oneLineIntro")
    detailed_intro: Optional[str] = Field(None, alias="detailedIntro")
    experience_years: Optional[int] = Field(None, alias="experienceYears")
    age: Optional[int] = None
    main_thumbnail_url: Optional[str] = Field(None, alias="mainThumbnailUrl")
    background_image_url: Optional[str] = Field(None, alias="backgroundImageUrl")
    sub_thumbnail_urls: Optional[List[str]] = Field(None, alias="subThumbnailUrls")
    status: Optional[str] = None
    is_age_public: Optional[bool] = Field(None, alias="isAgePublic")
    is_sizing_public: Optional[bool] = Field(None, alias="isSizingPublic")
    detailed_region: Optional[str] = Field(None, alias="detailedRegion")
    gender: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    top_size: Optional[str] = Field(None, alias="topSize")
    bottom_size: Optional[str] = Field(None, alias="bottomSize")
    shoe_size: Optional[int] = Field(None, alias="shoeSize")
    website_url: Optional[str] = Field(None, alias="websiteUrl")
    instagram_url: Optional[str] = Field(None, alias="instagramUrl")
    youtube_url: Optional[str] = Field(None, alias="youtubeUrl")
    tiktok_url: Optional[str] = Field(None, alias="tiktokUrl")
    contact: Optional[str] = None
    open_chat: Optional[str] = Field(None, alias="openChat")
    registration_type: Optional[str] = Field(None, alias="registrationType")
    public_scope: Optional[str] = Field(None, alias="publicScope")
    is_receiving_offers: Optional[bool] = Field(None, alias="isReceivingOffers")
    recent_lives: Optional[List[dict]] = Field(None, alias="recentLives")
    attached_file_url: Optional[str] = Field(None, alias="attachedFileUrl")

    class Config:
        populate_by_name = True


@router.get("/my/list")
async def get_my_portfolios(
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    """
    새 포트폴리오 생성
    """
    user_id = current_user.get("sub")

    # 포트폴리오 데이터 생성
    portfolio_data = request.model_dump(exclude_unset=True, by_alias=False)
    portfolio_data["id"] = str(uuid.uuid4())
    portfolio_data["user_id"] = user_id

    portfolio = Portfolio(**portfolio_data)
    db.add(portfolio)
    db.refresh(portfolio)

    data = model_to_dict(portfolio)
    return success_response(
        {"message": "포트폴리오가 성공적으로 생성되었습니다.", "data": data},
        status_code=status.HTTP_201_CREATED
    )


@router.put("/{portfolio_id}")
async def update_portfolio(
    portfolio_id: str,
    request: PortfolioUpdate,
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db)
):
    """
    특정 포트폴리오 수정
    """
    user_id = current_user.get("sub")
    user_role = current_user.get("role")

    # 서비스를 통한 소유권 확인
    portfolio = get_portfolio_by_id(db, portfolio_id, user_id, user_role)

    # 업데이트할 필드만 적용
    update_data = request.model_dump(exclude_unset=True, by_alias=False)
    for key, value in update_data.items():
        setattr(portfolio, key, value)

    db.refresh(portfolio)

    data = model_to_dict(portfolio)
    return success_response({"message": "성공적으로 수정되었습니다.", "data": data})


@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: str,
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db)
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
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    공개된 모든 포트폴리오 리스트 조회
    """
    # 서비스를 통한 포트폴리오 목록 조회
    portfolios, total_items = get_public_portfolios(db, page, limit)

    items = []
    for p in portfolios:
        items.append({
            "id": p.id,
            "nickname": p.nickname,
            "oneLineIntro": p.one_line_intro,
            "mainThumbnailUrl": p.main_thumbnail_url,
            "experienceYears": p.experience_years,
            "detailedRegion": p.detailed_region,
            "height": p.height,
        })

    total_pages = (total_items + limit - 1) // limit

    return success_response({
        "items": items,
        "currentPage": page,
        "totalPages": total_pages,
        "totalItems": total_items,
    })


@router.get("/{portfolio_id}")
async def get_portfolio(
    portfolio_id: str,
    db: Session = Depends(get_db)
):
    """
    특정 공개 포트폴리오 상세 조회
    """
    portfolio = get_portfolio_by_id(db, portfolio_id)
    
    # 공개 여부 확인
    if portfolio.public_scope != "전체공개" or portfolio.status != "published":
        return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND)

    data = model_to_dict(portfolio)
    return success_response({"data": data})

