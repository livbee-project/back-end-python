"""
News 모델
뉴스/공지사항 정보
"""
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class News(Base):
    """뉴스 모델"""
    __tablename__ = "news"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    created_by = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계
    created_by_user = relationship("User", back_populates="news")

