"""
제안 API 엔드포인트 통합 테스트
"""

from datetime import date, timedelta

import pytest


@pytest.fixture
def brand_user_token(client):
    """브랜드 사용자 토큰 생성"""
    client.post(
        "/api/v1/users/signup",
        json={
            "name": "Brand User",
            "email": "brand@example.com",
            "password": "password123",
            "role": "brand",
            "brandName": "Test Brand",
        },
    )

    response = client.post(
        "/api/v1/users/login", json={"email": "brand@example.com", "password": "password123"}
    )

    return response.json()["data"]["token"]


@pytest.fixture
def showhost_user_token(client):
    """쇼호스트 사용자 토큰 생성"""
    client.post(
        "/api/v1/users/signup",
        json={
            "name": "Showhost User",
            "email": "showhost@example.com",
            "password": "password123",
            "role": "showhost",
        },
    )

    response = client.post(
        "/api/v1/users/login", json={"email": "showhost@example.com", "password": "password123"}
    )

    return response.json()["data"]["token"]


@pytest.fixture
def test_portfolio(client, showhost_user_token):
    """테스트용 포트폴리오 생성"""
    response = client.post(
        "/api/v1/portfolios",
        headers={"Authorization": f"Bearer {showhost_user_token}"},
        json={"nickname": "Test Model", "oneLineIntro": "Test intro", "status": "published"},
    )

    return response.json()["data"]["data"]


def test_create_proposal_success(client, brand_user_token, test_portfolio):
    """제안 생성 성공 테스트"""
    response = client.post(
        "/api/v1/proposals",
        headers={"Authorization": f"Bearer {brand_user_token}"},
        json={
            "targetPortfolioId": test_portfolio["id"],
            "brandName": "Test Brand",
            "shootingDate": (date.today() + timedelta(days=7)).isoformat(),
            "replyDeadline": (date.today() + timedelta(days=3)).isoformat(),
            "fee": 100000,
            "content": "Test proposal",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["ok"]
    assert "data" in data["data"]


def test_get_sent_proposals(client, brand_user_token, test_portfolio):
    """보낸 제안 목록 조회 테스트"""
    # 제안 생성
    client.post(
        "/api/v1/proposals",
        headers={"Authorization": f"Bearer {brand_user_token}"},
        json={
            "targetPortfolioId": test_portfolio["id"],
            "brandName": "Test Brand",
            "shootingDate": (date.today() + timedelta(days=7)).isoformat(),
            "replyDeadline": (date.today() + timedelta(days=3)).isoformat(),
        },
    )

    # 조회
    response = client.get(
        "/api/v1/proposals/sent", headers={"Authorization": f"Bearer {brand_user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"]
    assert len(data["data"]["data"]) >= 1


def test_get_received_proposals(client, brand_user_token, showhost_user_token, test_portfolio):
    """받은 제안 목록 조회 테스트"""
    # 제안 생성
    client.post(
        "/api/v1/proposals",
        headers={"Authorization": f"Bearer {brand_user_token}"},
        json={
            "targetPortfolioId": test_portfolio["id"],
            "brandName": "Test Brand",
            "shootingDate": (date.today() + timedelta(days=7)).isoformat(),
            "replyDeadline": (date.today() + timedelta(days=3)).isoformat(),
        },
    )

    # 조회
    response = client.get(
        "/api/v1/proposals/received", headers={"Authorization": f"Bearer {showhost_user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"]
    assert len(data["data"]["data"]) >= 1
