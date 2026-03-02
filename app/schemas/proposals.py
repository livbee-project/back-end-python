"""
Proposal 도메인 스키마
제안 관련 요청/응답
"""
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class ProposalCreate(BaseModel):
    target_portfolio_id: Optional[str] = Field(None, alias="targetPortfolioId")
    target_model_id: Optional[str] = Field(None, alias="targetModelId")
    brand_name: str = Field(..., alias="brandName")
    fee: Optional[int] = None
    is_fee_negotiable: bool = Field(False, alias="isFeeNegotiable")
    shooting_date: date = Field(..., alias="shootingDate")
    shooting_time: Optional[str] = Field(None, alias="shootingTime")
    location: Optional[str] = None
    reply_deadline: date = Field(..., alias="replyDeadline")
    content: Optional[str] = Field(None, max_length=800)

    class Config:
        populate_by_name = True
