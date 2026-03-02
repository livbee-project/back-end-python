"""
News 라우트
뉴스/공지사항 관리
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.role import require_role
from app.models.user import UserRole
from app.schemas.news import NewsCreate, NewsUpdate
from app.services.news_service import (
    create_news as create_news_svc,
)
from app.services.news_service import (
    delete_news as delete_news_svc,
)
from app.services.news_service import (
    get_news_by_id,
)
from app.services.news_service import (
    get_news_list as get_news_list_svc,
)
from app.services.news_service import (
    update_news as update_news_svc,
)
from app.utils.common import model_to_dict, strip_tags, truncate_text
from app.utils.pagination import (
    build_paginated_payload,
    normalize_pagination,
)
from app.utils.response import success_response

router = APIRouter(prefix="/news", tags=["news"])


@router.get("")
async def get_news_list(
    page: int = Query(1, ge=1), limit: int = Query(10, ge=1), db: Session = Depends(get_db)
):
    """
    전체 뉴스 목록을 페이지네이션으로 조회
    """
    page, limit = normalize_pagination(page, limit, max_limit=50)

    # 서비스를 통한 뉴스 목록 조회
    news_items, total_items = get_news_list_svc(db, page, limit)

    items = []
    for news in news_items:
        payload = model_to_dict(news)
        payload["excerpt"] = truncate_text(strip_tags(news.content), limit=160)
        items.append(payload)

    return success_response(build_paginated_payload(items, total_items, page, limit))


@router.get("/{news_id}")
async def get_news(news_id: str, db: Session = Depends(get_db)):
    """
    특정 ID의 뉴스 상세 정보 조회
    """
    news_item = get_news_by_id(db, news_id)

    data = model_to_dict(news_item)
    return success_response({"data": data})


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_news(
    request: NewsCreate,
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db),
):
    """
    새로운 뉴스 생성
    """
    user_id = current_user.get("sub")

    # 서비스를 통한 뉴스 생성
    news_item = create_news_svc(
        db,
        title=request.title,
        content=request.content,
        created_by=user_id,
        image_url=str(request.image_url) if request.image_url else None,
    )

    data = model_to_dict(news_item)
    return success_response({"data": data}, status_code=status.HTTP_201_CREATED)


@router.put("/{news_id}")
async def update_news(
    news_id: str,
    request: NewsUpdate,
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db),
):
    """
    특정 ID의 뉴스 수정
    """
    update_data = request.model_dump(exclude_unset=True, by_alias=False)
    image_url = str(update_data["image_url"]) if update_data.get("image_url") else None

    # 서비스를 통한 뉴스 수정
    news_item = update_news_svc(
        db,
        news_id=news_id,
        title=update_data.get("title"),
        content=update_data.get("content"),
        image_url=image_url,
    )

    data = model_to_dict(news_item)
    return success_response({"data": data})


@router.delete("/{news_id}")
async def delete_news(
    news_id: str,
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db),
):
    """
    특정 ID의 뉴스 삭제
    """
    # 서비스를 통한 뉴스 삭제
    delete_news_svc(db, news_id)

    return success_response({"message": "뉴스가 성공적으로 삭제되었습니다."})
