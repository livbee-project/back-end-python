"""
공통 유효성 검증 유틸리티
날짜·시간·형식 등 도메인 검증 로직
"""
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any


class ValidationError(Exception):
    """유효성 검증 실패 시 사용하는 예외"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def validate_campaign_dates(
    shoot_date: date,
    close_at: date,
    today: Optional[date] = None,
) -> None:
    """
    캠페인 날짜 유효성 검증
    - shoot_date >= today
    - close_at < shoot_date

    Raises:
        ValidationError: 검증 실패 시
    """
    today = today or date.today()
    if shoot_date < today:
        raise ValidationError("촬영일은 오늘 이후여야 합니다.")
    if close_at >= shoot_date:
        raise ValidationError(
            "마감일은 촬영일보다 이전이어야 합니다. 같은 날은 허용되지 않습니다."
        )


def validate_time_range(start_time: str, end_time: str) -> None:
    """
    시간 범위 유효성 검증
    - HH:MM 형식 검증
    - end_time > start_time (같은 경우만 에러, 자정 넘김은 허용)

    Raises:
        ValidationError: 형식 오류 또는 end <= start 시
    """
    try:
        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")
        if end == start:
            raise ValidationError("종료 시간은 시작 시간보다 이후여야 합니다.")
    except ValueError:
        raise ValidationError("시간 형식이 올바르지 않습니다. (HH:MM 형식)")


def calculate_duration_hours(start_time: str, end_time: str) -> Optional[float]:
    """
    start_time, end_time으로 duration_hours 계산
    자정 넘김 시 다음날로 간주하여 계산

    Returns:
        시간(시간 단위 float) 또는 None (파싱 실패 시)
    """
    try:
        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")
        if end < start:
            end = end + timedelta(days=1)
        return (end - start).total_seconds() / 3600
    except (ValueError, TypeError):
        return None


def validate_portfolio_urls(
    website_url: Optional[str] = None,
    youtube_url: Optional[str] = None,
    instagram_url: Optional[str] = None,
    tiktok_url: Optional[str] = None,
    open_chat: Optional[str] = None,
    recent_lives: Optional[list] = None,
    validate_fn=None,
) -> Optional[str]:
    """
    포트폴리오 URL 필드 검증
    validate_fn(url) -> bool 형태의 검증 함수 사용 (common.validate_url 등)

    Returns:
        None (성공) 또는 에러 메시지
    """
    if validate_fn is None:
        from app.utils.common import validate_url
        validate_fn = validate_url

    url_fields = {
        "website_url": website_url,
        "youtube_url": youtube_url,
        "instagram_url": instagram_url,
        "tiktok_url": tiktok_url,
        "open_chat": open_chat,
    }
    for field_name, url_value in url_fields.items():
        if url_value and not validate_fn(url_value):
            return f"{field_name}의 URL 형식이 올바르지 않습니다."

    if recent_lives:
        for live in recent_lives:
            if isinstance(live, dict) and live.get("url") and not validate_fn(live["url"]):
                return "최근 라이브 방송 URL 형식이 올바르지 않습니다."

    return None


def validate_portfolio_contact(contact: Optional[str], validate_fn=None) -> Optional[str]:
    """
    포트폴리오 연락처(전화번호) 검증

    Returns:
        None (성공) 또는 에러 메시지
    """
    if not contact:
        return None
    if validate_fn is None:
        from app.utils.common import validate_phone_number
        validate_fn = validate_phone_number
    if not validate_fn(contact):
        return "연락처 전화번호 형식이 올바르지 않습니다."
    return None
