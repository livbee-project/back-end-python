"""
Studio 라우트
스튜디오 관리
"""
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.studio import Studio
from app.utils.response import success_response, fail_response
from app.utils.common import model_to_dict
from app.services.studio_service import (
    get_studio_by_id,
    create_studio,
    update_studio
)
import uuid

router = APIRouter(prefix="/studios", tags=["studios"])


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


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_studio(
    request: StudioCreate,
    db: Session = Depends(get_db)
):
    """
    새로운 스튜디오 정보 생성
    """
    studio_data = request.model_dump(exclude_unset=True, by_alias=False)

    # 서비스를 통한 스튜디오 생성
    studio = create_studio(db, **studio_data)

    data = model_to_dict(studio)
    return success_response({"data": data}, status_code=status.HTTP_201_CREATED)


@router.put("/{studio_id}")
async def update_studio(
    studio_id: str,
    request: StudioUpdate,
    db: Session = Depends(get_db)
):
    """
    특정 ID를 가진 스튜디오 정보 수정
    """
    update_data = request.model_dump(exclude_unset=True, by_alias=False)

    # 서비스를 통한 스튜디오 수정
    studio = update_studio(db, studio_id, **update_data)

    data = model_to_dict(studio)
    return success_response({"data": data})


@router.get("/{studio_id}")
async def get_studio(
    studio_id: str,
    db: Session = Depends(get_db)
):
    """
    특정 ID를 가진 스튜디오 정보 조회
    """
    studio = get_studio_by_id(db, studio_id)

    data = model_to_dict(studio)
    return success_response({"data": data})

