"""
Application 도메인 스키마
지원서 관련 요청/응답
"""
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.models.application import ApplicationStatus


class ApplicationCreate(BaseModel):
    campaign_id: str = Field(..., alias="campaignId")
    profile_ref: Optional[str] = Field(None, alias="portfolioId")  # 하위 호환성 유지
    portfolio_id: Optional[str] = Field(None, alias="portfolioId")
    model_id: Optional[str] = Field(None, alias="modelId")
    message: Optional[str] = None
    available_date: Optional[date] = Field(None, alias="availableDate")
    available_time: Optional[str] = Field(None, alias="availableTime")

    class Config:
        populate_by_name = True


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
