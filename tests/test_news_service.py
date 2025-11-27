"""
뉴스 서비스 단위 테스트
"""
import pytest
from fastapi import HTTPException
from app.services.news_service import (
    get_news_list,
    get_news_by_id,
    create_news,
    update_news,
    delete_news
)
from app.models.news import News
from app.models.user import User, UserRole
import uuid


@pytest.fixture
def test_user(db_session):
    """테스트용 사용자 생성"""
    from app.services.user_service import create_user
    return create_user(
        db_session,
        name="Test User",
        email="test@example.com",
        password="password123",
        role=UserRole.BRAND
    )


@pytest.fixture
def test_news(db_session, test_user):
    """테스트용 뉴스 생성"""
    news = News(
        id=str(uuid.uuid4()),
        title="Test News",
        content="Test content",
        created_by=test_user.id
    )
    db_session.add(news)
    db_session.flush()
    return news


def test_get_news_list(db_session, test_news):
    """뉴스 목록 조회 테스트"""
    news_list, total = get_news_list(db_session, page=1, limit=10)
    
    assert len(news_list) == 1
    assert total == 1
    assert news_list[0].id == test_news.id


def test_get_news_list_pagination(db_session, test_user):
    """뉴스 목록 페이지네이션 테스트"""
    # 여러 뉴스 생성
    for i in range(5):
        news = News(
            id=str(uuid.uuid4()),
            title=f"News {i}",
            content=f"Content {i}",
            created_by=test_user.id
        )
        db_session.add(news)
    db_session.flush()
    
    # 첫 페이지
    news_list, total = get_news_list(db_session, page=1, limit=2)
    assert len(news_list) == 2
    assert total == 5
    
    # 두 번째 페이지
    news_list, total = get_news_list(db_session, page=2, limit=2)
    assert len(news_list) == 2


def test_get_news_by_id_success(db_session, test_news):
    """뉴스 ID로 조회 성공 테스트"""
    news = get_news_by_id(db_session, test_news.id)
    
    assert news is not None
    assert news.id == test_news.id
    assert news.title == "Test News"


def test_get_news_by_id_not_found(db_session):
    """존재하지 않는 뉴스 조회 테스트"""
    with pytest.raises(HTTPException) as exc_info:
        get_news_by_id(db_session, str(uuid.uuid4()))
    
    assert exc_info.value.status_code == 404


def test_create_news_success(db_session, test_user):
    """뉴스 생성 성공 테스트"""
    news = create_news(
        db_session,
        title="New News",
        content="New content",
        created_by=test_user.id,
        image_url="https://example.com/image.jpg"
    )
    
    assert news is not None
    assert news.title == "New News"
    assert news.content == "New content"
    assert news.created_by == test_user.id
    assert news.image_url == "https://example.com/image.jpg"


def test_update_news_success(db_session, test_news):
    """뉴스 수정 성공 테스트"""
    updated = update_news(
        db_session,
        news_id=test_news.id,
        title="Updated Title",
        content="Updated content"
    )
    
    assert updated.title == "Updated Title"
    assert updated.content == "Updated content"


def test_update_news_partial(db_session, test_news):
    """뉴스 부분 수정 테스트"""
    original_content = test_news.content
    updated = update_news(
        db_session,
        news_id=test_news.id,
        title="Updated Title"
    )
    
    assert updated.title == "Updated Title"
    assert updated.content == original_content  # 변경되지 않음


def test_delete_news_success(db_session, test_news):
    """뉴스 삭제 성공 테스트"""
    news_id = test_news.id
    delete_news(db_session, news_id)
    
    # 삭제 확인
    with pytest.raises(HTTPException):
        get_news_by_id(db_session, news_id)

