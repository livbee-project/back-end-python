"""
Community 라우트
커뮤니티 게시글 / 댓글 / 좋아요
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user, get_optional_user
from app.schemas.community import (
    CommunityCommentCreate,
    CommunityCommentUpdate,
    CommunityPostCreate,
    CommunityPostUpdate,
)
from app.services.community_service import (
    add_like,
    create_comment,
    create_post,
    delete_comment,
    delete_post,
    get_comments_for_post,
    get_post_by_id,
    get_posts,
    remove_like,
    update_comment,
    update_post,
)
from app.utils.common import model_to_dict, strip_tags, truncate_text
from app.utils.pagination import build_paginated_payload, normalize_pagination
from app.utils.response import success_response

# prefix="/community/posts": REST 리소스가 "게시글(posts)"이고, 상위 네임스페이스 "community"로 구분. (다른 라우터는 단일 경로 ex. /users, /news)
router = APIRouter(prefix="/community/posts", tags=["community"])


@router.get("")
async def get_community_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    sort: str = Query("recent", pattern="^(recent|popular)$"),
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: Optional[dict] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    커뮤니티 게시글 목록 조회 (페이지네이션/정렬/필터)
    """
    page, limit = normalize_pagination(page, limit, max_limit=50)

    posts, total_items = get_posts(
        db,
        page=page,
        limit=limit,
        sort=sort,
        category=category,
        search=search,
    )

    current_user_id = current_user.get("sub") if current_user else None

    items = []
    if posts:
        liked_post_ids = set()
        if current_user_id:
            from app.models.community import CommunityPostLike  # local import to avoid cycle

            post_ids = [post.id for post in posts]
            liked_rows = (
                db.query(CommunityPostLike.post_id)
                .filter(
                    CommunityPostLike.post_id.in_(post_ids),
                    CommunityPostLike.user_id == current_user_id,
                )
                .all()
            )
            liked_post_ids = {row[0] for row in liked_rows}

        for post in posts:
            payload = model_to_dict(
                post,
                exclude=["created_by_user", "comments", "likes"],
                to_camel_case=True,
            )
            # 요약 본문
            content_for_summary = post.content if isinstance(post.content, str) else ""
            payload["summary"] = (
                truncate_text(strip_tags(content_for_summary), limit=220)
                if content_for_summary
                else ""
            )
            # 작성자 및 상태
            payload["authorId"] = post.created_by
            if post.created_by_user:
                payload["authorName"] = post.created_by_user.name
                payload["authorRole"] = post.created_by_user.role
            else:
                payload["authorName"] = None
                payload["authorRole"] = None
            payload["isLiked"] = post.id in liked_post_ids if current_user_id else False
            payload["isOwner"] = current_user_id == post.created_by if current_user_id else False
            items.append(payload)

    return success_response(build_paginated_payload(items, total_items, page, limit))


@router.get("/{post_id}")
async def get_community_post(
    post_id: str,
    current_user: Optional[dict] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    커뮤니티 게시글 상세 조회
    """
    post = get_post_by_id(db, post_id)

    current_user_id = current_user.get("sub") if current_user else None

    data = model_to_dict(
        post,
        exclude=["created_by_user", "comments", "likes"],
        to_camel_case=True,
    )
    data["authorId"] = post.created_by
    if post.created_by_user:
        data["authorName"] = post.created_by_user.name
        data["authorRole"] = post.created_by_user.role
    else:
        data["authorName"] = None
        data["authorRole"] = None
    data["isOwner"] = current_user_id == post.created_by if current_user_id else False

    if current_user_id:
        from app.models.community import CommunityPostLike  # local import to avoid cycle

        liked = (
            db.query(CommunityPostLike)
            .filter(
                CommunityPostLike.post_id == post_id,
                CommunityPostLike.user_id == current_user_id,
            )
            .first()
        )
        data["isLiked"] = liked is not None
    else:
        data["isLiked"] = False

    return success_response({"data": data})


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_community_post(
    request: CommunityPostCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    커뮤니티 게시글 생성 (로그인 필요)
    """
    user_id = current_user.get("sub")

    post = create_post(
        db,
        title=request.title,
        content=request.content,
        created_by=user_id,
        thumbnail_url=str(request.thumbnail_url) if request.thumbnail_url else None,
        category=request.category,
    )

    data = model_to_dict(
        post,
        exclude=["created_by_user", "comments", "likes"],
        to_camel_case=True,
    )
    data["authorId"] = post.created_by
    if post.created_by_user:
        data["authorName"] = post.created_by_user.name
        data["authorRole"] = post.created_by_user.role
    else:
        data["authorName"] = None
        data["authorRole"] = None
    data["isOwner"] = True
    data["isLiked"] = False

    return success_response({"data": data}, status_code=status.HTTP_201_CREATED)


@router.put("/{post_id}")
async def update_community_post(
    post_id: str,
    request: CommunityPostUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    커뮤니티 게시글 수정 (작성자/관리자만)
    """
    user_id = current_user.get("sub")
    user_role = current_user.get("role")

    update_data = request.model_dump(exclude_unset=True, by_alias=False)
    thumbnail_url = str(update_data["thumbnail_url"]) if update_data.get("thumbnail_url") else None

    post = update_post(
        db,
        post_id=post_id,
        user_id=user_id,
        user_role=user_role,
        title=update_data.get("title"),
        content=update_data.get("content"),
        thumbnail_url=thumbnail_url,
        category=update_data.get("category"),
    )

    data = model_to_dict(
        post,
        exclude=["created_by_user", "comments", "likes"],
        to_camel_case=True,
    )
    data["authorId"] = post.created_by
    if post.created_by_user:
        data["authorName"] = post.created_by_user.name
        data["authorRole"] = post.created_by_user.role
    else:
        data["authorName"] = None
        data["authorRole"] = None
    data["isOwner"] = True

    return success_response({"data": data})


@router.delete("/{post_id}")
async def delete_community_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    커뮤니티 게시글 삭제 (작성자/관리자만)
    """
    user_id = current_user.get("sub")
    user_role = current_user.get("role")

    delete_post(
        db,
        post_id=post_id,
        user_id=user_id,
        user_role=user_role,
    )

    return success_response({"message": "게시글이 성공적으로 삭제되었습니다."})


@router.get("/{post_id}/comments")
async def get_community_comments(
    post_id: str,
    db: Session = Depends(get_db),
):
    """
    커뮤니티 댓글/대댓글 목록 조회
    (1-depth 대댓글 구조)
    """
    comments = get_comments_for_post(db, post_id)

    # 1-depth 대댓글 구조는 유지하되, 1차 스펙에서는 parentId와 상관없이 평면 리스트로 제공
    items = []
    for comment in comments:
        payload = model_to_dict(
            comment,
            exclude=["post", "created_by_user", "parent", "replies"],
            to_camel_case=True,
        )
        payload["parentId"] = comment.parent_id
        payload["postId"] = comment.post_id
        payload["authorId"] = comment.created_by
        if comment.created_by_user:
            payload["authorName"] = comment.created_by_user.name
            payload["authorRole"] = comment.created_by_user.role
        else:
            payload["authorName"] = None
            payload["authorRole"] = None
        items.append(payload)

    return success_response({"items": items})


@router.post("/{post_id}/comments", status_code=status.HTTP_201_CREATED)
async def create_community_comment(
    post_id: str,
    request: CommunityCommentCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    커뮤니티 댓글/대댓글 생성 (로그인 필요)
    """
    user_id = current_user.get("sub")

    comment = create_comment(
        db,
        post_id=post_id,
        user_id=user_id,
        content=request.content,
        parent_id=request.parent_id,
    )

    data = model_to_dict(
        comment,
        exclude=["post", "created_by_user", "parent", "replies"],
        to_camel_case=True,
    )
    data["parentId"] = comment.parent_id
    data["postId"] = comment.post_id
    data["authorId"] = comment.created_by
    if comment.created_by_user:
        data["authorName"] = comment.created_by_user.name
        data["authorRole"] = comment.created_by_user.role
    else:
        data["authorName"] = None
        data["authorRole"] = None

    return success_response({"data": data}, status_code=status.HTTP_201_CREATED)


@router.put("/comments/{comment_id}")
async def update_community_comment(
    comment_id: str,
    request: CommunityCommentUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    커뮤니티 댓글/대댓글 수정 (작성자/관리자만)
    """
    user_id = current_user.get("sub")
    user_role = current_user.get("role")

    comment = update_comment(
        db,
        comment_id=comment_id,
        user_id=user_id,
        user_role=user_role,
        content=request.content,
    )

    data = model_to_dict(
        comment,
        exclude=["post", "created_by_user", "parent", "replies"],
        to_camel_case=True,
    )
    data["parentId"] = comment.parent_id
    data["postId"] = comment.post_id
    data["authorId"] = comment.created_by
    if comment.created_by_user:
        data["authorName"] = comment.created_by_user.name
        data["authorRole"] = comment.created_by_user.role
    else:
        data["authorName"] = None
        data["authorRole"] = None

    return success_response({"data": data})


@router.delete("/comments/{comment_id}")
async def delete_community_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    커뮤니티 댓글/대댓글 삭제 (작성자/관리자만)
    """
    user_id = current_user.get("sub")
    user_role = current_user.get("role")

    delete_comment(
        db,
        comment_id=comment_id,
        user_id=user_id,
        user_role=user_role,
    )

    return success_response({"message": "댓글이 성공적으로 삭제되었습니다."})


@router.post("/{post_id}/like", status_code=status.HTTP_200_OK)
async def like_community_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    커뮤니티 게시글 좋아요
    """
    user_id = current_user.get("sub")

    post = add_like(
        db,
        post_id=post_id,
        user_id=user_id,
    )

    return success_response(
        {
            "likeCount": post.like_count or 0,
            "isLiked": True,
        }
    )


@router.delete("/{post_id}/like")
async def unlike_community_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    커뮤니티 게시글 좋아요 취소
    """
    user_id = current_user.get("sub")

    post = remove_like(
        db,
        post_id=post_id,
        user_id=user_id,
    )

    return success_response(
        {
            "likeCount": post.like_count or 0,
            "isLiked": False,
        }
    )
