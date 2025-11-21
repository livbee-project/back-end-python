"""
공통 유틸리티 함수
"""
import re
import unicodedata
from typing import List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from app.core.config import settings


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


def format_date(date_obj) -> str:
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

