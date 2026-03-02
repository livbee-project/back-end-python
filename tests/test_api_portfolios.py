"""
포트폴리오 API 엔드포인트 통합 테스트
"""

import pytest


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


def test_get_portfolios_list(client):
    """포트폴리오 목록 조회 테스트"""
    response = client.get("/api/v1/portfolios")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"]
    assert "data" in data["data"]


def test_create_portfolio_success(client, showhost_user_token):
    """포트폴리오 생성 성공 테스트"""
    response = client.post(
        "/api/v1/portfolios",
        headers={"Authorization": f"Bearer {showhost_user_token}"},
        json={"nickname": "Test Model", "oneLineIntro": "Test intro", "status": "published"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["ok"]
    assert "data" in data["data"]


def test_get_portfolio_by_id(client, showhost_user_token):
    """포트폴리오 상세 조회 테스트"""
    # 포트폴리오 생성
    create_response = client.post(
        "/api/v1/portfolios",
        headers={"Authorization": f"Bearer {showhost_user_token}"},
        json={"nickname": "Test Model", "oneLineIntro": "Test intro", "status": "published"},
    )

    portfolio_id = create_response.json()["data"]["data"]["id"]

    # 조회
    response = client.get(f"/api/v1/portfolios/{portfolio_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"]
    assert data["data"]["data"]["id"] == portfolio_id


def test_get_my_portfolios(client, showhost_user_token):
    """내 포트폴리오 목록 조회 테스트"""
    # 포트폴리오 생성
    client.post(
        "/api/v1/portfolios",
        headers={"Authorization": f"Bearer {showhost_user_token}"},
        json={"nickname": "Test Model", "oneLineIntro": "Test intro", "status": "published"},
    )

    # 조회
    response = client.get(
        "/api/v1/portfolios/my/list", headers={"Authorization": f"Bearer {showhost_user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"]
    assert len(data["data"]["data"]) >= 1
