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
from app.utils.common import model_to_dict, models_to_list, validate_url, validate_phone_number
from app.utils.error_messages import get_error_message
from app.core.logging_config import get_logger

logger = get_logger(__name__)
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

    # 필수 필드 검증
    if not request.nickname:
        error = get_error_message("PORTFOLIO_MISSING_REQUIRED_FIELD")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PORTFOLIO_MISSING_REQUIRED_FIELD",
                "message": error["message"],
                "userMessage": "닉네임은 필수 입력값입니다.",
            }
        )
    
    if not request.registration_type:
        error = get_error_message("PORTFOLIO_MISSING_REQUIRED_FIELD")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PORTFOLIO_MISSING_REQUIRED_FIELD",
                "message": error["message"],
                "userMessage": "등록 유형은 필수 입력값입니다.",
            }
        )

    # 갤러리 이미지 개수 검증 (포트폴리오는 최대 9개)
    if request.sub_thumbnail_urls and len(request.sub_thumbnail_urls) > 9:
        error = get_error_message("PORTFOLIO_TOO_MANY_IMAGES")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PORTFOLIO_TOO_MANY_IMAGES",
                "message": error["message"],
                "userMessage": "갤러리 이미지는 최대 9개까지 등록할 수 있습니다.",
            }
        )

    # URL 형식 검증
    url_fields = {
        "website_url": request.website_url,
        "youtube_url": request.youtube_url,
        "instagram_url": request.instagram_url,
        "tiktok_url": request.tiktok_url,
        "open_chat": request.open_chat,
    }
    for field_name, url_value in url_fields.items():
        if url_value and not validate_url(url_value):
            error = get_error_message("PORTFOLIO_INVALID_URL")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "PORTFOLIO_INVALID_URL",
                    "message": error["message"],
                    "userMessage": f"{field_name}의 URL 형식이 올바르지 않습니다.",
                }
            )
    
    # recent_lives URL 검증
    if request.recent_lives:
        for live in request.recent_lives:
            if isinstance(live, dict) and "url" in live:
                if live["url"] and not validate_url(live["url"]):
                    error = get_error_message("PORTFOLIO_INVALID_URL")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error": "PORTFOLIO_INVALID_URL",
                            "message": error["message"],
                            "userMessage": "최근 라이브 방송 URL 형식이 올바르지 않습니다.",
                        }
                    )

    # 전화번호 형식 검증
    if request.contact and not validate_phone_number(request.contact):
        error = get_error_message("PORTFOLIO_INVALID_PHONE")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PORTFOLIO_INVALID_PHONE",
                "message": error["message"],
                "userMessage": "연락처 전화번호 형식이 올바르지 않습니다.",
            }
        )

    # websiteUrl을 youtube_url로 매핑 (프론트엔드 호환성)
    portfolio_data = request.model_dump(exclude_unset=True, by_alias=False)
    if "website_url" in portfolio_data and portfolio_data["website_url"] and not portfolio_data.get("youtube_url"):
        portfolio_data["youtube_url"] = portfolio_data["website_url"]
        # website_url은 모델에 있으므로 None으로 설정 (삭제하지 않음)
        portfolio_data["website_url"] = None

    portfolio_data["id"] = str(uuid.uuid4())
    portfolio_data["user_id"] = user_id

    # Portfolio 모델에 없는 필드 제거 (안전성)
    try:
        portfolio_fields = {col.name for col in Portfolio.__table__.columns}
        portfolio_data = {k: v for k, v in portfolio_data.items() if k in portfolio_fields}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "포트폴리오 필드 필터링 중 오류가 발생했습니다.",
                "userMessage": "서버에 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            }
        )

    try:
        portfolio = Portfolio(**portfolio_data)
        db.add(portfolio)
        db.flush()  # 다른 라우트들과 동일하게 flush 사용
        db.refresh(portfolio)
    except Exception as e:
        db.rollback()
        # 로그에 상세 정보 기록 (실제 에러는 로그에만 남김)
        logger.error(f"포트폴리오 생성 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "포트폴리오 생성 중 오류가 발생했습니다.",
                "userMessage": "서버에 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            }
        )

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

    # 갤러리 이미지 개수 검증 (포트폴리오는 최대 9개)
    if request.sub_thumbnail_urls is not None and len(request.sub_thumbnail_urls) > 9:
        error = get_error_message("PORTFOLIO_TOO_MANY_IMAGES")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PORTFOLIO_TOO_MANY_IMAGES",
                "message": error["message"],
                "userMessage": "갤러리 이미지는 최대 9개까지 등록할 수 있습니다.",
            }
        )

    # URL 형식 검증
    url_fields = {
        "website_url": request.website_url,
        "youtube_url": request.youtube_url,
        "instagram_url": request.instagram_url,
        "tiktok_url": request.tiktok_url,
        "open_chat": request.open_chat,
    }
    for field_name, url_value in url_fields.items():
        if url_value is not None and url_value and not validate_url(url_value):
            error = get_error_message("PORTFOLIO_INVALID_URL")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "PORTFOLIO_INVALID_URL",
                    "message": error["message"],
                    "userMessage": f"{field_name}의 URL 형식이 올바르지 않습니다.",
                }
            )
    
    # recent_lives URL 검증
    if request.recent_lives is not None:
        for live in request.recent_lives:
            if isinstance(live, dict) and "url" in live:
                if live["url"] and not validate_url(live["url"]):
                    error = get_error_message("PORTFOLIO_INVALID_URL")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error": "PORTFOLIO_INVALID_URL",
                            "message": error["message"],
                            "userMessage": "최근 라이브 방송 URL 형식이 올바르지 않습니다.",
                        }
                    )

    # 전화번호 형식 검증
    if request.contact is not None and request.contact and not validate_phone_number(request.contact):
        error = get_error_message("PORTFOLIO_INVALID_PHONE")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PORTFOLIO_INVALID_PHONE",
                "message": error["message"],
                "userMessage": "연락처 전화번호 형식이 올바르지 않습니다.",
            }
        )

    # 업데이트할 필드만 적용
    update_data = request.model_dump(exclude_unset=True, by_alias=False)
    
    # websiteUrl을 youtube_url로 매핑 (프론트엔드 호환성)
    if "website_url" in update_data and update_data["website_url"] and not update_data.get("youtube_url"):
        update_data["youtube_url"] = update_data["website_url"]
        update_data["website_url"] = None
    
    # Portfolio 모델에 있는 필드만 업데이트 (안전성)
    portfolio_fields = {col.name for col in Portfolio.__table__.columns}
    for key, value in update_data.items():
        if key in portfolio_fields:
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

