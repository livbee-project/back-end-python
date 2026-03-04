from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

"""
국세청 사업자등록정보 진위확인/상태조회 서비스 연동

공공데이터포털 국세청 사업자등록정보 상태조회 API를 감싸는 서비스 레이어.
현재는 사업자등록번호(b_no) 기준 상태조회(status)만 사용하며,
개업일자/대표자명은 향후 진위확인 API 연동 시 확장 가능하도록 인자로만 받고 있다.
"""


class BusinessVerificationError(Exception):
    """사업자 진위확인 API 호출/파싱 중 발생하는 도메인 전용 예외"""


@dataclass
class BusinessVerificationResult:
    business_number: str
    valid: bool
    status: Optional[str] = None
    status_code: Optional[str] = None
    tax_type: Optional[str] = None
    tax_type_code: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


def _build_status_url() -> str:
    base = settings.NTS_BUSINESS_API_BASE_URL
    if not base:
        raise BusinessVerificationError("NTS_BUSINESS_API_BASE_URL is not configured")
    return base.rstrip("/") + "/status"


def verify_business(
    business_number: str,
    opening_date: Optional[str] = None,
    representative_name: Optional[str] = None,
) -> BusinessVerificationResult:
    """
    사업자등록번호 기반 국세청 상태조회 API 호출.

    현재 구현:
        - 상태조회(status) 엔드포인트만 사용
        - 개업일자(opening_date), 대표자명(representative_name)는 향후 진위확인 API 연동 시 확장용
    """
    # 환경변수 설정 검증
    if not settings.NTS_BUSINESS_API_KEY:
        raise BusinessVerificationError("NTS_BUSINESS_API_KEY is not configured")

    url = _build_status_url()
    params = {
        "serviceKey": settings.NTS_BUSINESS_API_KEY,
        "returnType": "JSON",
    }
    payload = {
        "b_no": [business_number],
    }

    timeout_seconds = settings.NTS_BUSINESS_API_TIMEOUT_SECONDS or 5

    try:
        response = httpx.post(url, params=params, json=payload, timeout=timeout_seconds)
    except httpx.RequestError as exc:
        logger.exception("NTS business API request error: %s", exc)
        raise BusinessVerificationError("NTS business API request error") from exc

    if response.status_code != 200:
        logger.warning(
            "NTS business API HTTP error: status=%s body=%s",
            response.status_code,
            response.text[:500],
        )
        raise BusinessVerificationError(f"NTS business API returned HTTP {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        logger.exception("NTS business API JSON decode error: %s", exc)
        raise BusinessVerificationError("NTS business API returned invalid JSON") from exc

    # 공공데이터포털 응답 포맷 가정:
    # {
    #   "status": "OK",
    #   "count": 1,
    #   "data": [
    #       {
    #           "b_no": "0000000000",
    #           "b_stt": "계속사업자",
    #           "b_stt_cd": "01",
    #           "tax_type": "부가가치세 일반과세자",
    #           "tax_type_cd": "01",
    #           "end_dt": "",
    #           ...
    #       }
    #   ]
    # }
    items = data.get("data") or []
    if not isinstance(items, list):
        logger.warning("NTS business API unexpected data format: data=%s", data)
        raise BusinessVerificationError("NTS business API returned unexpected format")

    if not items:
        # 조회 결과가 없으면 유효하지 않은 사업자로 간주
        return BusinessVerificationResult(
            business_number=business_number,
            valid=False,
            raw=data,
        )

    item = items[0] or {}
    b_stt = item.get("b_stt")
    b_stt_cd = item.get("b_stt_cd")
    tax_type = item.get("tax_type")
    tax_type_cd = item.get("tax_type_cd")
    end_dt = (item.get("end_dt") or "").strip()

    # 간단한 유효성 기준:
    # - 상태 코드가 "01"(계속사업자)이고
    # - 폐업일자(end_dt)가 비어 있으면 유효한 사업자로 판단
    is_active = b_stt_cd == "01" and not end_dt

    logger.info(
        "NTS business verification: b_no=%s, b_stt=%s, b_stt_cd=%s, tax_type=%s, end_dt=%s, valid=%s",
        business_number,
        b_stt,
        b_stt_cd,
        tax_type,
        end_dt,
        is_active,
    )

    return BusinessVerificationResult(
        business_number=business_number,
        valid=is_active,
        status=b_stt,
        status_code=b_stt_cd,
        tax_type=tax_type,
        tax_type_code=tax_type_cd,
        raw=data,
    )
