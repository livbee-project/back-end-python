"""
Campaign 도메인 스키마
캠페인/공고 관련 요청/응답
"""
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    is_public: Optional[bool] = Field(True, alias="isPublic")
    brand_name: str = Field(..., alias="brandName")
    brand_introduction: Optional[str] = Field(None, alias="brandIntroduction")
    prefix: Optional[str] = None
    title: str
    content: Optional[str] = None
    detailed_content: Optional[str] = Field(None, alias="detailedContent")
    category: Optional[str] = None
    location: Optional[str] = None
    shoot_date: date = Field(..., alias="shootDate")
    close_at: date = Field(..., alias="closeAt")
    duration_hours: Optional[float] = Field(None, alias="durationHours")
    start_time: str = Field(..., alias="startTime")
    end_time: str = Field(..., alias="endTime")
    fee: Optional[float] = None
    fee_negotiable: Optional[bool] = Field(False, alias="feeNegotiable")
    cover_image_url: Optional[str] = Field(None, alias="coverImageUrl")
    live_vertical_cover_url: Optional[str] = Field(None, alias="liveVerticalCoverUrl")
    product_thumbnail_url: Optional[str] = Field(None, alias="productThumbnailUrl")
    product_name: Optional[str] = Field(None, alias="productName")
    products: Optional[List[dict]] = None
    recruit: Optional[dict] = None
    qualifications: Optional[List[str]] = None

    class Config:
        populate_by_name = True


class CampaignUpdate(BaseModel):
    is_public: Optional[bool] = Field(None, alias="isPublic")
    brand_name: Optional[str] = Field(None, alias="brandName")
    brand_introduction: Optional[str] = Field(None, alias="brandIntroduction")
    prefix: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    detailed_content: Optional[str] = Field(None, alias="detailedContent")
    category: Optional[str] = None
    location: Optional[str] = None
    shoot_date: Optional[date] = Field(None, alias="shootDate")
    close_at: Optional[date] = Field(None, alias="closeAt")
    duration_hours: Optional[float] = Field(None, alias="durationHours")
    start_time: Optional[str] = Field(None, alias="startTime")
    end_time: Optional[str] = Field(None, alias="endTime")
    fee: Optional[float] = None
    fee_negotiable: Optional[bool] = Field(None, alias="feeNegotiable")
    cover_image_url: Optional[str] = Field(None, alias="coverImageUrl")
    live_vertical_cover_url: Optional[str] = Field(None, alias="liveVerticalCoverUrl")
    product_thumbnail_url: Optional[str] = Field(None, alias="productThumbnailUrl")
    product_name: Optional[str] = Field(None, alias="productName")
    products: Optional[List[dict]] = None
    recruit: Optional[dict] = None
    qualifications: Optional[List[str]] = None

    class Config:
        populate_by_name = True
