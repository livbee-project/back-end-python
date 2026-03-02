"""
Pydantic 스키마 모듈
도메인별 요청/응답 스키마 정의
"""
from app.schemas.campaigns import CampaignCreate, CampaignUpdate
from app.schemas.users import SignupRequest, LoginRequest, UserResponse
from app.schemas.portfolios import PortfolioCreate, PortfolioUpdate
from app.schemas.models import ModelCreate, ModelUpdate
from app.schemas.applications import ApplicationCreate, ApplicationStatusUpdate
from app.schemas.proposals import ProposalCreate
from app.schemas.news import NewsCreate, NewsUpdate
from app.schemas.studios import StudioCreate, StudioUpdate
from app.schemas.chat import (
    ChatRoomCreateRequest,
    ChatMessageCreateRequest,
    ChatReadRequest,
)
from app.schemas.common import PaginationMeta

__all__ = [
    "CampaignCreate",
    "CampaignUpdate",
    "SignupRequest",
    "LoginRequest",
    "UserResponse",
    "PortfolioCreate",
    "PortfolioUpdate",
    "ModelCreate",
    "ModelUpdate",
    "ApplicationCreate",
    "ApplicationStatusUpdate",
    "ProposalCreate",
    "NewsCreate",
    "NewsUpdate",
    "StudioCreate",
    "StudioUpdate",
    "ChatRoomCreateRequest",
    "ChatMessageCreateRequest",
    "ChatReadRequest",
    "PaginationMeta",
]
