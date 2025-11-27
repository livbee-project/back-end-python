"""
사용자 서비스 단위 테스트
"""
import pytest
from fastapi import HTTPException
from app.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    authenticate_user
)
from app.models.user import User, UserRole


def test_create_user_success(db_session, test_user_data):
    """사용자 생성 성공 테스트"""
    user = create_user(
        db_session,
        name=test_user_data["name"],
        email=test_user_data["email"],
        password=test_user_data["password"],
        role=UserRole.SHOWHOST
    )
    
    assert user is not None
    assert user.email == test_user_data["email"]
    assert user.name == test_user_data["name"]
    assert user.role == UserRole.SHOWHOST
    assert user.password is not None  # 해시된 비밀번호


def test_create_user_duplicate_email(db_session, test_user_data):
    """중복 이메일로 사용자 생성 실패 테스트"""
    # 첫 번째 사용자 생성
    create_user(
        db_session,
        name=test_user_data["name"],
        email=test_user_data["email"],
        password=test_user_data["password"],
        role=UserRole.SHOWHOST
    )
    
    # 중복 이메일로 사용자 생성 시도
    with pytest.raises(HTTPException) as exc_info:
        create_user(
            db_session,
            name="Another User",
            email=test_user_data["email"],
            password="password123",
            role=UserRole.SHOWHOST
        )
    
    assert exc_info.value.status_code == 409


def test_get_user_by_email_success(db_session, test_user_data):
    """이메일로 사용자 조회 성공 테스트"""
    # 사용자 생성
    created_user = create_user(
        db_session,
        name=test_user_data["name"],
        email=test_user_data["email"],
        password=test_user_data["password"],
        role=UserRole.SHOWHOST
    )
    
    # 이메일로 조회
    user = get_user_by_email(db_session, test_user_data["email"])
    
    assert user is not None
    assert user.id == created_user.id
    assert user.email == test_user_data["email"]


def test_get_user_by_email_not_found(db_session):
    """존재하지 않는 이메일로 조회 테스트"""
    user = get_user_by_email(db_session, "nonexistent@example.com")
    assert user is None


def test_authenticate_user_success(db_session, test_user_data):
    """사용자 인증 성공 테스트"""
    # 사용자 생성
    create_user(
        db_session,
        name=test_user_data["name"],
        email=test_user_data["email"],
        password=test_user_data["password"],
        role=UserRole.SHOWHOST
    )
    
    # 인증
    user, token = authenticate_user(
        db_session,
        email=test_user_data["email"],
        password=test_user_data["password"]
    )
    
    assert user is not None
    assert token is not None
    assert user.email == test_user_data["email"]


def test_authenticate_user_invalid_credentials(db_session, test_user_data):
    """잘못된 자격증명으로 인증 실패 테스트"""
    # 사용자 생성
    create_user(
        db_session,
        name=test_user_data["name"],
        email=test_user_data["email"],
        password=test_user_data["password"],
        role=UserRole.SHOWHOST
    )
    
    # 잘못된 비밀번호로 인증 시도
    with pytest.raises(HTTPException) as exc_info:
        authenticate_user(
            db_session,
            email=test_user_data["email"],
            password="wrongpassword"
        )
    
    assert exc_info.value.status_code == 401

