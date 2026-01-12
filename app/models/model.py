"""
Model 모델
모델 정보
"""
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, ARRAY, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Model(Base):
    """모델 모델"""
    __tablename__ = "models"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 기본 정보
    nickname = Column(String, nullable=True)
    one_line_intro = Column(String, nullable=True)
    detailed_intro = Column(String, nullable=True)
    experience_years = Column(Integer, nullable=True)
    age = Column(Integer, nullable=True)

    # 이미지 URL
    main_thumbnail_url = Column(String, nullable=True)
    background_image_url = Column(String, nullable=True)
    sub_thumbnail_urls = Column(ARRAY(String), nullable=True)  # 최대 5개 (모델)

    # 상태 및 공개 설정
    status = Column(String, default="published")  # enum: ["published"]
    is_age_public = Column(Boolean, default=True)
    is_sizing_public = Column(Boolean, default=True)

    # 지역 및 신체 정보
    detailed_region = Column(String, nullable=True)
    gender = Column(String, nullable=True)  # enum: ["male", "female"]
    height = Column(Integer, nullable=True)  # cm
    weight = Column(Integer, nullable=True)  # kg
    top_size = Column(String, nullable=True)
    bottom_size = Column(String, nullable=True)
    shoe_size = Column(Integer, nullable=True)

    # SNS 및 연락처
    website_url = Column(String, nullable=True)
    instagram_url = Column(String, nullable=True)
    youtube_url = Column(String, nullable=True)
    tiktok_url = Column(String, nullable=True)
    contact = Column(String, nullable=True)
    open_chat = Column(String, nullable=True)

    # 기타
    registration_type = Column(String, nullable=True)
    public_scope = Column(String, default="전체공개")
    is_receiving_offers = Column(Boolean, default=True)
    # recent_lives 필드 제외 (모델은 라이브 방송 없음)
    attached_file_url = Column(String, nullable=True)

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계
    user = relationship("User", back_populates="models")
    proposals = relationship("Proposal", back_populates="target_model")
