"""
포트폴리오 서비스 단위 테스트
"""

import uuid

import pytest
from fastapi import HTTPException

from app.models.user import UserRole
from app.services.portfolio_service import (
    check_user_has_portfolio,
    create_portfolio,
    delete_portfolio,
    get_portfolio_by_id,
    update_portfolio,
)


@pytest.fixture
def test_user(db_session):
    """테스트용 사용자 생성"""
    from app.services.user_service import create_user

    return create_user(
        db_session,
        name="Test User",
        email="test@example.com",
        password="password123",
        role=UserRole.SHOWHOST,
    )


def test_create_portfolio_success(db_session, test_user):
    """포트폴리오 생성 성공 테스트"""
    portfolio_data = {
        "nickname": "Test Model",
        "one_line_intro": "Test intro",
        "status": "published",
    }

    portfolio = create_portfolio(db_session, test_user.id, portfolio_data)

    assert portfolio is not None
    assert portfolio.user_id == test_user.id
    assert portfolio.nickname == "Test Model"


def test_create_portfolio_duplicate(db_session, test_user):
    """중복 포트폴리오 생성 실패 테스트"""
    portfolio_data = {"nickname": "Test Model", "status": "published"}

    # 첫 번째 포트폴리오 생성
    create_portfolio(db_session, test_user.id, portfolio_data)

    # 중복 생성 시도
    with pytest.raises(HTTPException) as exc_info:
        create_portfolio(db_session, test_user.id, portfolio_data)

    assert exc_info.value.status_code == 409


def test_get_portfolio_by_id_success(db_session, test_user):
    """포트폴리오 ID로 조회 성공 테스트"""
    portfolio_data = {"nickname": "Test Model", "status": "published"}

    created = create_portfolio(db_session, test_user.id, portfolio_data)
    portfolio = get_portfolio_by_id(db_session, created.id)

    assert portfolio is not None
    assert portfolio.id == created.id


def test_get_portfolio_by_id_not_found(db_session):
    """존재하지 않는 포트폴리오 조회 테스트"""
    with pytest.raises(HTTPException) as exc_info:
        get_portfolio_by_id(db_session, str(uuid.uuid4()))

    assert exc_info.value.status_code == 404


def test_check_user_has_portfolio(db_session, test_user):
    """사용자 포트폴리오 존재 확인 테스트"""
    # 포트폴리오 없을 때
    assert not check_user_has_portfolio(db_session, test_user.id)

    # 포트폴리오 생성
    portfolio_data = {"nickname": "Test Model", "status": "published"}
    create_portfolio(db_session, test_user.id, portfolio_data)

    # 포트폴리오 있을 때
    assert check_user_has_portfolio(db_session, test_user.id)


def test_update_portfolio_success(db_session, test_user):
    """포트폴리오 수정 성공 테스트"""
    portfolio_data = {"nickname": "Test Model", "status": "published"}

    created = create_portfolio(db_session, test_user.id, portfolio_data)

    update_data = {"nickname": "Updated Model"}
    updated = update_portfolio(db_session, created.id, test_user.id, None, update_data)

    assert updated.nickname == "Updated Model"


def test_delete_portfolio_success(db_session, test_user):
    """포트폴리오 삭제 성공 테스트"""
    portfolio_data = {"nickname": "Test Model", "status": "published"}

    created = create_portfolio(db_session, test_user.id, portfolio_data)

    delete_portfolio(db_session, created.id, test_user.id, None)

    # 삭제 확인
    with pytest.raises(HTTPException):
        get_portfolio_by_id(db_session, created.id)
