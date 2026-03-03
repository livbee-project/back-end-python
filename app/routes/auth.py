"""
Auth 라우트
SMS 인증 전용 (인증번호 발송·검증)
"""

import random

from fastapi import APIRouter, Request, status

from app.core.logging_config import get_logger
from app.core.rate_limit import limiter
from app.core.redis import delete_sms_code, get_redis, get_sms_code, set_sms_code
from app.schemas.auth import SendSmsRequest, VerifySmsRequest
from app.utils.common import normalize_phone_number
from app.utils.response import fail_response, success_response
from app.utils.sms import send_sms_verification

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/send-sms")
@limiter.limit("5/minute")
async def send_sms(request: Request, body: SendSmsRequest):
    """
    SMS 인증번호 발송.
    전화번호 정규화 후 6자리 코드 생성 → Redis 저장 → SMS 발송.
    """
    normalized = normalize_phone_number(body.phone_number)
    if not normalized:
        return fail_response("VALIDATION_FAILED", status.HTTP_400_BAD_REQUEST)

    if get_redis() is None:
        logger.warning("send_sms: Redis unavailable")
        return fail_response("REDIS_UNAVAILABLE", status.HTTP_503_SERVICE_UNAVAILABLE)

    code = "".join(str(random.randint(0, 9)) for _ in range(6))
    set_sms_code(normalized, code)

    if not send_sms_verification(normalized, code):
        logger.warning("send_sms: SMS 발송 실패 phone=%s", normalized[:6] + "***")
        return fail_response("SMS_SEND_FAILED", status.HTTP_502_BAD_GATEWAY)

    logger.info("SMS 인증번호 발송 완료: phone=%s***", normalized[:6])
    return success_response(message="인증번호를 발송했습니다.")


@router.post("/verify-sms")
async def verify_sms(request: Request, body: VerifySmsRequest):
    """
    SMS 인증번호 검증.
    Redis에 저장된 코드와 비교 후 일치하면 키 삭제하고 성공 응답.
    """
    normalized = normalize_phone_number(body.phone_number)
    if not normalized:
        return fail_response("VALIDATION_FAILED", status.HTTP_400_BAD_REQUEST)

    stored = get_sms_code(normalized)
    if stored is None or stored != body.code:
        logger.info("verify_sms: 불일치 또는 만료 phone=%s***", normalized[:6])
        return fail_response("SMS_VERIFY_FAILED", status.HTTP_400_BAD_REQUEST)

    delete_sms_code(normalized)
    logger.info("SMS 인증 성공: phone=%s***", normalized[:6])
    return success_response(message="인증에 성공했습니다.")
