"""
Models 라우트
모델 관리 (포트폴리오와 동일한 데이터, 다른 엔드포인트명)
프론트엔드 호환성을 위해 /models 엔드포인트 제공
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
from app.utils.pagination import normalize_pagination, apply_pagination, build_paginated_payload
from app.utils.common import validate_url, validate_phone_number
from app.utils.error_messages import get_error_message
from app.services.portfolio_service import (
    get_portfolio_by_id,
    get_published_portfolios,
    check_user_has_portfolio,
    create_portfolio,
    update_portfolio,
    delete_portfolio
)
import uuid

router = APIRouter(prefix="/models", tags=["models"])


class ModelCreate(BaseModel):
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


class ModelUpdate(BaseModel):
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


def portfolio_to_model_dict(portfolio: Portfolio) -> dict:
    """Portfolio 객체를 모델 응답 형식으로 변환"""
    return {
        "id": portfolio.id,
        "user": portfolio.user_id,
        "nickname": portfolio.nickname,
        "oneLineIntro": portfolio.one_line_intro,
        "detailedIntro": portfolio.detailed_intro,
        "experienceYears": portfolio.experience_years,
        "age": portfolio.age,
        "isAgePublic": portfolio.is_age_public,
        "mainThumbnailUrl": portfolio.main_thumbnail_url,
        "backgroundImageUrl": portfolio.background_image_url,
        "subThumbnailUrls": portfolio.sub_thumbnail_urls or [],
        "status": portfolio.status,
        "detailedRegion": portfolio.detailed_region,
        "gender": portfolio.gender,
        "height": portfolio.height,
        "weight": portfolio.weight,
        "topSize": portfolio.top_size,
        "bottomSize": portfolio.bottom_size,
        "shoeSize": portfolio.shoe_size,
        "isSizingPublic": portfolio.is_sizing_public,
        "websiteUrl": portfolio.website_url,
        "instagramUrl": portfolio.instagram_url,
        "youtubeUrl": portfolio.youtube_url,
        "tiktokUrl": portfolio.tiktok_url,
        "publicScope": portfolio.public_scope,
        "isReceivingOffers": portfolio.is_receiving_offers,
        "attachedFileUrl": portfolio.attached_file_url,
        "createdAt": portfolio.created_at.isoformat() if portfolio.created_at else None,
        "updatedAt": portfolio.updated_at.isoformat() if portfolio.updated_at else None,
    }


@router.get("")
async def get_model_list(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    모델 목록 조회 (페이지네이션)
    포트폴리오 데이터를 모델 형식으로 반환
    """
    # 페이지네이션 정규화
    page, limit = normalize_pagination(page, limit)
    
    # 서비스를 통한 published 포트폴리오 목록 조회
    portfolios, total_items = get_published_portfolios(db, page, limit)
    
    # 응답 데이터 변환
    items = [portfolio_to_model_dict(p) for p in portfolios]
    
    # 페이지네이션 응답 구성
    return success_response(build_paginated_payload(items, total_items, page, limit))


@router.get("/{model_id}")
async def get_model(
    model_id: str,
    db: Session = Depends(get_db)
):
    """
    특정 모델 상세 정보 조회
    """
    portfolio = get_portfolio_by_id(db, model_id)
    
    data = portfolio_to_model_dict(portfolio)
    return success_response({"data": data})


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_model(
    request: ModelCreate,
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db)
):
    """
    새 모델 등록 (포트폴리오 생성)
    showhost 역할만 가능
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

    # 갤러리 이미지 개수 검증 (모델은 최대 5개)
    if request.sub_thumbnail_urls and len(request.sub_thumbnail_urls) > 5:
        error = get_error_message("PORTFOLIO_TOO_MANY_IMAGES")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PORTFOLIO_TOO_MANY_IMAGES",
                "message": error["message"],
                "userMessage": "갤러리 이미지는 최대 5개까지 등록할 수 있습니다.",
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
    
    # 포트폴리오 데이터 준비
    portfolio_data = request.model_dump(exclude_unset=True, by_alias=False)
    
    # websiteUrl을 youtube_url로 매핑 (프론트엔드 호환성)
    if "website_url" in portfolio_data and portfolio_data["website_url"] and not portfolio_data.get("youtube_url"):
        portfolio_data["youtube_url"] = portfolio_data["website_url"]
        portfolio_data["website_url"] = None
    
    # Portfolio 모델에 없는 필드 제거 (안전성)
    from app.models.portfolio import Portfolio
    portfolio_fields = {col.name for col in Portfolio.__table__.columns}
    portfolio_data = {k: v for k, v in portfolio_data.items() if k in portfolio_fields}
    
    # 서비스를 통한 포트폴리오 생성
    portfolio = create_portfolio(db, user_id, portfolio_data)
    
    data = portfolio_to_model_dict(portfolio)
    return success_response({"data": data}, status_code=status.HTTP_201_CREATED)


@router.put("/{model_id}")
async def update_model(
    model_id: str,
    request: ModelUpdate,
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db)
):
    """
    모델 정보 수정
    showhost 역할만 가능, 본인 포트폴리오만 수정 가능
    """
    user_id = current_user.get("sub")
    user_role = current_user.get("role")
    
    # 갤러리 이미지 개수 검증 (모델은 최대 5개)
    if request.sub_thumbnail_urls is not None and len(request.sub_thumbnail_urls) > 5:
        error = get_error_message("PORTFOLIO_TOO_MANY_IMAGES")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PORTFOLIO_TOO_MANY_IMAGES",
                "message": error["message"],
                "userMessage": "갤러리 이미지는 최대 5개까지 등록할 수 있습니다.",
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
    
    update_data = request.model_dump(exclude_unset=True, by_alias=False)
    
    # websiteUrl을 youtube_url로 매핑 (프론트엔드 호환성)
    if "website_url" in update_data and update_data["website_url"] and not update_data.get("youtube_url"):
        update_data["youtube_url"] = update_data["website_url"]
        update_data["website_url"] = None
    
    # Portfolio 모델에 있는 필드만 업데이트 (안전성)
    from app.models.portfolio import Portfolio
    portfolio_fields = {col.name for col in Portfolio.__table__.columns}
    update_data = {k: v for k, v in update_data.items() if k in portfolio_fields}
    
    # 서비스를 통한 포트폴리오 수정
    portfolio = update_portfolio(db, model_id, user_id, user_role, update_data)
    
    data = portfolio_to_model_dict(portfolio)
    return success_response({"data": data})


@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db)
):
    """
    모델 삭제
    showhost 역할만 가능, 본인 포트폴리오만 삭제 가능
    """
    user_id = current_user.get("sub")
    user_role = current_user.get("role")
    
    # 서비스를 통한 포트폴리오 삭제
    delete_portfolio(db, model_id, user_id, user_role)
    
    return success_response({"message": "모델이 성공적으로 삭제되었습니다."})

