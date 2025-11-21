"""
Studio 모델
스튜디오 정보
"""
from sqlalchemy import Column, String, Boolean, ARRAY, JSON, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Studio(Base):
    """스튜디오 모델"""
    __tablename__ = "studios"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # 기본 정보
    brand_name = Column(String, nullable=True)
    one_line_intro = Column(String, nullable=True)
    detailed_intro = Column(String, nullable=True)
    usage_info = Column(String, nullable=True)
    price_info = Column(String, nullable=True)

    # 이미지 URL
    main_thumbnail_url = Column(String, nullable=True)
    background_image_url = Column(String, nullable=True)
    sub_thumbnail_urls = Column(ARRAY(String), nullable=True)  # 최대 5개
    gallery_urls = Column(ARRAY(String), nullable=True)  # 최대 9개

    # 연락처 및 위치
    contact = Column(JSON, nullable=True)  # {phone, email, kakao}
    location = Column(JSON, nullable=True)  # {address, mapUrl}

    # 주간 영업시간
    weekly_schedule = Column(JSON, nullable=True)  # {월: {isOpen, startTime, endTime, excludedTimes}, ...}

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

