"""
User 모델
사용자 정보 관리
"""

import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class UserRole(str, enum.Enum):
    """사용자 역할"""

    BRAND = "brand"
    SHOWHOST = "showhost"


class User(Base):
    """사용자 모델"""

    __tablename__ = "users"

    # 기본 필수 정보
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)  # 해시된 비밀번호
    role = Column(SQLEnum(UserRole), nullable=False)

    # 공통 선택 정보
    phone = Column(String, nullable=True)
    kakao_id = Column(String, nullable=True, index=True)

    # 역할 플래그 (다중 역할 지원용)
    # - is_brand: 브랜드 기능 사용 가능 여부
    # - is_showhost: 쇼호스트 기능 사용 가능 여부
    # 기존 데이터 호환을 위해 기본값 False, 서버 기본값도 false로 설정
    is_brand = Column(Boolean, nullable=False, server_default="false")
    is_showhost = Column(Boolean, nullable=False, server_default="false")

    # 'brand' 역할 전용 정보
    brand_name = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    business_number = Column(String, nullable=True)

    # 'showhost' 역할 전용 정보
    nickname = Column(String, nullable=True)
    sns_link = Column(String, nullable=True)
    introduction = Column(String, nullable=True)

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # 관계
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    models = relationship("Model", back_populates="user", cascade="all, delete-orphan")
    campaigns = relationship(
        "Campaign", back_populates="created_by_user", foreign_keys="Campaign.created_by"
    )
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    proposals_sent = relationship(
        "Proposal", back_populates="proposer", foreign_keys="Proposal.proposer_id"
    )
    proposals_received = relationship(
        "Proposal", back_populates="target_showhost", foreign_keys="Proposal.target_showhost_id"
    )
    news = relationship("News", back_populates="created_by_user", cascade="all, delete-orphan")
    brand_chat_rooms = relationship(
        "ChatRoom", back_populates="brand_user", foreign_keys="ChatRoom.brand_user_id"
    )
    showhost_chat_rooms = relationship(
        "ChatRoom", back_populates="showhost_user", foreign_keys="ChatRoom.showhost_user_id"
    )
    chat_participations = relationship(
        "ChatParticipant", back_populates="user", cascade="all, delete-orphan"
    )
