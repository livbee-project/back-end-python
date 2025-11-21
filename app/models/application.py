"""
Application 모델
지원서 정보
"""
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
import uuid


class ApplicationStatus(str, enum.Enum):
    """지원서 상태"""
    SUBMITTED = "submitted"
    REVIEWING = "reviewing"
    SHORTLISTED = "shortlisted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Application(Base):
    """지원서 모델"""
    __tablename__ = "applications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    profile_ref = Column(String, nullable=True)  # 포트폴리오 링크 or id
    message = Column(String, nullable=True)
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.SUBMITTED, index=True)

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계
    campaign = relationship("Campaign", back_populates="applications")
    user = relationship("User", back_populates="applications")

    # 제약 조건: 중복 지원 방지
    __table_args__ = (
        UniqueConstraint('campaign_id', 'user_id', name='uq_campaign_user'),
    )

