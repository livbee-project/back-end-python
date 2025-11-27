"""
News 라우트
뉴스/공지사항 관리
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, HttpUrl, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.role import require_role
from app.models.news import News
from app.models.user import User, UserRole
from app.utils.response import success_response, fail_response
from app.utils.common import strip_tags, truncate_text, model_to_dict
from app.services.news_service import (
    get_news_list,
    get_news_by_id,
    create_news,
    update_news,
    delete_news
)
from app.utils.pagination import (
    normalize_pagination,
    apply_pagination,
    build_paginated_payload,
)
import uuid

router = APIRouter(prefix="/news", tags=["news"])


class NewsCreate(BaseModel):
    title: str
    content: str
    image_url: Optional[HttpUrl] = Field(None, alias="imageUrl")

    class Config:
        populate_by_name = True


class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[HttpUrl] = Field(None, alias="imageUrl")

    class Config:
        populate_by_name = True


@router.get("")
async def get_news_list(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db)
):
    """
    전체 뉴스 목록을 페이지네이션으로 조회
    """
    page, limit = normalize_pagination(page, limit, max_limit=50)

    # 서비스를 통한 뉴스 목록 조회
    news_items, total_items = get_news_list(db, page, limit)

    items = []
    for news in news_items:
        payload = model_to_dict(news)
        payload["excerpt"] = truncate_text(strip_tags(news.content), limit=160)
        items.append(payload)

    return success_response(build_paginated_payload(items, total_items, page, limit))


@router.get("/{news_id}")
async def get_news(
    news_id: str,
    db: Session = Depends(get_db)
):
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
    db: Session = Depends(get_db)
):
    """
    새로운 뉴스 생성
    """
    user_id = current_user.get("sub")

    # 서비스를 통한 뉴스 생성
    news_item = create_news(
        db,
        title=request.title,
        content=request.content,
        created_by=user_id,
        image_url=str(request.image_url) if request.image_url else None
    )

    data = model_to_dict(news_item)
    return success_response({"data": data}, status_code=status.HTTP_201_CREATED)


@router.put("/{news_id}")
async def update_news(
    news_id: str,
    request: NewsUpdate,
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db)
):
    """
    특정 ID의 뉴스 수정
    """
    update_data = request.model_dump(exclude_unset=True, by_alias=False)
    image_url = str(update_data["image_url"]) if update_data.get("image_url") else None

    # 서비스를 통한 뉴스 수정
    news_item = update_news(
        db,
        news_id=news_id,
        title=update_data.get("title"),
        content=update_data.get("content"),
        image_url=image_url
    )

    data = model_to_dict(news_item)
    return success_response({"data": data})


@router.delete("/{news_id}")
async def delete_news(
    news_id: str,
    current_user: dict = Depends(require_role(UserRole.SHOWHOST.value)),
    db: Session = Depends(get_db)
):
    """
    특정 ID의 뉴스 삭제
    """
    # 서비스를 통한 뉴스 삭제
    delete_news(db, news_id)

    return success_response({"message": "뉴스가 성공적으로 삭제되었습니다."})

