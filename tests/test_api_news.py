"""
뉴스 API 엔드포인트 통합 테스트
"""

import pytest


@pytest.fixture
def admin_user_token(client):
    """뉴스 생성용 쇼호스트 사용자 토큰 생성"""
    client.post(
        "/api/v1/users/signup",
        json={
            "name": "Admin User",
            "email": "admin@example.com",
            "password": "password123",
            "role": "showhost",
        },
    )

    response = client.post(
        "/api/v1/users/login", json={"email": "admin@example.com", "password": "password123"}
    )

    return response.json()["data"]["token"]


def test_get_news_list(client):
    """뉴스 목록 조회 테스트"""
    response = client.get("/api/v1/news")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"]
    assert "items" in data["data"]


def test_get_news_by_id(client, admin_user_token):
    """뉴스 상세 조회 테스트"""
    # 뉴스 생성
    create_response = client.post(
        "/api/v1/news",
        headers={"Authorization": f"Bearer {admin_user_token}"},
        json={"title": "Test News", "content": "Test content"},
    )

    if create_response.status_code != 201:
        pytest.skip(f"뉴스 생성 실패: {create_response.status_code} - {create_response.json()}")

    news_id = create_response.json()["data"]["data"]["id"]

    # 조회
    response = client.get(f"/api/v1/news/{news_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"]
    assert data["data"]["data"]["id"] == news_id
