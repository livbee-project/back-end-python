"""
News 도메인 스키마
뉴스/공지사항 관련 요청/응답
"""
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field


class NewsCreate(BaseModel):
    title: str
    content: str
    image_url: Optional[HttpUrl] = Field(None, alias="imageUrl")

    class Config:
        populate_by_name = True


class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[HttpUrl] = Field(None, alias="imageUrl")

    class Config:
        populate_by_name = True
