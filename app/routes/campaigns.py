"""
Campaign 라우트
캠페인/공고 관리
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc
from sqlalchemy import func as sql_func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_optional_user
from app.middleware.role import require_role
from app.models.campaign import Campaign
from app.models.user import UserRole
from app.schemas.campaigns import CampaignCreate, CampaignUpdate
from app.services.campaign_service import (
    check_application_exists,
    check_campaign_ownership,
    get_campaign_by_id,
    get_campaigns_with_applied_status,
    get_user_campaigns,
)
from app.services.campaign_service import (
    create_campaign as create_campaign_service,
)
from app.services.campaign_service import (
    update_campaign as update_campaign_service,
)
from app.utils.common import (
    model_to_dict,
    models_to_list,
    strip_tags,
    truncate_text,
)
from app.utils.pagination import (
    build_paginated_payload,
    normalize_pagination,
)
from app.utils.response import success_response

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("/meta")
async def get_campaign_meta(db: Session = Depends(get_db)):
    """
    공고 생성 및 검색에 필요한 메타데이터 제공
    """
    product_cats = ["뷰티", "가전", "음식", "패션", "리빙", "생활", "디지털"]
    recruit_cats = ["뷰티", "가전", "음식", "패션", "리빙", "일반"]

    # 브랜드 목록 집계
    brands_result = (
        db.query(Campaign.brand_name, sql_func.count(Campaign.id).label("count"))
        .filter(Campaign.brand_name.isnot(None), Campaign.brand_name != "")
        .group_by(Campaign.brand_name)
        .order_by(desc(sql_func.count(Campaign.id)), Campaign.brand_name)
        .limit(50)
        .all()
    )

    brands = [{"name": name, "count": count} for name, count in brands_result]

    return success_response(
        {
            "data": {
                "categories": {"product": product_cats, "recruit": recruit_cats},
                "brands": brands,
                "updatedAt": datetime.utcnow().isoformat(),
            }
        }
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_campaign(
    request: CampaignCreate,
    current_user: dict = Depends(require_role(UserRole.BRAND.value, "admin")),
    db: Session = Depends(get_db),
):
    """
    새로운 모집 공고 생성
    """
    user_id = current_user.get("sub")
    campaign = create_campaign_service(db, request, user_id)
    data = model_to_dict(campaign)
    return success_response({"data": data}, status_code=status.HTTP_201_CREATED)


@router.get("")
async def get_campaigns(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    search: Optional[str] = None,
    sort: Optional[str] = Query(None, pattern="^(deadline|latest|created)$"),
    current_user: Optional[dict] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    모집 공고 목록 조회 (검색, 정렬, 페이지네이션)
    """
    page, limit = normalize_pagination(page, limit, max_limit=50)

    # 서비스를 통한 캠페인 목록 조회 (쿼리 최적화)
    user_id = current_user.get("sub") if current_user else None
    campaigns, total_items, applied_campaign_ids = get_campaigns_with_applied_status(
        db, page=page, limit=limit, search=search, sort=sort, user_id=user_id
    )

    items = []
    for campaign in campaigns:
        # 목록 조회 시 불필요한 필드 제외 (응답 크기 최적화)
        item = model_to_dict(campaign, exclude=["brand_introduction", "detailed_content"])
        # product_thumbnail_url 필드 명시적으로 포함 (프론트엔드 요청)
        if hasattr(campaign, "product_thumbnail_url"):
            item["product_thumbnail_url"] = campaign.product_thumbnail_url
        item["isAd"] = False
        item["isApplied"] = campaign.id in applied_campaign_ids
        # detailedContent 우선, 없으면 content 사용
        try:
            content_for_summary = (
                campaign.detailed_content if campaign.detailed_content else campaign.content
            )
            if content_for_summary and isinstance(content_for_summary, str):
                item["summary"] = truncate_text(strip_tags(content_for_summary), limit=220)
            else:
                item["summary"] = ""
        except Exception:
            # summary 생성 실패 시 빈 문자열로 처리
            item["summary"] = ""
        items.append(item)

    return success_response(build_paginated_payload(items, total_items, page, limit))


@router.get("/mine")
async def get_my_campaigns(
    current_user: dict = Depends(require_role(UserRole.BRAND.value, "admin")),
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
):
    """
    특정 공고 정보 수정
    """
    user_id = current_user.get("sub")
    user_role = current_user.get("role")

    campaign = check_campaign_ownership(db, campaign_id, user_id, user_role)
    update_data = request.model_dump(exclude_unset=True, by_alias=False)
    campaign = update_campaign_service(db, campaign, update_data)
    data = model_to_dict(campaign)
    return success_response({"data": data})


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: dict = Depends(require_role(UserRole.BRAND.value, "admin")),
    db: Session = Depends(get_db),
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
