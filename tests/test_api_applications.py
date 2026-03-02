"""
지원서 API 엔드포인트 통합 테스트
"""

from datetime import date, timedelta

import pytest


@pytest.fixture
def brand_user_token(client):
    """브랜드 사용자 토큰 생성"""
    # 회원가입
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

    # 로그인
    response = client.post(
        "/api/v1/users/login", json={"email": "brand@example.com", "password": "password123"}
    )

    return response.json()["data"]["token"]


@pytest.fixture
def showhost_user_token(client):
    """쇼호스트 사용자 토큰 생성"""
    # 회원가입
    client.post(
        "/api/v1/users/signup",
        json={
            "name": "Showhost User",
            "email": "showhost@example.com",
            "password": "password123",
            "role": "showhost",
        },
    )

    # 로그인
    response = client.post(
        "/api/v1/users/login", json={"email": "showhost@example.com", "password": "password123"}
    )

    return response.json()["data"]["token"]


def _minimal_campaign_payload(shoot_date: date, close_at: date):
    """CampaignCreate 필수 필드를 포함한 최소 payload (test_api_campaigns와 동일)"""
    return {
        "title": "Test Campaign",
        "content": "Test content",
        "brandName": "Test Brand",
        "shootDate": shoot_date.isoformat(),
        "closeAt": close_at.isoformat(),
        "startTime": "09:00",
        "endTime": "18:00",
        "isPublic": True,
    }


@pytest.fixture
def test_campaign(client, brand_user_token):
    """테스트용 캠페인 생성"""
    shoot_date = date.today() + timedelta(days=14)
    close_at = date.today() + timedelta(days=7)
    response = client.post(
        "/api/v1/campaigns",
        headers={"Authorization": f"Bearer {brand_user_token}"},
        json=_minimal_campaign_payload(shoot_date, close_at),
    )

    return response.json()["data"]["data"]


def test_create_application_success(client, showhost_user_token, test_campaign):
    """지원서 생성 성공 테스트"""
    response = client.post(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {showhost_user_token}"},
        json={"campaignId": test_campaign["id"], "message": "Test application"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["ok"]
    assert "data" in data["data"]
    assert "chatRoomId" in data["data"]


def test_get_my_application(client, showhost_user_token, test_campaign):
    """내 지원서 조회 테스트"""
    # 지원서 생성
    client.post(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {showhost_user_token}"},
        json={"campaignId": test_campaign["id"], "message": "Test application"},
    )

    # 조회
    response = client.get(
        f"/api/v1/applications/mine?campaign_id={test_campaign['id']}",
        headers={"Authorization": f"Bearer {showhost_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"]
    assert data["data"]["data"] is not None
