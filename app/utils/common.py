"""
공통 유틸리티 함수
"""
import re
from typing import Optional
from datetime import datetime
import html
from bs4 import BeautifulSoup
from app.core.config import settings


def to_thumb(url: Optional[str] = "") -> str:
    """
    Cloudinary 썸네일 URL 생성
    
    Args:
        url: 원본 이미지 URL
    
    Returns:
        썸네일 URL
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
    
    Args:
        html_content: 원본 HTML 문자열
    
    Returns:
        정리된 HTML 문자열
    """
    if not html_content:
        return ""
    
    # BeautifulSoup을 사용한 HTML 정리
    soup = BeautifulSoup(html_content, "html.parser")
    
    # 허용할 태그 목록
    allowed_tags = [
        "p", "br", "strong", "em", "u", "b", "i", "a", "ul", "ol", "li",
        "img", "h1", "h2", "h3", "h4", "h5", "h6", "span", "div",
        "figure", "figcaption", "blockquote", "pre", "code"
    ]
    
    # 허용할 속성
    allowed_attrs = {
        "*": ["style", "class", "id"],
        "a": ["href", "target", "rel"],
        "img": ["src", "alt", "title", "width", "height"],
    }
    
    # 태그 정리
    for tag in soup.find_all():
        if tag.name not in allowed_tags:
            tag.unwrap()  # 태그 제거하되 내용은 유지
        else:
            # 허용되지 않는 속성 제거
            if tag.name in allowed_attrs:
                attrs_to_keep = allowed_attrs[tag.name]
            else:
                attrs_to_keep = allowed_attrs.get("*", [])
            
            tag.attrs = {
                k: v for k, v in tag.attrs.items()
                if k in attrs_to_keep
            }
    
    return str(soup)


def format_date(date: Optional[datetime]) -> str:
    """
    날짜를 'YYYY. MM. DD' 형식으로 변환
    
    Args:
        date: datetime 객체
    
    Returns:
        포맷된 날짜 문자열
    """
    if not date:
        return ""
    
    try:
        return date.strftime("%Y. %m. %d")
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
    
    Args:
        category: 한글 카테고리명
    
    Returns:
        영문 코드 또는 None
    """
    if not category:
        return None
    return CATEGORY_MAP.get(category)


def code_to_category(code: Optional[str]) -> Optional[str]:
    """
    영문 코드를 카테고리 한글명으로 변환
    
    Args:
        code: 영문 코드
    
    Returns:
        한글 카테고리명 또는 None
    """
    if not code:
        return None
    
    reverse_map = {v: k for k, v in CATEGORY_MAP.items()}
    return reverse_map.get(code)

