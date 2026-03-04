from typing import Any, Dict

import httpx
import pytest

from app.core.config import settings
from app.services.business_verification_service import (
    BusinessVerificationError,
    BusinessVerificationResult,
    verify_business,
)


class DummyResponse:
    def __init__(self, status_code: int, json_data: Dict[str, Any]):
        self.status_code = status_code
        self._json_data = json_data
        self.text = str(json_data)

    def json(self) -> Dict[str, Any]:
        return self._json_data


def test_verify_business_active(monkeypatch):
    """계속사업자(활성) 상태일 때 valid=True 반환"""

    def fake_post(url, params=None, json=None, timeout=None):
        assert "status" in url
        assert json == {"b_no": ["1234567890"]}
        data = {
            "status": "OK",
            "count": 1,
            "data": [
                {
                    "b_no": "1234567890",
                    "b_stt": "계속사업자",
                    "b_stt_cd": "01",
                    "tax_type": "부가가치세 일반과세자",
                    "tax_type_cd": "01",
                    "end_dt": "",
                }
            ],
        }
        return DummyResponse(200, data)

    settings.NTS_BUSINESS_API_BASE_URL = "https://api.odcloud.kr/api/nts-businessman/v1"
    settings.NTS_BUSINESS_API_KEY = "test-key"

    monkeypatch.setattr(httpx, "post", fake_post)

    result = verify_business("1234567890")

    assert isinstance(result, BusinessVerificationResult)
    assert result.business_number == "1234567890"
    assert result.valid is True
    assert result.status_code == "01"
    assert result.tax_type_code == "01"


def test_verify_business_inactive(monkeypatch):
    """폐업 등 비활성 상태일 때 valid=False 반환"""

    def fake_post(url, params=None, json=None, timeout=None):
        data = {
            "status": "OK",
            "count": 1,
            "data": [
                {
                    "b_no": "1234567890",
                    "b_stt": "폐업자",
                    "b_stt_cd": "02",
                    "tax_type": "부가가치세 일반과세자",
                    "tax_type_cd": "01",
                    "end_dt": "20201231",
                }
            ],
        }
        return DummyResponse(200, data)

    settings.NTS_BUSINESS_API_BASE_URL = "https://api.odcloud.kr/api/nts-businessman/v1"
    settings.NTS_BUSINESS_API_KEY = "test-key"

    monkeypatch.setattr(httpx, "post", fake_post)

    result = verify_business("1234567890")

    assert result.valid is False
    assert result.status_code == "02"


def test_verify_business_no_result(monkeypatch):
    """조회 결과가 없으면 valid=False"""

    def fake_post(url, params=None, json=None, timeout=None):
        data = {
            "status": "OK",
            "count": 0,
            "data": [],
        }
        return DummyResponse(200, data)

    settings.NTS_BUSINESS_API_BASE_URL = "https://api.odcloud.kr/api/nts-businessman/v1"
    settings.NTS_BUSINESS_API_KEY = "test-key"

    monkeypatch.setattr(httpx, "post", fake_post)

    result = verify_business("1234567890")

    assert result.valid is False


def test_verify_business_http_error(monkeypatch):
    """HTTP 상태 코드가 200이 아니면 BusinessVerificationError 발생"""

    def fake_post(url, params=None, json=None, timeout=None):
        return DummyResponse(500, {"error": "SERVER_ERROR"})

    settings.NTS_BUSINESS_API_BASE_URL = "https://api.odcloud.kr/api/nts-businessman/v1"
    settings.NTS_BUSINESS_API_KEY = "test-key"

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(BusinessVerificationError):
        verify_business("1234567890")
