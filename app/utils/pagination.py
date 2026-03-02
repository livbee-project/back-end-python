"""
페이지네이션 유틸리티
"""

from math import ceil
from typing import Any, Dict, Tuple

DEFAULT_PAGE = 1
DEFAULT_LIMIT = 10
MAX_LIMIT = 50


def normalize_pagination(page: int, limit: int, max_limit: int = MAX_LIMIT) -> Tuple[int, int]:
    """
    페이지와 limit 값을 허용 범위 내로 정규화
    """
    normalized_page = page if page and page > 0 else DEFAULT_PAGE
    normalized_limit = limit if limit and limit > 0 else DEFAULT_LIMIT
    normalized_limit = min(normalized_limit, max_limit)
    return normalized_page, normalized_limit


def get_pagination_meta(total_items: int, page: int, limit: int) -> Dict[str, Any]:
    """
    표준 페이지네이션 메타데이터 생성
    """
    total_pages = ceil(total_items / limit) if total_items else 0
    return {
        "currentPage": page,
        "totalPages": total_pages,
        "totalItems": total_items,
        "limit": limit,
        "hasNextPage": page < total_pages,
        "hasPrevPage": page > 1,
    }


def apply_pagination(query, page: int, limit: int):
    """
    SQLAlchemy 쿼리에 offset/limit 적용
    """
    offset = (page - 1) * limit
    return query.offset(offset).limit(limit)


def build_paginated_payload(items: Any, total_items: int, page: int, limit: int) -> Dict[str, Any]:
    """
    items와 페이지네이션 메타를 결합한 응답 페이로드 생성
    """
    payload = {"items": items}
    payload.update(get_pagination_meta(total_items, page, limit))
    return payload
