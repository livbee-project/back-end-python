"""
캠페인 API 엔드포인트 통합 테스트
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


def _minimal_campaign_payload(shoot_date: date, close_at: date):
    """CampaignCreate 필수 필드를 포함한 최소 payload"""
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


def test_get_campaigns_list(client):
    """캠페인 목록 조회 테스트"""
    response = client.get("/api/v1/campaigns")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"]
    assert "data" in data["data"]


def test_create_campaign_success(client, brand_user_token):
    """캠페인 생성 성공 테스트"""
    shoot_date = date.today() + timedelta(days=14)
    close_at = date.today() + timedelta(days=7)
    response = client.post(
        "/api/v1/campaigns",
        headers={"Authorization": f"Bearer {brand_user_token}"},
        json=_minimal_campaign_payload(shoot_date, close_at),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["ok"]
    assert "data" in data["data"]
    assert data["data"]["data"]["title"] == "Test Campaign"


def test_get_campaign_by_id(client, brand_user_token):
    """캠페인 상세 조회 테스트"""
    shoot_date = date.today() + timedelta(days=14)
    close_at = date.today() + timedelta(days=7)
    create_response = client.post(
        "/api/v1/campaigns",
        headers={"Authorization": f"Bearer {brand_user_token}"},
        json=_minimal_campaign_payload(shoot_date, close_at),
    )

    campaign_id = create_response.json()["data"]["data"]["id"]

    response = client.get(f"/api/v1/campaigns/{campaign_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"]
    assert data["data"]["data"]["id"] == campaign_id


def test_get_my_campaigns(client, brand_user_token):
    """내 캠페인 목록 조회 테스트"""
    shoot_date = date.today() + timedelta(days=14)
    close_at = date.today() + timedelta(days=7)
    client.post(
        "/api/v1/campaigns",
        headers={"Authorization": f"Bearer {brand_user_token}"},
        json=_minimal_campaign_payload(shoot_date, close_at),
    )

    response = client.get(
        "/api/v1/campaigns/my", headers={"Authorization": f"Bearer {brand_user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"]
    assert len(data["data"]["data"]) >= 1


def test_create_campaign_date_validation_close_at_after_shoot_date(client, brand_user_token):
    """closeAt >= shootDate 인 경우 400 에러와 메시지 검증"""
    shoot_date = date.today() + timedelta(days=7)
    close_at = date.today() + timedelta(days=14)
    payload = _minimal_campaign_payload(shoot_date, close_at)

    response = client.post(
        "/api/v1/campaigns", headers={"Authorization": f"Bearer {brand_user_token}"}, json=payload
    )

    assert response.status_code == 400
    data = response.json()
    assert "마감일은 촬영일보다 이전이어야 합니다" in data.get("userMessage", "")


def test_create_campaign_date_validation_same_day(client, brand_user_token):
    """closeAt == shootDate (같은 날) 인 경우 400 에러 검증"""
    same_day = date.today() + timedelta(days=14)
    payload = _minimal_campaign_payload(shoot_date=same_day, close_at=same_day)

    response = client.post(
        "/api/v1/campaigns", headers={"Authorization": f"Bearer {brand_user_token}"}, json=payload
    )

    assert response.status_code == 400
