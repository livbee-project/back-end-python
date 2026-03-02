"""
Proposal 모델
쇼호스트 제안 정보
"""

import enum
import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ProposalStatus(str, enum.Enum):
    """제안 상태"""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELED = "canceled"
    WITHDRAWN = "withdrawn"
    HOLD = "hold"


class Proposal(Base):
    """제안 모델"""

    __tablename__ = "proposals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # 제안의 주체 및 대상
    target_portfolio_id = Column(
        String, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=True, index=True
    )
    target_model_id = Column(
        String, ForeignKey("models.id", ondelete="CASCADE"), nullable=True, index=True
    )
    proposer_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_showhost_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # 제안 내용
    brand_name = Column(String, nullable=False)
    fee = Column(Integer, nullable=True)
    is_fee_negotiable = Column(Boolean, default=False)
    shooting_date = Column(Date, nullable=False)
    shooting_time = Column(String, nullable=True)
    location = Column(String, nullable=True)
    reply_deadline = Column(Date, nullable=False)
    content = Column(String, nullable=True)  # maxlength: 800

    # 제안 상태
    status = Column(SQLEnum(ProposalStatus), default=ProposalStatus.PENDING, index=True)

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # 관계
    target_portfolio = relationship("Portfolio", back_populates="proposals")
    target_model = relationship("Model", back_populates="proposals")
    proposer = relationship("User", back_populates="proposals_sent", foreign_keys=[proposer_id])
    target_showhost = relationship(
        "User", back_populates="proposals_received", foreign_keys=[target_showhost_id]
    )
