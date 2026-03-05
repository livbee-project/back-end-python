"""
커뮤니티 도메인 비즈니스 로직 서비스
"""

from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from app.models.community import CommunityComment, CommunityPost, CommunityPostLike
from app.utils.db_helpers import get_or_404, require_ownership_or_admin
from app.utils.error_messages import get_error_message


def get_posts(
    db: Session,
    page: int,
    limit: int,
    sort: str = "recent",
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> Tuple[List[CommunityPost], int]:
    """
    커뮤니티 게시글 목록 조회
    """
    query = db.query(CommunityPost)

    if category:
        query = query.filter(CommunityPost.category == category)

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            or_(
                CommunityPost.title.ilike(like_pattern),
                CommunityPost.content.ilike(like_pattern),
            )
        )

    total_items = query.count()

    if sort == "popular":
        query = query.order_by(desc(CommunityPost.like_count), desc(CommunityPost.created_at))
    else:
        query = query.order_by(desc(CommunityPost.created_at))

    offset = (page - 1) * limit
    posts = query.offset(offset).limit(limit).all()

    return posts, total_items


def get_post_by_id(db: Session, post_id: str) -> CommunityPost:
    """
    커뮤니티 게시글 단건 조회 (없으면 404)
    """
    post = get_or_404(
        db,
        CommunityPost,
        lambda q: q.filter(CommunityPost.id == post_id),
        error_key="COMMUNITY_POST_NOT_FOUND",
    )

    # 조회수 증가
    post.view_count = (post.view_count or 0) + 1
    db.flush()

    return post


def create_post(
    db: Session,
    *,
    title: str,
    content: str,
    created_by: str,
    thumbnail_url: Optional[str] = None,
    category: Optional[str] = None,
) -> CommunityPost:
    """
    커뮤니티 게시글 생성
    """
    post = CommunityPost(
        title=title,
        content=content,
        created_by=created_by,
        thumbnail_url=thumbnail_url,
        category=category,
    )

    db.add(post)
    db.flush()
    db.refresh(post)

    return post


def update_post(
    db: Session,
    *,
    post_id: str,
    user_id: str,
    user_role: Optional[str],
    title: Optional[str] = None,
    content: Optional[str] = None,
    thumbnail_url: Optional[str] = None,
    category: Optional[str] = None,
) -> CommunityPost:
    """
    커뮤니티 게시글 수정 (소유자 또는 admin만)
    """
    post = get_or_404(
        db,
        CommunityPost,
        lambda q: q.filter(CommunityPost.id == post_id),
        error_key="COMMUNITY_POST_NOT_FOUND",
    )

    require_ownership_or_admin(
        post,
        user_id=user_id,
        user_role=user_role,
        owner_field="created_by",
        error_key="COMMUNITY_FORBIDDEN_EDIT",
    )

    if title is not None:
        post.title = title
    if content is not None:
        post.content = content
    if thumbnail_url is not None:
        post.thumbnail_url = thumbnail_url
    if category is not None:
        post.category = category

    db.flush()
    db.refresh(post)

    return post


def delete_post(
    db: Session,
    *,
    post_id: str,
    user_id: str,
    user_role: Optional[str],
) -> None:
    """
    커뮤니티 게시글 삭제 (소유자 또는 admin만)
    """
    post = get_or_404(
        db,
        CommunityPost,
        lambda q: q.filter(CommunityPost.id == post_id),
        error_key="COMMUNITY_POST_NOT_FOUND",
    )

    require_ownership_or_admin(
        post,
        user_id=user_id,
        user_role=user_role,
        owner_field="created_by",
        error_key="COMMUNITY_FORBIDDEN_EDIT",
    )

    db.delete(post)
    db.flush()


def get_comments_for_post(db: Session, post_id: str) -> List[CommunityComment]:
    """
    특정 게시글의 모든 댓글/대댓글 조회
    """
    # 게시글 존재 여부 확인
    get_or_404(
        db,
        CommunityPost,
        lambda q: q.filter(CommunityPost.id == post_id),
        error_key="COMMUNITY_POST_NOT_FOUND",
    )

    comments = (
        db.query(CommunityComment)
        .filter(CommunityComment.post_id == post_id)
        .order_by(CommunityComment.created_at.asc())
        .all()
    )

    return comments


def create_comment(
    db: Session,
    *,
    post_id: str,
    user_id: str,
    content: str,
    parent_id: Optional[str] = None,
) -> CommunityComment:
    """
    커뮤니티 댓글/대댓글 생성
    """
    # 게시글 존재 여부 확인
    get_or_404(
        db,
        CommunityPost,
        lambda q: q.filter(CommunityPost.id == post_id),
        error_key="COMMUNITY_POST_NOT_FOUND",
    )

    parent_comment: Optional[CommunityComment] = None
    if parent_id:
        parent_comment = get_or_404(
            db,
            CommunityComment,
            lambda q: q.filter(
                and_(
                    CommunityComment.id == parent_id,
                    CommunityComment.post_id == post_id,
                )
            ),
            error_key="COMMUNITY_COMMENT_NOT_FOUND",
        )
        # 1-depth 대댓글만 허용 (대댓글의 parent_id는 항상 최상위 댓글)
        if parent_comment.parent_id is not None:
            error = get_error_message("COMMUNITY_INVALID_COMMENT_DEPTH")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "COMMUNITY_INVALID_COMMENT_DEPTH",
                    "message": error["message"],
                    "userMessage": error["userMessage"],
                },
            )

    comment = CommunityComment(
        post_id=post_id,
        parent_id=parent_comment.id if parent_comment else None,
        content=content,
        created_by=user_id,
    )

    db.add(comment)

    # 게시글의 댓글 수 증가
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if post:
        post.comment_count = (post.comment_count or 0) + 1

    db.flush()
    db.refresh(comment)

    return comment


def update_comment(
    db: Session,
    *,
    comment_id: str,
    user_id: str,
    user_role: Optional[str],
    content: str,
) -> CommunityComment:
    """
    커뮤니티 댓글/대댓글 수정 (소유자 또는 admin만)
    """
    comment = get_or_404(
        db,
        CommunityComment,
        lambda q: q.filter(CommunityComment.id == comment_id),
        error_key="COMMUNITY_COMMENT_NOT_FOUND",
    )

    require_ownership_or_admin(
        comment,
        user_id=user_id,
        user_role=user_role,
        owner_field="created_by",
        error_key="COMMUNITY_FORBIDDEN_EDIT",
    )

    comment.content = content

    db.flush()
    db.refresh(comment)

    return comment


def delete_comment(
    db: Session,
    *,
    comment_id: str,
    user_id: str,
    user_role: Optional[str],
) -> None:
    """
    커뮤니티 댓글/대댓글 삭제 (소유자 또는 admin만)
    """
    comment = get_or_404(
        db,
        CommunityComment,
        lambda q: q.filter(CommunityComment.id == comment_id),
        error_key="COMMUNITY_COMMENT_NOT_FOUND",
    )

    require_ownership_or_admin(
        comment,
        user_id=user_id,
        user_role=user_role,
        owner_field="created_by",
        error_key="COMMUNITY_FORBIDDEN_EDIT",
    )

    post_id = comment.post_id

    db.delete(comment)

    # 게시글의 댓글 수 감소 (0 미만으로 내려가지 않도록 보호)
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if post:
        post.comment_count = max((post.comment_count or 0) - 1, 0)

    db.flush()


def add_like(
    db: Session,
    *,
    post_id: str,
    user_id: str,
) -> CommunityPost:
    """
    게시글 좋아요 추가
    """
    post = get_or_404(
        db,
        CommunityPost,
        lambda q: q.filter(CommunityPost.id == post_id),
        error_key="COMMUNITY_POST_NOT_FOUND",
    )

    existing = (
        db.query(CommunityPostLike)
        .filter(
            CommunityPostLike.post_id == post_id,
            CommunityPostLike.user_id == user_id,
        )
        .first()
    )
    if existing:
        error = get_error_message("COMMUNITY_ALREADY_LIKED")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "COMMUNITY_ALREADY_LIKED",
                "message": error["message"],
                "userMessage": error["userMessage"],
            },
        )

    like = CommunityPostLike(post_id=post_id, user_id=user_id)
    db.add(like)

    post.like_count = (post.like_count or 0) + 1

    db.flush()
    db.refresh(post)

    return post


def remove_like(
    db: Session,
    *,
    post_id: str,
    user_id: str,
) -> CommunityPost:
    """
    게시글 좋아요 취소
    """
    post = get_or_404(
        db,
        CommunityPost,
        lambda q: q.filter(CommunityPost.id == post_id),
        error_key="COMMUNITY_POST_NOT_FOUND",
    )

    like = (
        db.query(CommunityPostLike)
        .filter(
            CommunityPostLike.post_id == post_id,
            CommunityPostLike.user_id == user_id,
        )
        .first()
    )
    if not like:
        error = get_error_message("COMMUNITY_NOT_LIKED")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "COMMUNITY_NOT_LIKED",
                "message": error["message"],
                "userMessage": error["userMessage"],
            },
        )

    db.delete(like)
    post.like_count = max((post.like_count or 0) - 1, 0)

    db.flush()
    db.refresh(post)

    return post
