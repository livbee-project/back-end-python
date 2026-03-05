"""
카카오 로그인 API 통합 테스트
"""


def test_kakao_login_brand_then_showhost_not_found_for_role(client):
    """
    브랜드로만 가입된 계정이 showhost 역할로 카카오 로그인 시도할 때
    USER_NOT_FOUND_FOR_ROLE(404)를 반환해야 한다.
    """
    # 1) 브랜드 계정으로 이메일 회원가입
    signup_response = client.post(
        "/api/v1/users/signup",
        json={
            "name": "Brand User",
            "email": "brand-kakao@example.com",
            "password": "brandpassword123",
            "role": "brand",
            "brandName": "Test Brand",
        },
    )
    assert signup_response.status_code == 201
    signup_data = signup_response.json()
    assert signup_data["ok"]

    # 2) 같은 이메일로 brand 역할 카카오 로그인 → 성공
    login_brand_response = client.post(
        "/api/v1/auth/kakao/login",
        json={
            "kakaoId": "kakao-brand-123",
            "email": "brand-kakao@example.com",
            "name": "Brand User",
            "role": "brand",
        },
    )
    assert login_brand_response.status_code == 200
    login_brand_data = login_brand_response.json()
    assert login_brand_data["ok"]
    assert "token" in login_brand_data["data"]
    assert "user" in login_brand_data["data"]

    # 3) 동일 카카오 계정으로 showhost 역할 카카오 로그인 → 404 USER_NOT_FOUND_FOR_ROLE
    login_showhost_response = client.post(
        "/api/v1/auth/kakao/login",
        json={
            "kakaoId": "kakao-brand-123",
            "email": "brand-kakao@example.com",
            "name": "Brand User",
            "role": "showhost",
        },
    )
    assert login_showhost_response.status_code == 404
    login_showhost_data = login_showhost_response.json()
    assert not login_showhost_data["ok"]
    assert login_showhost_data["error"] == "USER_NOT_FOUND_FOR_ROLE"


def test_kakao_login_unknown_user_returns_user_not_found(client):
    """
    전혀 가입되지 않은 카카오/이메일 조합으로 로그인 시도 시
    USER_NOT_FOUND(404)를 반환해야 한다.
    """
    response = client.post(
        "/api/v1/auth/kakao/login",
        json={
            "kakaoId": "kakao-unknown-123",
            "email": "unknown-kakao@example.com",
            "name": "Unknown User",
            "role": "brand",
        },
    )

    assert response.status_code == 404
    data = response.json()
    assert not data["ok"]
    assert data["error"] == "USER_NOT_FOUND"
