"""
Model 도메인 스키마
모델 관련 요청/응답
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ModelCreate(BaseModel):
    nickname: Optional[str] = None
    one_line_intro: Optional[str] = Field(None, alias="oneLineIntro")
    detailed_intro: Optional[str] = Field(None, alias="detailedIntro")
    experience_years: Optional[int] = Field(None, alias="experienceYears")
    age: Optional[int] = None
    main_thumbnail_url: Optional[str] = Field(None, alias="mainThumbnailUrl")
    background_image_url: Optional[str] = Field(None, alias="backgroundImageUrl")
    sub_thumbnail_urls: Optional[List[str]] = Field(None, alias="subThumbnailUrls")
    status: Optional[str] = "published"
    is_age_public: Optional[bool] = Field(True, alias="isAgePublic")
    is_sizing_public: Optional[bool] = Field(True, alias="isSizingPublic")
    detailed_region: Optional[str] = Field(None, alias="detailedRegion")
    gender: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    top_size: Optional[str] = Field(None, alias="topSize")
    bottom_size: Optional[str] = Field(None, alias="bottomSize")
    shoe_size: Optional[int] = Field(None, alias="shoeSize")
    website_url: Optional[str] = Field(None, alias="websiteUrl")
    instagram_url: Optional[str] = Field(None, alias="instagramUrl")
    youtube_url: Optional[str] = Field(None, alias="youtubeUrl")
    tiktok_url: Optional[str] = Field(None, alias="tiktokUrl")
    contact: Optional[str] = None
    open_chat: Optional[str] = Field(None, alias="openChat")
    registration_type: Optional[str] = Field(None, alias="registrationType")
    public_scope: Optional[str] = Field("전체공개", alias="publicScope")
    is_receiving_offers: Optional[bool] = Field(True, alias="isReceivingOffers")
    attached_file_url: Optional[str] = Field(None, alias="attachedFileUrl")

    class Config:
        populate_by_name = True


class ModelUpdate(BaseModel):
    nickname: Optional[str] = None
    one_line_intro: Optional[str] = Field(None, alias="oneLineIntro")
    detailed_intro: Optional[str] = Field(None, alias="detailedIntro")
    experience_years: Optional[int] = Field(None, alias="experienceYears")
    age: Optional[int] = None
    main_thumbnail_url: Optional[str] = Field(None, alias="mainThumbnailUrl")
    background_image_url: Optional[str] = Field(None, alias="backgroundImageUrl")
    sub_thumbnail_urls: Optional[List[str]] = Field(None, alias="subThumbnailUrls")
    status: Optional[str] = None
    is_age_public: Optional[bool] = Field(None, alias="isAgePublic")
    is_sizing_public: Optional[bool] = Field(None, alias="isSizingPublic")
    detailed_region: Optional[str] = Field(None, alias="detailedRegion")
    gender: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    top_size: Optional[str] = Field(None, alias="topSize")
    bottom_size: Optional[str] = Field(None, alias="bottomSize")
    shoe_size: Optional[int] = Field(None, alias="shoeSize")
    website_url: Optional[str] = Field(None, alias="websiteUrl")
    instagram_url: Optional[str] = Field(None, alias="instagramUrl")
    youtube_url: Optional[str] = Field(None, alias="youtubeUrl")
    tiktok_url: Optional[str] = Field(None, alias="tiktokUrl")
    contact: Optional[str] = None
    open_chat: Optional[str] = Field(None, alias="openChat")
    registration_type: Optional[str] = Field(None, alias="registrationType")
    public_scope: Optional[str] = Field(None, alias="publicScope")
    is_receiving_offers: Optional[bool] = Field(None, alias="isReceivingOffers")
    attached_file_url: Optional[str] = Field(None, alias="attachedFileUrl")

    class Config:
        populate_by_name = True
