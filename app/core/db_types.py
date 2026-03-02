"""
SQLAlchemy 커스텀 타입
SQLite·PostgreSQL 양쪽 호환을 위한 타입 정의
"""

import json
from typing import Any, List

from sqlalchemy import String
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import TypeDecorator


class StringArray(TypeDecorator[List[str]]):
    """
    문자열 배열 타입.
    - PostgreSQL: 네이티브 ARRAY(String) 사용
    - SQLite: JSON 문자열로 직렬화하여 저장 (테스트 환경 호환)
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.ARRAY(String()))
        return dialect.type_descriptor(String(2000))

    def process_bind_param(self, value: List[str] | None, dialect: Any) -> str | List[str] | None:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return json.dumps(value)

    def process_result_value(self, value: str | List[str] | None, dialect: Any) -> List[str] | None:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return list(value) if value else []
        if isinstance(value, str):
            return json.loads(value) if value else []
        return value if isinstance(value, list) else []
