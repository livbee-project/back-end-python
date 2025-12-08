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
from app.services.campaign_service import (
    get_campaign_by_id,
    get_user_campaigns,
    check_campaign_ownership,
    check_application_exists,
    get_campaigns_with_applied_status
)
from app.utils.common import (
    to_thumb,
    sanitize_html,
    code_to_category,
    prefix_to_korean,
    strip_tags,
    truncate_text,
    model_to_dict,
    models_to_list,
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
    detailed_content: Optional[str] = Field(None, alias="detailedContent")
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
    product_thumbnail_url: Optional[str] = Field(None, alias="productThumbnailUrl")
    product_name: Optional[str] = Field(None, alias="productName")
    products: Optional[List[dict]] = None
    recruit: Optional[dict] = None
    qualifications: Optional[List[str]] = None

    class Config:
        populate_by_name = True


class CampaignUpdate(BaseModel):
    is_public: Optional[bool] = Field(None, alias="isPublic")
    brand_name: Optional[str] = Field(None, alias="brandName")
    brand_introduction: Optional[str] = Field(None, alias="brandIntroduction")
    prefix: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    detailed_content: Optional[str] = Field(None, alias="detailedContent")
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
    product_thumbnail_url: Optional[str] = Field(None, alias="productThumbnailUrl")
    product_name: Optional[str] = Field(None, alias="productName")
    products: Optional[List[dict]] = None
    recruit: Optional[dict] = None
    qualifications: Optional[List[str]] = None

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

    # 날짜 유효성 검증
    today = date.today()
    if request.shoot_date < today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="촬영일은 오늘 이후여야 합니다."
        )
    if request.close_at <= request.shoot_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="마감일은 촬영일보다 이후여야 합니다."
        )

    # 시간 유효성 검증
    try:
        start = datetime.strptime(request.start_time, "%H:%M")
        end = datetime.strptime(request.end_time, "%H:%M")
        # 다음날로 넘어가는 경우를 제외하고 end_time이 start_time보다 이후인지 확인
        if end < start:
            # 다음날로 넘어가는 경우는 허용 (자동 계산 로직에서 처리)
            pass
        elif end == start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="종료 시간은 시작 시간보다 이후여야 합니다."
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="시간 형식이 올바르지 않습니다. (HH:MM 형식)"
        )

    # prefix 영문 코드 → 한글 변환
    prefix_korean = prefix_to_korean(request.prefix) if request.prefix else None

    # 카테고리 변환 (영문 코드 → 한글)
    category_korean = code_to_category(request.category) if request.category else None
    if not category_korean and request.category:
        # 변환되지 않은 경우 (이미 한글이거나 잘못된 값) 원본 유지
        category_korean = request.category

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

    # 콘텐츠 sanitize (detailedContent 우선, 없으면 content 사용)
    detailed_content = sanitize_html(request.detailed_content) if request.detailed_content else None
    content = sanitize_html(request.content) if request.content else None
    # detailedContent가 없으면 content를 사용
    if not detailed_content and content:
        detailed_content = content
    brand_introduction = sanitize_html(request.brand_introduction) if request.brand_introduction else None

    # 썸네일 자동 생성
    thumbnail_url = None
    if request.cover_image_url:
        thumbnail_url = to_thumb(request.cover_image_url)

    # 자격 요건 필터링 (빈 문자열 제거)
    qualifications = None
    if request.qualifications:
        qualifications = [q for q in request.qualifications if q and q.strip()]

    # 캠페인 데이터 생성
    campaign_data = {
        "id": str(uuid.uuid4()),
        "is_public": request.is_public if request.is_public is not None else True,
        "brand_name": request.brand_name,
        "brand_introduction": brand_introduction,
        "prefix": prefix_korean,
        "title": request.title,
        "content": content,
        "detailed_content": detailed_content,
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
        "product_thumbnail_url": request.product_thumbnail_url,
        "product_name": request.product_name,
        "qualifications": qualifications if qualifications else None,
        "created_by": user_id,
        "metrics": {"views": 0, "clicks": 0, "applications": 0},
    }

    campaign = Campaign(**campaign_data)
    db.add(campaign)
    db.flush()

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

    db.refresh(campaign)

    data = model_to_dict(campaign)
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

    # 서비스를 통한 캠페인 목록 조회 (쿼리 최적화)
    user_id = current_user.get("sub") if current_user else None
    campaigns, total_items, applied_campaign_ids = get_campaigns_with_applied_status(
        db,
        page=page,
        limit=limit,
        search=search,
        sort=sort,
        user_id=user_id
    )

    items = []
    for campaign in campaigns:
        # 목록 조회 시 불필요한 필드 제외 (응답 크기 최적화)
        item = model_to_dict(
            campaign,
            exclude=['brand_introduction', 'detailed_content']
        )
        item["isAd"] = False
        item["isApplied"] = campaign.id in applied_campaign_ids
        # detailedContent 우선, 없으면 content 사용
        try:
            content_for_summary = campaign.detailed_content if campaign.detailed_content else campaign.content
            if content_for_summary and isinstance(content_for_summary, str):
                item["summary"] = truncate_text(strip_tags(content_for_summary), limit=220)
            else:
                item["summary"] = ""
        except Exception as e:
            # summary 생성 실패 시 빈 문자열로 처리
            item["summary"] = ""
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
    campaigns = get_user_campaigns(db, user_id)

    items = models_to_list(campaigns)
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
    campaign = get_campaign_by_id(db, campaign_id)

    # 로그인한 사용자의 지원 여부 확인
    is_applied = False
    if current_user:
        user_id = current_user.get("sub")
        is_applied = check_application_exists(db, campaign_id, user_id)

    data = model_to_dict(campaign)
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
    user_role = current_user.get("role")

    # 서비스를 통한 소유권 확인
    campaign = check_campaign_ownership(db, campaign_id, user_id, user_role)

    # 업데이트할 필드만 적용
    update_data = request.model_dump(exclude_unset=True, by_alias=False)

    # 날짜 유효성 검증 (업데이트되는 경우만)
    if "shoot_date" in update_data or "close_at" in update_data:
        shoot_date = update_data.get("shoot_date", campaign.shoot_date)
        close_at = update_data.get("close_at", campaign.close_at)
        today = date.today()
        
        if shoot_date < today:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="촬영일은 오늘 이후여야 합니다."
            )
        if close_at <= shoot_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="마감일은 촬영일보다 이후여야 합니다."
            )

    # 시간 유효성 검증 (업데이트되는 경우만)
    if "start_time" in update_data or "end_time" in update_data:
        start_time = update_data.get("start_time", campaign.start_time)
        end_time = update_data.get("end_time", campaign.end_time)
        try:
            start = datetime.strptime(start_time, "%H:%M")
            end = datetime.strptime(end_time, "%H:%M")
            if end < start:
                # 다음날로 넘어가는 경우는 허용
                pass
            elif end == start:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="종료 시간은 시작 시간보다 이후여야 합니다."
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="시간 형식이 올바르지 않습니다. (HH:MM 형식)"
            )

    # prefix 영문 코드 → 한글 변환
    if "prefix" in update_data and update_data["prefix"]:
        update_data["prefix"] = prefix_to_korean(update_data["prefix"])

    # 카테고리 변환 (영문 코드 → 한글)
    if "category" in update_data and update_data["category"]:
        category_korean = code_to_category(update_data["category"])
        if category_korean:
            update_data["category"] = category_korean

    # 콘텐츠 sanitize
    if "content" in update_data and update_data["content"]:
        update_data["content"] = sanitize_html(update_data["content"])
    if "detailed_content" in update_data and update_data["detailed_content"]:
        update_data["detailed_content"] = sanitize_html(update_data["detailed_content"])
    if "brand_introduction" in update_data and update_data["brand_introduction"]:
        update_data["brand_introduction"] = sanitize_html(update_data["brand_introduction"])

    # 썸네일 자동 생성
    if "cover_image_url" in update_data and update_data["cover_image_url"] and not update_data.get("thumbnail_url"):
        update_data["thumbnail_url"] = to_thumb(update_data["cover_image_url"])

    # 자격 요건 필터링 (빈 문자열 제거)
    if "qualifications" in update_data:
        if update_data["qualifications"]:
            qualifications = [q for q in update_data["qualifications"] if q and q.strip()]
            update_data["qualifications"] = qualifications if qualifications else None
        else:
            update_data["qualifications"] = None

    for key, value in update_data.items():
        setattr(campaign, key, value)

    db.refresh(campaign)

    data = model_to_dict(campaign)
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
    user_role = current_user.get("role")

    # 서비스를 통한 소유권 확인
    campaign = check_campaign_ownership(db, campaign_id, user_id, user_role)

    campaign.is_public = False

    return success_response({"message": "삭제 완료"})

