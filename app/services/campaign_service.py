"""
캠페인 관련 비즈니스 로직 서비스
"""

import uuid
from datetime import date
from typing import Any, Dict, Optional, Set

from fastapi import HTTPException, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session, selectinload

from app.models.application import Application
from app.models.campaign import Campaign, ProductItem, Question
from app.utils.common import (
    code_to_category,
    prefix_to_korean,
    sanitize_html,
    to_thumb,
)
from app.utils.db_helpers import get_or_404, require_ownership_or_admin
from app.utils.validators import (
    ValidationError,
    calculate_duration_hours,
    validate_campaign_dates,
    validate_time_range,
)


def validate_and_prepare_campaign_data(
    request: Any,
    user_id: str,
) -> Dict[str, Any]:
    """
    캠페인 생성용 요청 데이터 검증 및 변환
    - 날짜·시간 유효성 검증
    - prefix/category 한글 변환
    - duration_hours 자동 계산
    - sanitize_html, 썸네일 생성, 자격요건 필터링

    Returns:
        DB 저장용 campaign_data 딕셔너리

    Raises:
        HTTPException: 검증 실패 시
    """
    today = date.today()

    # 날짜 유효성 검증
    try:
        validate_campaign_dates(request.shoot_date, request.close_at, today)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.message),
        ) from e

    # 시간 유효성 검증
    try:
        validate_time_range(request.start_time, request.end_time)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.message),
        ) from e

    # prefix 영문 코드 → 한글 변환
    prefix_korean = prefix_to_korean(request.prefix) if request.prefix else None

    # 카테고리 변환 (영문 코드 → 한글)
    category_korean = code_to_category(request.category) if request.category else None
    if not category_korean and request.category:
        category_korean = request.category

    # durationHours 자동 계산
    duration_hours = request.duration_hours
    if not duration_hours and request.start_time and request.end_time:
        calculated = calculate_duration_hours(request.start_time, request.end_time)
        duration_hours = round(calculated) if calculated is not None else 0
    duration_hours = round(duration_hours) if duration_hours is not None else 0

    # 콘텐츠 sanitize
    detailed_content = sanitize_html(request.detailed_content) if request.detailed_content else None
    content = sanitize_html(request.content) if request.content else None
    if not detailed_content and content:
        detailed_content = content
    brand_introduction = (
        sanitize_html(request.brand_introduction) if request.brand_introduction else None
    )

    # 썸네일 자동 생성
    thumbnail_url = to_thumb(request.cover_image_url) if request.cover_image_url else None

    # 자격 요건 필터링 (빈 문자열 제거)
    qualifications = None
    if request.qualifications:
        qualifications = [q for q in request.qualifications if q and q.strip()]
        qualifications = qualifications if qualifications else None

    return {
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
        "qualifications": qualifications,
        "created_by": user_id,
        "metrics": {"views": 0, "clicks": 0, "applications": 0},
    }


def prepare_campaign_update_data(
    update_data: Dict[str, Any],
    campaign: Campaign,
) -> Dict[str, Any]:
    """
    캠페인 업데이트용 데이터 검증 및 변환
    - 날짜·시간 유효성 검증 (해당 필드 업데이트 시)
    - prefix/category 한글 변환
    - sanitize_html, 썸네일 생성, 자격요건 필터링

    Returns:
        setattr 적용용 update_data 딕셔너리

    Raises:
        HTTPException: 검증 실패 시
    """
    today = date.today()

    # 날짜 유효성 검증 (업데이트되는 경우만)
    if "shoot_date" in update_data or "close_at" in update_data:
        shoot_date = update_data.get("shoot_date", campaign.shoot_date)
        close_at = update_data.get("close_at", campaign.close_at)
        try:
            validate_campaign_dates(shoot_date, close_at, today)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e.message),
            ) from e

    # 시간 유효성 검증 (업데이트되는 경우만)
    if "start_time" in update_data or "end_time" in update_data:
        start_time = update_data.get("start_time", campaign.start_time)
        end_time = update_data.get("end_time", campaign.end_time)
        try:
            validate_time_range(start_time, end_time)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e.message),
            ) from e

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
    if (
        "cover_image_url" in update_data
        and update_data["cover_image_url"]
        and not update_data.get("thumbnail_url")
    ):
        update_data["thumbnail_url"] = to_thumb(update_data["cover_image_url"])

    # 자격 요건 필터링 (빈 문자열 제거)
    if "qualifications" in update_data:
        if update_data["qualifications"]:
            qualifications = [q for q in update_data["qualifications"] if q and q.strip()]
            update_data["qualifications"] = qualifications if qualifications else None
        else:
            update_data["qualifications"] = None

    return update_data


def create_campaign(
    db: Session,
    request: Any,
    user_id: str,
) -> Campaign:
    """
    캠페인 생성 (검증·변환 후 DB 저장)

    Returns:
        생성된 Campaign 인스턴스
    """
    campaign_data = validate_and_prepare_campaign_data(request, user_id)

    campaign = Campaign(**campaign_data)
    db.add(campaign)
    db.flush()

    # 상품 및 질문 추가
    if hasattr(request, "products") and request.products:
        for product_data in request.products:
            product = ProductItem(
                id=str(uuid.uuid4()),
                campaign_id=campaign.id,
                **product_data,
            )
            db.add(product)

    if hasattr(request, "recruit") and request.recruit and request.recruit.get("questions"):
        for question_data in request.recruit["questions"]:
            question = Question(
                id=str(uuid.uuid4()),
                campaign_id=campaign.id,
                **question_data,
            )
            db.add(question)

    db.refresh(campaign)
    return campaign


def update_campaign(
    db: Session,
    campaign: Campaign,
    update_data: Dict[str, Any],
) -> Campaign:
    """
    캠페인 업데이트 (검증·변환 후 setattr 적용)
    products, recruit 등 관계 필드는 제외하고 Campaign 컬럼만 업데이트
    """
    prepared = prepare_campaign_update_data(update_data, campaign)
    campaign_columns = {col.name for col in Campaign.__table__.columns}
    for key, value in prepared.items():
        if key in campaign_columns:
            setattr(campaign, key, value)
    db.refresh(campaign)
    return campaign


def get_campaign_by_id(db: Session, campaign_id: str) -> Campaign:
    """
    캠페인 ID로 조회 (products, questions eager load로 N+1 방지)

    Args:
        db: 데이터베이스 세션
        campaign_id: 캠페인 ID

    Returns:
        캠페인 인스턴스

    Raises:
        HTTPException: 캠페인을 찾을 수 없는 경우
    """
    return get_or_404(
        db,
        Campaign,
        lambda q: q.options(
            selectinload(Campaign.products),
            selectinload(Campaign.questions),
        ).filter(Campaign.id == campaign_id),
        error_key="NOT_FOUND",
    )


def get_user_campaigns(db: Session, user_id: str) -> list[Campaign]:
    """
    사용자가 생성한 캠페인 목록 조회

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID

    Returns:
        캠페인 리스트
    """
    return (
        db.query(Campaign)
        .filter(Campaign.created_by == user_id)
        .order_by(desc(Campaign.created_at))
        .all()
    )


def check_campaign_ownership(
    db: Session, campaign_id: str, user_id: str, user_role: Optional[str] = None
) -> Campaign:
    """
    캠페인 소유권 확인

    Args:
        db: 데이터베이스 세션
        campaign_id: 캠페인 ID
        user_id: 사용자 ID
        user_role: 사용자 역할

    Returns:
        캠페인 인스턴스

    Raises:
        HTTPException: 캠페인을 찾을 수 없거나 권한이 없는 경우
    """
    campaign = get_campaign_by_id(db, campaign_id)
    require_ownership_or_admin(
        campaign, user_id, user_role, owner_field="created_by", error_key="FORBIDDEN"
    )
    return campaign


def check_application_exists(db: Session, campaign_id: str, user_id: str) -> bool:
    """
    사용자가 해당 캠페인에 지원했는지 확인

    Args:
        db: 데이터베이스 세션
        campaign_id: 캠페인 ID
        user_id: 사용자 ID

    Returns:
        지원 여부
    """
    application = (
        db.query(Application)
        .filter(Application.user_id == user_id, Application.campaign_id == campaign_id)
        .first()
    )
    return application is not None


def get_campaigns_with_applied_status(
    db: Session,
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    sort: Optional[str] = None,
    user_id: Optional[str] = None,
) -> tuple[list[Campaign], int, Set[str]]:
    """
    캠페인 목록 조회 (지원 여부 포함, 쿼리 최적화)

    Args:
        db: 데이터베이스 세션
        page: 페이지 번호
        limit: 페이지당 항목 수
        search: 검색어
        sort: 정렬 방식
        user_id: 사용자 ID (지원 여부 확인용)

    Returns:
        (캠페인 리스트, 전체 개수, 지원한 캠페인 ID 집합) 튜플
    """
    skip = (page - 1) * limit

    query = db.query(Campaign).filter(Campaign.is_public, Campaign.close_at >= date.today())

    # 검색 조건
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Campaign.title.ilike(search_term),
                Campaign.content.ilike(search_term),
                Campaign.brand_name.ilike(search_term),
            )
        )

    # 정렬
    if sort == "deadline":
        query = query.order_by(Campaign.close_at.asc())
    else:
        query = query.order_by(desc(Campaign.created_at))

    total_items = query.count()
    campaigns = query.offset(skip).limit(limit).all()

    # 지원 여부 확인 (배치 쿼리로 N+1 방지)
    applied_campaign_ids: Set[str] = set()
    if user_id and campaigns:
        campaign_ids = [c.id for c in campaigns]
        applications = (
            db.query(Application.campaign_id)
            .filter(Application.user_id == user_id, Application.campaign_id.in_(campaign_ids))
            .all()
        )
        applied_campaign_ids = {app.campaign_id for app in applications}

    return campaigns, total_items, applied_campaign_ids
