"""
Redis 연결 및 SMS 인증번호 저장/조회
키 형식: sms:{phone_number}, TTL 180초. redis-py 사용.
"""

from typing import Optional

from redis import Redis

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

SMS_CODE_TTL_SECONDS = 180
SMS_KEY_PREFIX = "sms:"

_redis_client: Optional[Redis] = None
_redis_init_failed = False


def _make_sms_key(phone_number: str) -> str:
    """SMS 인증번호 Redis 키 생성. phone_number는 호출 측에서 정규화된 값 사용."""
    return f"{SMS_KEY_PREFIX}{phone_number}"


def get_redis() -> Optional[Redis]:
    """
    Redis 클라이언트 반환 (싱글톤, lazy 초기화).
    REDIS_URL이 없거나 연결 실패 시 None 반환. 앱 기동 시 Redis 필수 아님.
    """
    global _redis_client, _redis_init_failed

    if _redis_init_failed:
        return None
    if _redis_client is not None:
        return _redis_client

    url = getattr(settings, "REDIS_URL", None) or ""
    if not url or not url.strip():
        logger.warning("REDIS_URL not set, Redis client disabled")
        _redis_init_failed = True
        return None

    try:
        _redis_client = Redis.from_url(
            url,
            decode_responses=True,
        )
        _redis_client.ping()
        logger.info("Redis client connected")
        return _redis_client
    except Exception as e:
        logger.warning("Redis connection failed: %s", e, exc_info=True)
        _redis_init_failed = True
        _redis_client = None
        return None


def set_sms_code(phone_number: str, code: str) -> None:
    """SMS 인증번호 저장. TTL 180초. Redis 미사용 시 무시."""
    client = get_redis()
    if client is None:
        logger.debug("set_sms_code skipped (Redis unavailable)")
        return
    key = _make_sms_key(phone_number)
    try:
        client.set(key, code, ex=SMS_CODE_TTL_SECONDS)
    except Exception as e:
        logger.error("set_sms_code failed: %s", e, exc_info=True)


def get_sms_code(phone_number: str) -> Optional[str]:
    """SMS 인증번호 조회. 없거나 Redis 미사용 시 None."""
    client = get_redis()
    if client is None:
        return None
    key = _make_sms_key(phone_number)
    try:
        value = client.get(key)
        return value if value is None else str(value)
    except Exception as e:
        logger.error("get_sms_code failed: %s", e, exc_info=True)
        return None


def delete_sms_code(phone_number: str) -> None:
    """SMS 인증번호 삭제 (검증 성공 시 등). Redis 미사용 시 무시."""
    client = get_redis()
    if client is None:
        logger.debug("delete_sms_code skipped (Redis unavailable)")
        return
    key = _make_sms_key(phone_number)
    try:
        client.delete(key)
    except Exception as e:
        logger.error("delete_sms_code failed: %s", e, exc_info=True)
