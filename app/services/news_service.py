"""
뉴스 관련 비즈니스 로직 서비스
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.news import News
from app.utils.db_helpers import get_or_404
import uuid


def get_news_list(
    db: Session,
    page: int = 1,
    limit: int = 10
) -> tuple[list[News], int]:
    """
    뉴스 목록 조회
    
    Args:
        db: 데이터베이스 세션
        page: 페이지 번호
        limit: 페이지당 항목 수
    
    Returns:
        (뉴스 리스트, 전체 개수) 튜플
    """
    skip = (page - 1) * limit
    query = db.query(News).order_by(desc(News.created_at))
    total_items = query.count()
    news_items = query.offset(skip).limit(limit).all()
    return news_items, total_items


def get_news_by_id(
    db: Session,
    news_id: str
) -> News:
    """
    뉴스 ID로 조회
    
    Args:
        db: 데이터베이스 세션
        news_id: 뉴스 ID
    
    Returns:
        뉴스 인스턴스
    
    Raises:
        HTTPException: 뉴스를 찾을 수 없는 경우
    """
    return get_or_404(
        db,
        News,
        lambda q: q.filter(News.id == news_id),
        error_key="NOT_FOUND"
    )


def create_news(
    db: Session,
    title: str,
    content: str,
    created_by: str,
    image_url: Optional[str] = None
) -> News:
    """
    뉴스 생성
    
    Args:
        db: 데이터베이스 세션
        title: 제목
        content: 내용
        created_by: 생성자 ID
        image_url: 이미지 URL
    
    Returns:
        생성된 뉴스 인스턴스
    """
    news_item = News(
        id=str(uuid.uuid4()),
        title=title,
        content=content,
        image_url=image_url,
        created_by=created_by
    )
    
    db.add(news_item)
    db.refresh(news_item)
    
    return news_item


def update_news(
    db: Session,
    news_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    image_url: Optional[str] = None
) -> News:
    """
    뉴스 수정
    
    Args:
        db: 데이터베이스 세션
        news_id: 뉴스 ID
        title: 제목
        content: 내용
        image_url: 이미지 URL
    
    Returns:
        수정된 뉴스 인스턴스
    
    Raises:
        HTTPException: 뉴스를 찾을 수 없는 경우
    """
    news_item = get_news_by_id(db, news_id)
    
    if title is not None:
        news_item.title = title
    if content is not None:
        news_item.content = content
    if image_url is not None:
        news_item.image_url = image_url
    
    db.refresh(news_item)
    
    return news_item


def delete_news(
    db: Session,
    news_id: str
) -> None:
    """
    뉴스 삭제
    
    Args:
        db: 데이터베이스 세션
        news_id: 뉴스 ID
    
    Raises:
        HTTPException: 뉴스를 찾을 수 없는 경우
    """
    news_item = get_news_by_id(db, news_id)
    db.delete(news_item)

