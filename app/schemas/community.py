"""
Community 도메인 스키마
커뮤니티 게시글 / 댓글 요청 스키마
"""

from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class CommunityPostCreate(BaseModel):
    """커뮤니티 게시글 생성 요청"""

    title: str
    content: str
    thumbnail_url: Optional[HttpUrl] = Field(None, alias="thumbnailUrl")
    category: Optional[str] = None

    class Config:
        populate_by_name = True


class CommunityPostUpdate(BaseModel):
    """커뮤니티 게시글 수정 요청"""

    title: Optional[str] = None
    content: Optional[str] = None
    thumbnail_url: Optional[HttpUrl] = Field(None, alias="thumbnailUrl")
    category: Optional[str] = None

    class Config:
        populate_by_name = True


class CommunityCommentCreate(BaseModel):
    """커뮤니티 댓글/대댓글 생성 요청"""

    content: str
    parent_id: Optional[str] = Field(None, alias="parentId")

    class Config:
        populate_by_name = True


class CommunityCommentUpdate(BaseModel):
    """커뮤니티 댓글/대댓글 수정 요청"""

    content: str
