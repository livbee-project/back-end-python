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
    skip = (page - 1) * limit

    total_items = db.query(News).count()
    news_items = db.query(News).order_by(desc(News.created_at)).offset(skip).limit(limit).all()

    items = [{"id": n.id, **{k: v for k, v in n.__dict__.items() if not k.startswith("_")}} for n in news_items]
    total_pages = (total_items + limit - 1) // limit

    return success_response({
        "items": items,
        "currentPage": page,
        "totalPages": total_pages,
        "totalItems": total_items,
    })


@router.get("/{news_id}")
async def get_news(
    news_id: str,
    db: Session = Depends(get_db)
):
    """
    특정 ID의 뉴스 상세 정보 조회
    """
    news_item = db.query(News).filter(News.id == news_id).first()
    if not news_item:
        return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND)

    data = {"id": news_item.id, **{k: v for k, v in news_item.__dict__.items() if not k.startswith("_")}}
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

    news_item = News(
        id=str(uuid.uuid4()),
        title=request.title,
        content=request.content,
        image_url=str(request.image_url) if request.image_url else None,
        created_by=user_id
    )

    db.add(news_item)
    db.commit()
    db.refresh(news_item)

    data = {"id": news_item.id, **{k: v for k, v in news_item.__dict__.items() if not k.startswith("_")}}
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
    news_item = db.query(News).filter(News.id == news_id).first()
    if not news_item:
        return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND)

    update_data = request.model_dump(exclude_unset=True, by_alias=False)
    if "image_url" in update_data and update_data["image_url"]:
        update_data["image_url"] = str(update_data["image_url"])

    for key, value in update_data.items():
        setattr(news_item, key, value)

    db.commit()
    db.refresh(news_item)

    data = {"id": news_item.id, **{k: v for k, v in news_item.__dict__.items() if not k.startswith("_")}}
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
    news_item = db.query(News).filter(News.id == news_id).first()
    if not news_item:
        return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND)

    db.delete(news_item)
    db.commit()

    return success_response({"message": "뉴스가 성공적으로 삭제되었습니다."})

