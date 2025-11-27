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

