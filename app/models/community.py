"""
Community 모델
커뮤니티 게시글 / 댓글 / 좋아요
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CommunityPost(Base):
    """커뮤니티 게시글 모델"""

    __tablename__ = "community_posts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)

    # 메타 정보
    thumbnail_url = Column(String, nullable=True)
    category = Column(String, nullable=True)

    # 통계
    like_count = Column(Integer, nullable=False, default=0)
    comment_count = Column(Integer, nullable=False, default=0)
    view_count = Column(Integer, nullable=False, default=0)

    # 작성자
    created_by = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # 관계
    created_by_user = relationship(
        "User",
        back_populates="community_posts",
        foreign_keys=[created_by],
    )
    comments = relationship(
        "CommunityComment",
        back_populates="post",
        cascade="all, delete-orphan",
    )
    likes = relationship(
        "CommunityPostLike",
        back_populates="post",
        cascade="all, delete-orphan",
    )


class CommunityComment(Base):
    """커뮤니티 댓글/대댓글 모델 (1-depth 대댓글까지 지원)"""

    __tablename__ = "community_comments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    post_id = Column(
        String,
        ForeignKey("community_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id = Column(
        String,
        ForeignKey("community_comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    content = Column(String, nullable=False)

    # 작성자
    created_by = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # 관계
    post = relationship("CommunityPost", back_populates="comments")
    created_by_user = relationship("User", back_populates="community_comments")
    parent = relationship(
        "CommunityComment",
        remote_side=[id],
        back_populates="replies",
    )
    replies = relationship(
        "CommunityComment",
        back_populates="parent",
        cascade="all, delete-orphan",
    )


class CommunityPostLike(Base):
    """커뮤니티 게시글 좋아요 모델"""

    __tablename__ = "community_post_likes"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_community_post_like_post_user"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    post_id = Column(
        String,
        ForeignKey("community_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 관계
    post = relationship("CommunityPost", back_populates="likes")
    user = relationship("User", back_populates="community_post_likes")
