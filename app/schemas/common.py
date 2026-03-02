"""
공통 스키마
페이지네이션 메타 등 여러 도메인에서 재사용되는 스키마
"""

from typing import Optional

from pydantic import BaseModel, Field


class PaginationMeta(BaseModel):
    """페이지네이션 메타데이터"""

    current_page: int = Field(..., alias="currentPage")
    total_pages: int = Field(..., alias="totalPages")
    total_items: int = Field(..., alias="totalItems")
    limit: Optional[int] = None
    has_next_page: Optional[bool] = Field(None, alias="hasNextPage")
    has_prev_page: Optional[bool] = Field(None, alias="hasPrevPage")

    class Config:
        populate_by_name = True
