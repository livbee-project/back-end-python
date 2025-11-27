"""
캠페인 API 엔드포인트 통합 테스트
"""
import pytest
from datetime import date, timedelta
from app.models.user import UserRole


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
            "brandName": "Test Brand"
        }
    )
    
    response = client.post(
        "/api/v1/users/login",
        json={
            "email": "brand@example.com",
            "password": "password123"
        }
    )
    
    return response.json()["data"]["token"]


def test_get_campaigns_list(client):
    """캠페인 목록 조회 테스트"""
    response = client.get("/api/v1/campaigns")
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] == True
    assert "data" in data["data"]


def test_create_campaign_success(client, brand_user_token):
    """캠페인 생성 성공 테스트"""
    response = client.post(
        "/api/v1/campaigns",
        headers={"Authorization": f"Bearer {brand_user_token}"},
        json={
            "title": "Test Campaign",
            "content": "Test content",
            "brandName": "Test Brand",
            "closeAt": (date.today() + timedelta(days=7)).isoformat(),
            "isPublic": True
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["ok"] == True
    assert "data" in data["data"]
    assert data["data"]["data"]["title"] == "Test Campaign"


def test_get_campaign_by_id(client, brand_user_token):
    """캠페인 상세 조회 테스트"""
    # 캠페인 생성
    create_response = client.post(
        "/api/v1/campaigns",
        headers={"Authorization": f"Bearer {brand_user_token}"},
        json={
            "title": "Test Campaign",
            "content": "Test content",
            "brandName": "Test Brand",
            "closeAt": (date.today() + timedelta(days=7)).isoformat(),
            "isPublic": True
        }
    )
    
    campaign_id = create_response.json()["data"]["data"]["id"]
    
    # 조회
    response = client.get(f"/api/v1/campaigns/{campaign_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] == True
    assert data["data"]["data"]["id"] == campaign_id


def test_get_my_campaigns(client, brand_user_token):
    """내 캠페인 목록 조회 테스트"""
    # 캠페인 생성
    client.post(
        "/api/v1/campaigns",
        headers={"Authorization": f"Bearer {brand_user_token}"},
        json={
            "title": "Test Campaign",
            "content": "Test content",
            "brandName": "Test Brand",
            "closeAt": (date.today() + timedelta(days=7)).isoformat(),
            "isPublic": True
        }
    )
    
    # 조회
    response = client.get(
        "/api/v1/campaigns/my",
        headers={"Authorization": f"Bearer {brand_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] == True
    assert len(data["data"]["data"]) >= 1

