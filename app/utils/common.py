"""
공통 유틸리티 함수
"""
import re
import unicodedata
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from bs4 import BeautifulSoup
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


def snake_to_camel(snake_str: str) -> str:
    """
    snake_case를 camelCase로 변환
    """
    components = snake_str.split('_')
    return components[0] + ''.join(x.capitalize() for x in components[1:])


def to_thumb(url: Optional[str] = "") -> str:
    """
    Cloudinary 썸네일 URL 생성
    """
    if not url:
        return ""

    try:
        url_str = str(url)
        parts = url_str.split("/upload/")
        if len(parts) == 2:
            return f"{parts[0]}/upload/{settings.CLOUDINARY_THUMB}/{parts[1]}"
        return url_str
    except Exception:
        return url_str if url else ""


def sanitize_html(html_content: Optional[str]) -> str:
    """
    HTML 콘텐츠를 안전하게 정리
    """
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    allowed_tags = [
        "p", "br", "strong", "em", "u", "b", "i", "a", "ul", "ol", "li",
        "img", "h1", "h2", "h3", "h4", "h5", "h6", "span", "div",
        "figure", "figcaption", "blockquote", "pre", "code"
    ]

    allowed_attrs = {
        "*": ["style", "class", "id"],
        "a": ["href", "target", "rel"],
        "img": ["src", "alt", "title", "width", "height"],
    }

    for tag in soup.find_all():
        if tag.name not in allowed_tags:
            tag.unwrap()
        else:
            attrs_to_keep = allowed_attrs.get(tag.name, allowed_attrs.get("*", []))
            tag.attrs = {k: v for k, v in tag.attrs.items() if k in attrs_to_keep}

    return str(soup)


def strip_tags(html_content: Optional[str]) -> str:
    """
    HTML 태그를 모두 제거하고 텍스트만 반환
    """
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(" ", strip=True)


def truncate_text(text: Optional[str], limit: int = 140, suffix: str = "…") -> str:
    """
    길이가 긴 텍스트를 지정된 길이로 자르고 말줄임표를 부여
    """
    if not text:
        return ""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + suffix


def mask_email(email: Optional[str]) -> str:
    """
    이메일 주소를 마스킹하여 일부만 노출
    """
    if not email or "@" not in email:
        return email or ""
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}"
    return f"{masked_local}@{domain}"


def mask_phone(phone: Optional[str]) -> str:
    """
    전화번호를 ###-****-#### 형태로 마스킹
    """
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 7:
        return phone
    prefix = digits[:3]
    suffix = digits[-4:]
    masked_middle = "*" * (len(digits) - len(prefix) - len(suffix))
    return f"{prefix}-{masked_middle}-{suffix}"


def normalize_phone_number(phone: Optional[str], country_code: str = "+82") -> str:
    """
    전화번호에서 숫자만 남기고 국제전화 형태(E.164)에 맞게 변환
    """
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if not digits:
        return ""
    if digits.startswith("0"):
        digits = digits[1:]
    cc = country_code.replace("+", "")
    return f"+{cc}{digits}"


def slugify(value: Optional[str], allow_unicode: bool = False) -> str:
    """
    문자열을 슬러그(소문자-하이픈) 형태로 변환
    """
    if not value:
        return ""
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower()).strip()
    return re.sub(r"[-\s]+", "-", value)


def extract_hashtags(text: Optional[str]) -> List[str]:
    """
    텍스트에서 해시태그(#hashtag) 목록 추출
    """
    if not text:
        return []
    tags = re.findall(r"#([\w가-힣]+)", text)
    return sorted({tag.lower() for tag in tags})


def format_date(date_obj: Any) -> str:
    """
    날짜를 'YYYY. MM. DD' 형식으로 변환
    """
    if not date_obj:
        return ""

    try:
        if isinstance(date_obj, datetime):
            return date_obj.strftime("%Y. %m. %d")
        if hasattr(date_obj, "strftime"):
            return date_obj.strftime("%Y. %m. %d")
        return str(date_obj)
    except Exception:
        return ""


# 카테고리 한글 → 영문 코드 매핑
CATEGORY_MAP = {
    "뷰티": "beauty",
    "패션": "fashion",
    "식품": "food",
    "가전": "electronics",
    "생활/리빙": "lifestyle",
}

PREFIX_MAP = {
    "showhost": "쇼호스트모집",
    "staff": "촬영스태프",
    "model": "모델모집",
    "other": "기타모집",
}


def category_to_code(category: Optional[str]) -> Optional[str]:
    """
    카테고리 한글명을 영문 코드로 변환
    """
    if not category:
        return None
    return CATEGORY_MAP.get(category)


def code_to_category(code: Optional[str]) -> Optional[str]:
    """
    영문 코드를 카테고리 한글명으로 변환
    """
    if not code:
        return None

    reverse_map = {v: k for k, v in CATEGORY_MAP.items()}
    return reverse_map.get(code)


def prefix_to_korean(prefix: Optional[str]) -> Optional[str]:
    """
    prefix 영문 코드를 한글 값으로 변환
    """
    if not prefix:
        return None
    
    # 이미 한글 값인 경우 그대로 반환
    if prefix in PREFIX_MAP.values():
        return prefix
    
    # 영문 코드인 경우 한글로 변환
    return PREFIX_MAP.get(prefix, prefix)


def model_to_dict(
    model: Union[DeclarativeBase, Any],
    exclude: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    exclude_private: bool = True,
    to_camel_case: bool = False
) -> Dict[str, Any]:
    """
    SQLAlchemy 모델을 딕셔너리로 변환
    
    Args:
        model: SQLAlchemy 모델 인스턴스
        exclude: 제외할 필드 목록
        include: 포함할 필드 목록 (지정 시 include만 포함)
        exclude_private: True인 경우 '_'로 시작하는 필드 제외
        to_camel_case: True인 경우 필드명을 camelCase로 변환
    
    Returns:
        딕셔너리 형태의 모델 데이터
    
    Example:
        data = model_to_dict(user)
        data = model_to_dict(user, exclude=['password'])
        data = model_to_dict(user, include=['id', 'name', 'email'])
        data = model_to_dict(user, to_camel_case=True)
    """
    if model is None:
        return {}
    
    exclude = exclude or []
    result = {}
    
    # 모델의 모든 속성 순회
    for key, value in model.__dict__.items():
        # private 필드 제외
        if exclude_private and key.startswith('_'):
            continue
        
        # exclude 목록에 있으면 제외
        if key in exclude:
            continue
        
        # include가 지정된 경우 include에 있는 것만 포함
        if include and key not in include:
            continue
        
        # 출력 키 결정 (camelCase 변환 여부)
        output_key = snake_to_camel(key) if to_camel_case else key
        
        # datetime, date 객체를 ISO 형식 문자열로 변환
        if isinstance(value, (datetime, date)):
            result[output_key] = value.isoformat() if value else None
        # Enum 객체를 값으로 변환
        elif hasattr(value, 'value'):
            result[output_key] = value.value
        # 일반 값은 그대로
        else:
            result[output_key] = value
    
    return result


def models_to_list(
    models: List[Union[DeclarativeBase, Any]],
    exclude: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    exclude_private: bool = True
) -> List[Dict[str, Any]]:
    """
    SQLAlchemy 모델 리스트를 딕셔너리 리스트로 변환
    
    Args:
        models: SQLAlchemy 모델 인스턴스 리스트
        exclude: 제외할 필드 목록
        include: 포함할 필드 목록
        exclude_private: True인 경우 '_'로 시작하는 필드 제외
    
    Returns:
        딕셔너리 리스트
    
    Example:
        items = models_to_list(users)
        items = models_to_list(applications, exclude=['message'])
    """
    return [
        model_to_dict(model, exclude=exclude, include=include, exclude_private=exclude_private)
        for model in models
    ]


def validate_url(url: Optional[str]) -> bool:
    """
    URL 형식 검증
    
    Args:
        url: 검증할 URL 문자열
    
    Returns:
        유효한 URL이면 True, 아니면 False
    """
    if not url:
        return True  # None이나 빈 문자열은 허용 (선택 필드)
    
    try:
        url_str = str(url).strip()
        if not url_str:
            return True
        
        # 기본적인 URL 형식 검증 (더 관대한 패턴)
        # http:// 또는 https://로 시작하는지 확인
        if not url_str.startswith(('http://', 'https://')):
            return False
        
        # 최소한의 도메인 형식 확인
        # http:// 또는 https:// 제거 후 남은 부분 확인
        url_without_scheme = url_str.split('://', 1)[1] if '://' in url_str else ''
        if not url_without_scheme or len(url_without_scheme.split('/')[0].split('.')) < 1:
            return False
        
        return True
    except Exception:
        # 예외 발생 시 False 반환 (안전하게 처리)
        return False


def validate_phone_number(phone: Optional[str]) -> bool:
    """
    전화번호 형식 검증 (한국 전화번호)
    
    Args:
        phone: 검증할 전화번호 문자열
    
    Returns:
        유효한 전화번호이면 True, 아니면 False
    """
    if not phone:
        return True  # None이나 빈 문자열은 허용 (선택 필드)
    
    # 숫자만 추출
    digits = re.sub(r'\D', '', phone)
    
    # 한국 전화번호: 10자리 또는 11자리 (휴대폰: 11자리, 일반전화: 10자리)
    if len(digits) < 10 or len(digits) > 11:
        return False
    
    # 휴대폰 번호: 010으로 시작하는 11자리
    if len(digits) == 11 and digits.startswith('010'):
        return True
    
    # 일반 전화번호: 지역번호로 시작하는 10자리
    if len(digits) == 10:
        # 지역번호 체크 (02, 031, 032, 033, 041, 042, 043, 044, 051, 052, 053, 054, 055, 061, 062, 063, 064)
        area_codes = ['02', '031', '032', '033', '041', '042', '043', '044', 
                     '051', '052', '053', '054', '055', '061', '062', '063', '064']
        if any(digits.startswith(code) for code in area_codes):
            return True
    
    return False