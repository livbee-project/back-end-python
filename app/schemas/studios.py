"""
Studio 도메인 스키마
스튜디오 관련 요청/응답
"""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class StudioCreate(BaseModel):
    brand_name: Optional[str] = Field(None, alias="brandName")
    one_line_intro: Optional[str] = Field(None, alias="oneLineIntro")
    detailed_intro: Optional[str] = Field(None, alias="detailedIntro")
    usage_info: Optional[str] = Field(None, alias="usageInfo")
    price_info: Optional[str] = Field(None, alias="priceInfo")
    main_thumbnail_url: Optional[str] = Field(None, alias="mainThumbnailUrl")
    background_image_url: Optional[str] = Field(None, alias="backgroundImageUrl")
    sub_thumbnail_urls: Optional[List[str]] = Field(None, alias="subThumbnailUrls")
    gallery_urls: Optional[List[str]] = Field(None, alias="galleryUrls")
    contact: Optional[Dict] = None
    location: Optional[Dict] = None
    weekly_schedule: Optional[Dict] = Field(None, alias="weeklySchedule")

    class Config:
        populate_by_name = True


class StudioUpdate(BaseModel):
    brand_name: Optional[str] = Field(None, alias="brandName")
    one_line_intro: Optional[str] = Field(None, alias="oneLineIntro")
    detailed_intro: Optional[str] = Field(None, alias="detailedIntro")
    usage_info: Optional[str] = Field(None, alias="usageInfo")
    price_info: Optional[str] = Field(None, alias="priceInfo")
    main_thumbnail_url: Optional[str] = Field(None, alias="mainThumbnailUrl")
    background_image_url: Optional[str] = Field(None, alias="backgroundImageUrl")
    sub_thumbnail_urls: Optional[List[str]] = Field(None, alias="subThumbnailUrls")
    gallery_urls: Optional[List[str]] = Field(None, alias="galleryUrls")
    contact: Optional[Dict] = None
    location: Optional[Dict] = None
    weekly_schedule: Optional[Dict] = Field(None, alias="weeklySchedule")

    class Config:
        populate_by_name = True
