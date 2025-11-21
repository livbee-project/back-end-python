"""
Campaign 라우트
캠페인/공고 관리
"""
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func as sql_func
from app.core.database import get_db
from app.middleware.auth import get_current_user, get_optional_user
from app.middleware.role import require_role
from app.models.campaign import Campaign, ProductItem, Question
from app.models.application import Application
from app.models.user import User, UserRole
from app.utils.response import success_response, fail_response
from app.utils.common import (
    to_thumb,
    sanitize_html,
    category_to_code,
    code_to_category,
    strip_tags,
    truncate_text,
)
from app.utils.pagination import (
    normalize_pagination,
    apply_pagination,
    build_paginated_payload,
)
import uuid

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


class CampaignCreate(BaseModel):
    is_public: Optional[bool] = Field(True, alias="isPublic")
    brand_name: str = Field(..., alias="brandName")
    brand_introduction: Optional[str] = Field(None, alias="brandIntroduction")
    prefix: Optional[str] = None
    title: str
    content: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    shoot_date: date = Field(..., alias="shootDate")
    close_at: date = Field(..., alias="closeAt")
    duration_hours: Optional[float] = Field(None, alias="durationHours")
    start_time: str = Field(..., alias="startTime")
    end_time: str = Field(..., alias="endTime")
    fee: Optional[float] = None
    fee_negotiable: Optional[bool] = Field(False, alias="feeNegotiable")
    cover_image_url: Optional[str] = Field(None, alias="coverImageUrl")
    live_vertical_cover_url: Optional[str] = Field(None, alias="liveVerticalCoverUrl")
    live_stream_url: Optional[str] = Field(None, alias="liveStreamUrl")
    product_thumbnail_url: Optional[str] = Field(None, alias="productThumbnailUrl")
    product_name: Optional[str] = Field(None, alias="productName")
    product_url: Optional[str] = Field(None, alias="productUrl")
    products: Optional[List[dict]] = None
    recruit: Optional[dict] = None

    class Config:
        populate_by_name = True


class CampaignUpdate(BaseModel):
    is_public: Optional[bool] = Field(None, alias="isPublic")
    brand_name: Optional[str] = Field(None, alias="brandName")
    brand_introduction: Optional[str] = Field(None, alias="brandIntroduction")
    prefix: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    shoot_date: Optional[date] = Field(None, alias="shootDate")
    close_at: Optional[date] = Field(None, alias="closeAt")
    duration_hours: Optional[float] = Field(None, alias="durationHours")
    start_time: Optional[str] = Field(None, alias="startTime")
    end_time: Optional[str] = Field(None, alias="endTime")
    fee: Optional[float] = None
    fee_negotiable: Optional[bool] = Field(None, alias="feeNegotiable")
    cover_image_url: Optional[str] = Field(None, alias="coverImageUrl")
    live_vertical_cover_url: Optional[str] = Field(None, alias="liveVerticalCoverUrl")
    live_stream_url: Optional[str] = Field(None, alias="liveStreamUrl")
    product_thumbnail_url: Optional[str] = Field(None, alias="productThumbnailUrl")
    product_name: Optional[str] = Field(None, alias="productName")
    product_url: Optional[str] = Field(None, alias="productUrl")
    products: Optional[List[dict]] = None
    recruit: Optional[dict] = None

    class Config:
        populate_by_name = True


@router.get("/meta")
async def get_campaign_meta(db: Session = Depends(get_db)):
    """
    공고 생성 및 검색에 필요한 메타데이터 제공
    """
    product_cats = ["뷰티", "가전", "음식", "패션", "리빙", "생활", "디지털"]
    recruit_cats = ["뷰티", "가전", "음식", "패션", "리빙", "일반"]

    # 브랜드 목록 집계
    brands_result = db.query(
        Campaign.brand_name,
        sql_func.count(Campaign.id).label("count")
    ).filter(
        Campaign.brand_name.isnot(None),
        Campaign.brand_name != ""
    ).group_by(Campaign.brand_name).order_by(
        desc(sql_func.count(Campaign.id)),
        Campaign.brand_name
    ).limit(50).all()

    brands = [{"name": name, "count": count} for name, count in brands_result]

    return success_response({
        "data": {
            "categories": {"product": product_cats, "recruit": recruit_cats},
            "brands": brands,
            "updatedAt": datetime.utcnow().isoformat(),
        }
    })


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_campaign(
    request: CampaignCreate,
    current_user: dict = Depends(require_role(UserRole.BRAND.value, "admin")),
    db: Session = Depends(get_db)
):
    """
    새로운 모집 공고 생성
    """
    user_id = current_user.get("sub")

    # 카테고리 변환
    category_korean = category_to_code(request.category) if request.category else None
    if category_korean:
        category_korean = code_to_category(category_korean) or request.category

    # durationHours 자동 계산
    duration_hours = request.duration_hours
    if not duration_hours and request.start_time and request.end_time:
        try:
            start = datetime.strptime(request.start_time, "%H:%M")
            end = datetime.strptime(request.end_time, "%H:%M")
            if end < start:
                # 다음날로 넘어가는 경우
                from datetime import timedelta
                end = end + timedelta(days=1)
            duration_hours = (end - start).total_seconds() / 3600
        except Exception:
            pass

    # 콘텐츠 sanitize
    content = sanitize_html(request.content) if request.content else None
    brand_introduction = sanitize_html(request.brand_introduction) if request.brand_introduction else None

    # 썸네일 자동 생성
    thumbnail_url = None
    if request.cover_image_url:
        thumbnail_url = to_thumb(request.cover_image_url)

    # 캠페인 데이터 생성
    campaign_data = {
        "id": str(uuid.uuid4()),
        "is_public": request.is_public if request.is_public is not None else True,
        "brand_name": request.brand_name,
        "brand_introduction": brand_introduction,
        "prefix": request.prefix,
        "title": request.title,
        "content": content,
        "category": category_korean,
        "location": request.location,
        "shoot_date": request.shoot_date,
        "close_at": request.close_at,
        "duration_hours": duration_hours,
        "start_time": request.start_time,
        "end_time": request.end_time,
        "fee": request.fee,
        "fee_negotiable": request.fee_negotiable or False,
        "cover_image_url": request.cover_image_url,
        "thumbnail_url": thumbnail_url,
        "live_vertical_cover_url": request.live_vertical_cover_url,
        "live_stream_url": request.live_stream_url,
        "product_thumbnail_url": request.product_thumbnail_url,
        "product_name": request.product_name,
        "product_url": request.product_url,
        "created_by": user_id,
        "metrics": {"views": 0, "clicks": 0, "applications": 0},
    }

    campaign = Campaign(**campaign_data)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    # 상품 및 질문 추가
    if request.products:
        for product_data in request.products:
            product = ProductItem(
                id=str(uuid.uuid4()),
                campaign_id=campaign.id,
                **product_data
            )
            db.add(product)

    if request.recruit and request.recruit.get("questions"):
        for question_data in request.recruit["questions"]:
            question = Question(
                id=str(uuid.uuid4()),
                campaign_id=campaign.id,
                **question_data
            )
            db.add(question)

    db.commit()

    data = {"id": campaign.id, **{k: v for k, v in campaign.__dict__.items() if not k.startswith("_")}}
    return success_response({"data": data}, status_code=status.HTTP_201_CREATED)


@router.get("")
async def get_campaigns(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    search: Optional[str] = None,
    sort: Optional[str] = Query(None, regex="^(deadline|latest|created)$"),
    current_user: Optional[dict] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    모집 공고 목록 조회 (검색, 정렬, 페이지네이션)
    """
    page, limit = normalize_pagination(page, limit, max_limit=50)

    query = db.query(Campaign).filter(
        Campaign.is_public == True,
        Campaign.close_at >= date.today()
    )

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Campaign.title.ilike(search_term),
                Campaign.content.ilike(search_term),
                Campaign.brand_name.ilike(search_term)
            )
        )

    if sort == "deadline":
        query = query.order_by(Campaign.close_at.asc())
    else:
        query = query.order_by(desc(Campaign.created_at))

    total_items = query.count()
    campaigns = apply_pagination(query, page, limit).all()

    applied_campaign_ids = set()
    if current_user and campaigns:
        user_id = current_user.get("sub")
        campaign_ids = [c.id for c in campaigns]
        applications = db.query(Application.campaign_id).filter(
            Application.user_id == user_id,
            Application.campaign_id.in_(campaign_ids)
        ).all()
        applied_campaign_ids = {app.campaign_id for app in applications}

    items = []
    for campaign in campaigns:
        item = {"id": campaign.id, **{k: v for k, v in campaign.__dict__.items() if not k.startswith("_")}}
        item["isAd"] = False
        item["isApplied"] = campaign.id in applied_campaign_ids
        item["summary"] = truncate_text(strip_tags(campaign.content), limit=220)
        items.append(item)

    return success_response(build_paginated_payload(items, total_items, page, limit))


@router.get("/mine")
async def get_my_campaigns(
    current_user: dict = Depends(require_role(UserRole.BRAND.value, "admin")),
    db: Session = Depends(get_db)
):
    """
    현재 로그인된 사용자가 생성한 모든 공고 목록 조회
    """
    user_id = current_user.get("sub")
    campaigns = db.query(Campaign).filter(
        Campaign.created_by == user_id
    ).order_by(desc(Campaign.created_at)).all()

    items = [{"id": c.id, **{k: v for k, v in c.__dict__.items() if not k.startswith("_")}} for c in campaigns]
    return success_response({"items": items})


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current_user: Optional[dict] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    특정 공고 상세 정보 조회
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND)

    # 로그인한 사용자의 지원 여부 확인
    is_applied = False
    if current_user:
        user_id = current_user.get("sub")
        application = db.query(Application).filter(
            Application.user_id == user_id,
            Application.campaign_id == campaign_id
        ).first()
        is_applied = application is not None

    data = {"id": campaign.id, **{k: v for k, v in campaign.__dict__.items() if not k.startswith("_")}}
    data["isApplied"] = is_applied
    return success_response({"data": data})


@router.put("/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    request: CampaignUpdate,
    current_user: dict = Depends(require_role(UserRole.BRAND.value, "admin")),
    db: Session = Depends(get_db)
):
    """
    특정 공고 정보 수정
    """
    user_id = current_user.get("sub")

    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.created_by == user_id
    ).first()

    if not campaign:
        return fail_response("RECRUIT_FORBIDDEN_EDIT", status.HTTP_403_FORBIDDEN)

    # 업데이트할 필드만 적용
    update_data = request.model_dump(exclude_unset=True, by_alias=False)

    # 콘텐츠 sanitize
    if "content" in update_data and update_data["content"]:
        update_data["content"] = sanitize_html(update_data["content"])
    if "brand_introduction" in update_data and update_data["brand_introduction"]:
        update_data["brand_introduction"] = sanitize_html(update_data["brand_introduction"])

    # 썸네일 자동 생성
    if "cover_image_url" in update_data and update_data["cover_image_url"] and not update_data.get("thumbnail_url"):
        update_data["thumbnail_url"] = to_thumb(update_data["cover_image_url"])

    for key, value in update_data.items():
        setattr(campaign, key, value)

    db.commit()
    db.refresh(campaign)

    data = {"id": campaign.id, **{k: v for k, v in campaign.__dict__.items() if not k.startswith("_")}}
    return success_response({"data": data})


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: dict = Depends(require_role(UserRole.BRAND.value, "admin")),
    db: Session = Depends(get_db)
):
    """
    특정 공고 삭제 (isPublic을 false로 변경)
    """
    user_id = current_user.get("sub")

    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.created_by == user_id
    ).first()

    if not campaign:
        return fail_response("RECRUIT_FORBIDDEN_DELETE", status.HTTP_403_FORBIDDEN)

    campaign.is_public = False
    db.commit()

    return success_response({"message": "삭제 완료"})

