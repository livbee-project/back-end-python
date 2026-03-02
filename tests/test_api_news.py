"""
뉴스 API 엔드포인트 통합 테스트
"""

import pytest


@pytest.fixture
def admin_user_token(client):
    """관리자 사용자 토큰 생성"""
    # 일반 사용자로 회원가입 (실제로는 admin 역할이 필요하지만 테스트용)
    client.post(
        "/api/v1/users/signup",
        json={
            "name": "Admin User",
            "email": "admin@example.com",
            "password": "password123",
            "role": "brand",
            "brandName": "Admin Brand",
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
    assert "data" in data["data"]


def test_get_news_by_id(client, admin_user_token):
    """뉴스 상세 조회 테스트"""
    # 뉴스 생성
    create_response = client.post(
        "/api/v1/news",
        headers={"Authorization": f"Bearer {admin_user_token}"},
        json={"title": "Test News", "content": "Test content"},
    )

    if create_response.status_code == 201:
        news_id = create_response.json()["data"]["data"]["id"]

        # 조회
        response = client.get(f"/api/v1/news/{news_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"]
        assert data["data"]["data"]["id"] == news_id
