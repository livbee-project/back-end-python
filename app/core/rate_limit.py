"""
Rate Limiting 설정
slowapi를 사용한 요청 제한
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
