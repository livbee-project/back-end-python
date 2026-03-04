"""
사업자 진위확인 API 엔드포인트 통합 테스트
"""


def test_verify_business_success(client, monkeypatch):
    """정상 사업자번호일 때 valid=True 응답"""

    from app.routes import auth as auth_routes
    from app.services import business_verification_service

    def fake_verify_business(business_number: str, opening_date=None, representative_name=None):
        return business_verification_service.BusinessVerificationResult(
            business_number=business_number,
            valid=True,
            status="계속사업자",
            status_code="01",
            tax_type="부가가치세 일반과세자",
            tax_type_code="01",
            raw={},
        )

    monkeypatch.setattr(auth_routes, "verify_business", fake_verify_business)

    response = client.post(
        "/api/v1/auth/verify-business",
        json={
            "businessNumber": "123-45-67890",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["data"]["valid"] is True
    assert data["data"]["businessNumber"] == "1234567890"


def test_verify_business_invalid_number(client):
    """형식이 잘못된 사업자번호는 400 VALIDATION_FAILED"""

    response = client.post(
        "/api/v1/auth/verify-business",
        json={
            "businessNumber": "1234",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert data["ok"] is False
    assert data["error"] == "VALIDATION_FAILED"
