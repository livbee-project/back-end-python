"""
Rate Limiting 설정
slowapi를 사용한 요청 제한
"""

import uuid

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings


def _key_func(request=None):
    """TESTING 시 매 요청마다 고유 키 반환 → rate limit 미적용"""
    if get_settings().TESTING:
        return str(uuid.uuid4())
    return get_remote_address(request)


limiter = Limiter(key_func=_key_func)
