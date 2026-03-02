"""
사용자 API 엔드포인트 통합 테스트
"""
import pytest
from app.models.user import UserRole


def test_signup_success(client):
    """회원가입 성공 테스트"""
    response = client.post(
        "/api/v1/users/signup",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123",
            "role": "showhost"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["ok"] == True
    assert "userId" in data["data"]


def test_signup_duplicate_email(client):
    """중복 이메일 회원가입 실패 테스트"""
    # 첫 번째 회원가입
    client.post(
        "/api/v1/users/signup",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123",
            "role": "showhost"
        }
    )
    
    # 중복 이메일로 회원가입 시도
    response = client.post(
        "/api/v1/users/signup",
        json={
            "name": "Another User",
            "email": "test@example.com",
            "password": "password123",
            "role": "showhost"
        }
    )
    
    assert response.status_code == 409
    data = response.json()
    assert data["ok"] == False


def test_login_success(client):
    """로그인 성공 테스트"""
    # 회원가입
    client.post(
        "/api/v1/users/signup",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123",
            "role": "showhost"
        }
    )
    
    # 로그인
    response = client.post(
        "/api/v1/users/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] == True
    assert "token" in data["data"]
    assert "user" in data["data"]


def test_login_invalid_credentials(client):
    """잘못된 자격증명으로 로그인 실패 테스트"""
    response = client.post(
        "/api/v1/users/login",
        json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["ok"] == False


def test_login_role_mismatch_brand_only_tries_showhost(client):
    """
    브랜드 전용 계정으로 role=showhost 로그인 시 403 ROLE_MISMATCH 반환
    응답 형식: ok, error, message, userMessage 최상위 필드 검증
    """
    # 브랜드 전용 계정 회원가입 (is_brand=True, is_showhost=False)
    client.post(
        "/api/v1/users/signup",
        json={
            "name": "Brand User",
            "email": "brand@example.com",
            "password": "brandpassword123",
            "role": "brand",
            "brandName": "Test Brand"
        }
    )
    
    # role=showhost로 로그인 시도 → 403 ROLE_MISMATCH
    response = client.post(
        "/api/v1/users/login",
        json={
            "email": "brand@example.com",
            "password": "brandpassword123",
            "role": "showhost"
        }
    )
    
    assert response.status_code == 403
    data = response.json()
    assert data["ok"] == False
    assert data["error"] == "ROLE_MISMATCH"
    assert "message" in data
    assert "userMessage" in data
    assert data["userMessage"] == "선택하신 역할과 계정 정보가 일치하지 않습니다."

