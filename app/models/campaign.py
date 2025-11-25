"""
Campaign 모델
캠페인/공고 정보
"""
from sqlalchemy import Column, String, Integer, Boolean, Date, ForeignKey, ARRAY, JSON, Numeric, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class ProductItem(Base):
    """상품 아이템 모델 (임베디드)"""
    __tablename__ = "product_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)

    url = Column(String, nullable=False)
    marketplace = Column(String, default="smartstore")  # enum: ["smartstore", "coupang", "gmarket", "etc"]
    title = Column(String, nullable=True)
    price = Column(Numeric, nullable=True)
    sale_price = Column(Numeric, nullable=True)
    sale_duration_sec = Column(Integer, nullable=True)
    sale_until = Column(Date, nullable=True)
    image_url = Column(String, nullable=True)
    deep_link = Column(String, nullable=True)
    utm = Column(JSON, nullable=True)  # {source, medium, campaign}
    detail_html = Column(String, nullable=True)

    # 관계
    campaign = relationship("Campaign", back_populates="products")


class Question(Base):
    """질문 항목 모델 (임베디드)"""
    __tablename__ = "questions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)

    label = Column(String, nullable=False)
    type = Column(String, default="short")  # enum: ["short", "long", "select", "file", "url", "number"]
    required = Column(Boolean, default=False)
    options = Column(ARRAY(String), nullable=True)

    # 관계
    campaign = relationship("Campaign", back_populates="questions")


class Campaign(Base):
    """캠페인 모델"""
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # 기본 정보
    is_public = Column(Boolean, default=True, index=True)
    brand_name = Column(String, nullable=False)
    brand_introduction = Column(String, nullable=True)
    prefix = Column(String, nullable=True)  # enum: ["쇼호스트모집", "촬영스태프", "모델모집", "기타모집"]
    title = Column(String, nullable=False)
    content = Column(String, nullable=True)
    category = Column(String, nullable=True)  # enum: ["뷰티", "패션", "식품", "가전", "생활/리빙"]

    # 일정 및 장소
    location = Column(String, nullable=True)
    shoot_date = Column(Date, nullable=False)
    close_at = Column(Date, nullable=False)
    duration_hours = Column(Integer, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)

    # 출연료 정보
    fee = Column(Numeric, nullable=True)
    fee_negotiable = Column(Boolean, default=False)

    # 이미지 및 외부 링크
    cover_image_url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    live_vertical_cover_url = Column(String, nullable=True)
    live_stream_url = Column(String, nullable=True)

    # 상품 정보
    product_thumbnail_url = Column(String, nullable=True)
    product_name = Column(String, nullable=True)
    product_url = Column(String, nullable=True)

    # 통계
    metrics = Column(JSON, default={"views": 0, "clicks": 0, "applications": 0})

    # 소유자 정보
    created_by = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계
    created_by_user = relationship("User", back_populates="campaigns", foreign_keys=[created_by])
    applications = relationship("Application", back_populates="campaign", cascade="all, delete-orphan")
    chat_rooms = relationship("ChatRoom", back_populates="campaign", cascade="all, delete-orphan")
    products = relationship("ProductItem", back_populates="campaign", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="campaign", cascade="all, delete-orphan")

