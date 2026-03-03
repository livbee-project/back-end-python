"""
SMS 발송 유틸 (Solapi 연동)
인증번호 등 SMS 메시지 발송
"""

from solapi import SolapiMessageService
from solapi.model import RequestMessage

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

SMS_VERIFICATION_TEMPLATE = "[Livbee] 인증번호는 {code}입니다."


def send_sms_verification(phone_number: str, code: str) -> bool:
    """
    SMS 인증번호 발송.
    설정이 없거나 SMS_SKIP_SEND가 True면 실제 발송 없이 로그만 남기고 True 반환(로컬/테스트용).

    Args:
        phone_number: 수신 전화번호
        code: 인증번호

    Returns:
        성공 시 True, 실패 시 False (예외는 로그 후 False 반환, raise 하지 않음)
    """
    if not phone_number or not code:
        logger.warning("send_sms_verification: phone_number 또는 code가 비어 있음")
        return False

    skip = (
        settings.SMS_SKIP_SEND
        or not settings.SOLAPI_API_KEY
        or not settings.SOLAPI_API_SECRET
        or not settings.SOLAPI_SENDER_NUMBER
    )
    if skip:
        logger.info(
            "SMS 발송 스킵 (SMS_SKIP_SEND=%s 또는 Solapi 설정 없음): to=%s, code=%s",
            settings.SMS_SKIP_SEND,
            phone_number,
            code,
        )
        return True

    text = SMS_VERIFICATION_TEMPLATE.format(code=code)
    try:
        message_service = SolapiMessageService(
            api_key=settings.SOLAPI_API_KEY,
            api_secret=settings.SOLAPI_API_SECRET,
        )
        message = RequestMessage(
            from_=settings.SOLAPI_SENDER_NUMBER,
            to=phone_number,
            text=text,
        )
        message_service.send(message)
        logger.info("SMS 인증 발송 성공: to=%s", phone_number)
        return True
    except Exception as e:
        logger.exception("SMS 발송 예외: to=%s, error=%s", phone_number, e)
        return False
