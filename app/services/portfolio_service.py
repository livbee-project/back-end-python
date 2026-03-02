"""
포트폴리오 관련 비즈니스 로직 서비스
"""

import uuid
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.models.portfolio import Portfolio
from app.utils.db_helpers import get_or_404, require_ownership_or_admin
from app.utils.error_messages import get_error_message
from app.utils.validators import validate_portfolio_contact, validate_portfolio_urls


def validate_and_prepare_portfolio_create_data(request: Any) -> Dict[str, Any]:
    """
    포트폴리오 생성용 요청 데이터 검증 및 변환
    - 필수 필드(nickname, registration_type) 검증
    - 갤러리 이미지 개수(최대 9개) 검증
    - URL·전화번호 형식 검증
    - website_url → youtube_url 매핑

    Returns:
        DB 저장용 portfolio_data 딕셔너리

    Raises:
        HTTPException: 검증 실패 시
    """
    # 필수 필드 검증
    if not request.nickname:
        error = get_error_message("PORTFOLIO_MISSING_REQUIRED_FIELD")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PORTFOLIO_MISSING_REQUIRED_FIELD",
                "message": error["message"],
                "userMessage": "닉네임은 필수 입력값입니다.",
            },
        )
    if not request.registration_type:
        error = get_error_message("PORTFOLIO_MISSING_REQUIRED_FIELD")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PORTFOLIO_MISSING_REQUIRED_FIELD",
                "message": error["message"],
                "userMessage": "등록 유형은 필수 입력값입니다.",
            },
        )

    # 갤러리 이미지 개수 검증
    if request.sub_thumbnail_urls and len(request.sub_thumbnail_urls) > 9:
        error = get_error_message("PORTFOLIO_TOO_MANY_IMAGES")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PORTFOLIO_TOO_MANY_IMAGES",
                "message": error["message"],
                "userMessage": "갤러리 이미지는 최대 9개까지 등록할 수 있습니다.",
            },
        )

    # URL 검증
    url_error = validate_portfolio_urls(
        website_url=request.website_url,
        youtube_url=request.youtube_url,
        instagram_url=request.instagram_url,
        tiktok_url=request.tiktok_url,
        open_chat=request.open_chat,
        recent_lives=request.recent_lives,
    )
    if url_error:
        error = get_error_message("PORTFOLIO_INVALID_URL")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PORTFOLIO_INVALID_URL",
                "message": error["message"],
                "userMessage": url_error,
            },
        )

    # 전화번호 검증
    contact_error = validate_portfolio_contact(request.contact)
    if contact_error:
        error = get_error_message("PORTFOLIO_INVALID_PHONE")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PORTFOLIO_INVALID_PHONE",
                "message": error["message"],
                "userMessage": contact_error,
            },
        )

    portfolio_data = request.model_dump(exclude_unset=True, by_alias=False)
    if (
        "website_url" in portfolio_data
        and portfolio_data["website_url"]
        and not portfolio_data.get("youtube_url")
    ):
        portfolio_data["youtube_url"] = portfolio_data["website_url"]
        portfolio_data["website_url"] = None

    portfolio_fields = {col.name for col in Portfolio.__table__.columns}
    return {k: v for k, v in portfolio_data.items() if k in portfolio_fields}


def validate_and_prepare_portfolio_update_data(
    update_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    포트폴리오 업데이트용 데이터 검증 및 변환
    - 갤러리 이미지 개수(최대 9개) 검증
    - URL·전화번호 형식 검증
    - website_url → youtube_url 매핑

    Returns:
        setattr 적용용 update_data 딕셔너리

    Raises:
        HTTPException: 검증 실패 시
    """
    if "sub_thumbnail_urls" in update_data and update_data["sub_thumbnail_urls"] is not None:
        if len(update_data["sub_thumbnail_urls"]) > 9:
            error = get_error_message("PORTFOLIO_TOO_MANY_IMAGES")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "PORTFOLIO_TOO_MANY_IMAGES",
                    "message": error["message"],
                    "userMessage": "갤러리 이미지는 최대 9개까지 등록할 수 있습니다.",
                },
            )

    url_error = validate_portfolio_urls(
        website_url=update_data.get("website_url"),
        youtube_url=update_data.get("youtube_url"),
        instagram_url=update_data.get("instagram_url"),
        tiktok_url=update_data.get("tiktok_url"),
        open_chat=update_data.get("open_chat"),
        recent_lives=update_data.get("recent_lives"),
    )
    if url_error:
        error = get_error_message("PORTFOLIO_INVALID_URL")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PORTFOLIO_INVALID_URL",
                "message": error["message"],
                "userMessage": url_error,
            },
        )

    if "contact" in update_data and update_data["contact"]:
        contact_error = validate_portfolio_contact(update_data["contact"])
        if contact_error:
            error = get_error_message("PORTFOLIO_INVALID_PHONE")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "PORTFOLIO_INVALID_PHONE",
                    "message": error["message"],
                    "userMessage": contact_error,
                },
            )

    # website_url → youtube_url 매핑
    if (
        "website_url" in update_data
        and update_data["website_url"]
        and not update_data.get("youtube_url")
    ):
        update_data["youtube_url"] = update_data["website_url"]
        update_data["website_url"] = None

    return update_data


def get_portfolio_by_id(
    db: Session, portfolio_id: str, user_id: Optional[str] = None, user_role: Optional[str] = None
) -> Portfolio:
    """
    포트폴리오 ID로 조회 (user 관계 eager load로 N+1 방지)

    Args:
        db: 데이터베이스 세션
        portfolio_id: 포트폴리오 ID
        user_id: 사용자 ID (소유권 확인용, 선택적)
        user_role: 사용자 역할 (소유권 확인용, 선택적)

    Returns:
        포트폴리오 인스턴스

    Raises:
        HTTPException: 포트폴리오를 찾을 수 없거나 권한이 없는 경우
    """
    portfolio = get_or_404(
        db,
        Portfolio,
        lambda q: q.options(joinedload(Portfolio.user)).filter(Portfolio.id == portfolio_id),
        error_key="NOT_FOUND",
    )

    # 소유권 확인이 필요한 경우
    if user_id:
        require_ownership_or_admin(
            portfolio,
            user_id,
            user_role,
            owner_field="user_id",
            error_key="PORTFOLIO_FORBIDDEN_EDIT",
        )

    return portfolio


def get_user_portfolios(db: Session, user_id: str) -> list[Portfolio]:
    """
    사용자의 포트폴리오 목록 조회

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID

    Returns:
        포트폴리오 리스트
    """
    return (
        db.query(Portfolio)
        .filter(Portfolio.user_id == user_id)
        .order_by(desc(Portfolio.created_at))
        .all()
    )


def get_public_portfolios(
    db: Session, page: int = 1, limit: int = 20
) -> tuple[list[Portfolio], int]:
    """
    공개된 포트폴리오 목록 조회

    Args:
        db: 데이터베이스 세션
        page: 페이지 번호
        limit: 페이지당 항목 수

    Returns:
        (포트폴리오 리스트, 전체 개수) 튜플
    """
    skip = (page - 1) * limit

    query = db.query(Portfolio).filter(
        Portfolio.public_scope == "전체공개", Portfolio.status == "published"
    )

    total_items = query.count()
    portfolios = query.order_by(desc(Portfolio.created_at)).offset(skip).limit(limit).all()

    return portfolios, total_items


def get_published_portfolios(
    db: Session, page: int = 1, limit: int = 10
) -> tuple[list[Portfolio], int]:
    """
    published 상태의 포트폴리오 목록 조회

    Args:
        db: 데이터베이스 세션
        page: 페이지 번호
        limit: 페이지당 항목 수

    Returns:
        (포트폴리오 리스트, 전체 개수) 튜플
    """
    skip = (page - 1) * limit

    query = db.query(Portfolio).filter(Portfolio.status == "published")

    total_items = query.count()
    portfolios = query.order_by(desc(Portfolio.created_at)).offset(skip).limit(limit).all()

    return portfolios, total_items


def check_user_has_portfolio(db: Session, user_id: str) -> bool:
    """
    사용자가 포트폴리오를 가지고 있는지 확인

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID

    Returns:
        포트폴리오 존재 여부
    """
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
    return portfolio is not None


def create_portfolio(db: Session, user_id: str, portfolio_data: Dict[str, Any]) -> Portfolio:
    """
    포트폴리오 생성

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        portfolio_data: 포트폴리오 데이터

    Returns:
        생성된 포트폴리오 인스턴스

    Raises:
        HTTPException: 이미 포트폴리오가 있는 경우
    """
    # 중복 체크
    if check_user_has_portfolio(db, user_id):
        from fastapi import HTTPException, status

        from app.utils.error_messages import get_error_message

        error = get_error_message("PORTFOLIO_DUP")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "PORTFOLIO_DUP",
                "message": error["message"],
                "userMessage": error["userMessage"],
            },
        )

    portfolio_data["id"] = str(uuid.uuid4())
    portfolio_data["user_id"] = user_id

    portfolio = Portfolio(**portfolio_data)
    db.add(portfolio)
    db.flush()  # 세션 변경사항을 DB에 반영 (커밋은 아님)
    db.refresh(portfolio)

    return portfolio


def update_portfolio(
    db: Session,
    portfolio_id: str,
    user_id: str,
    user_role: Optional[str] = None,
    update_data: Optional[Dict[str, Any]] = None,
) -> Portfolio:
    """
    포트폴리오 수정 (검증·변환 후 적용)

    Args:
        db: 데이터베이스 세션
        portfolio_id: 포트폴리오 ID
        user_id: 사용자 ID
        user_role: 사용자 역할
        update_data: 업데이트할 데이터

    Returns:
        수정된 포트폴리오 인스턴스

    Raises:
        HTTPException: 검증 실패 또는 포트폴리오를 찾을 수 없거나 권한이 없는 경우
    """
    portfolio = get_portfolio_by_id(db, portfolio_id, user_id, user_role)

    if update_data:
        prepared = validate_and_prepare_portfolio_update_data(update_data)
        portfolio_fields = {col.name for col in Portfolio.__table__.columns}
        for key, value in prepared.items():
            if key in portfolio_fields:
                setattr(portfolio, key, value)

    db.flush()
    db.refresh(portfolio)

    return portfolio


def delete_portfolio(
    db: Session, portfolio_id: str, user_id: str, user_role: Optional[str] = None
) -> None:
    """
    포트폴리오 삭제

    Args:
        db: 데이터베이스 세션
        portfolio_id: 포트폴리오 ID
        user_id: 사용자 ID
        user_role: 사용자 역할

    Raises:
        HTTPException: 포트폴리오를 찾을 수 없거나 권한이 없는 경우
    """
    portfolio = get_portfolio_by_id(db, portfolio_id, user_id, user_role)
    db.delete(portfolio)
    db.flush()
