"""
모델 관련 비즈니스 로직 서비스
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.model import Model
from app.utils.db_helpers import get_or_404, require_ownership_or_admin
import uuid


def get_model_by_id(
    db: Session,
    model_id: str,
    user_id: Optional[str] = None,
    user_role: Optional[str] = None
) -> Model:
    """
    모델 ID로 조회
    
    Args:
        db: 데이터베이스 세션
        model_id: 모델 ID
        user_id: 사용자 ID (소유권 확인용, 선택적)
        user_role: 사용자 역할 (소유권 확인용, 선택적)
    
    Returns:
        모델 인스턴스
    
    Raises:
        HTTPException: 모델을 찾을 수 없거나 권한이 없는 경우
    """
    model = get_or_404(
        db,
        Model,
        lambda q: q.filter(Model.id == model_id),
        error_key="NOT_FOUND"
    )
    
    # 소유권 확인이 필요한 경우
    if user_id:
        require_ownership_or_admin(
            model,
            user_id,
            user_role,
            owner_field="user_id",
            error_key="MODEL_FORBIDDEN_EDIT"
        )
    
    return model


def get_user_models(
    db: Session,
    user_id: str
) -> list[Model]:
    """
    사용자의 모델 목록 조회
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
    
    Returns:
        모델 리스트
    """
    return db.query(Model).filter(
        Model.user_id == user_id
    ).order_by(desc(Model.created_at)).all()


def get_public_models(
    db: Session,
    page: int = 1,
    limit: int = 20
) -> tuple[list[Model], int]:
    """
    공개된 모델 목록 조회
    
    Args:
        db: 데이터베이스 세션
        page: 페이지 번호
        limit: 페이지당 항목 수
    
    Returns:
        (모델 리스트, 전체 개수) 튜플
    """
    skip = (page - 1) * limit
    
    query = db.query(Model).filter(
        Model.public_scope == "전체공개",
        Model.status == "published"
    )
    
    total_items = query.count()
    models = query.order_by(desc(Model.created_at)).offset(skip).limit(limit).all()
    
    return models, total_items


def get_published_models(
    db: Session,
    page: int = 1,
    limit: int = 10
) -> tuple[list[Model], int]:
    """
    published 상태의 모델 목록 조회
    
    Args:
        db: 데이터베이스 세션
        page: 페이지 번호
        limit: 페이지당 항목 수
    
    Returns:
        (모델 리스트, 전체 개수) 튜플
    """
    skip = (page - 1) * limit
    
    query = db.query(Model).filter(
        Model.status == "published"
    )
    
    total_items = query.count()
    models = query.order_by(desc(Model.created_at)).offset(skip).limit(limit).all()
    
    return models, total_items


def check_user_has_model(
    db: Session,
    user_id: str
) -> bool:
    """
    사용자가 모델을 가지고 있는지 확인
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
    
    Returns:
        모델 존재 여부
    """
    model = db.query(Model).filter(Model.user_id == user_id).first()
    return model is not None


def create_model(
    db: Session,
    user_id: str,
    model_data: Dict[str, Any]
) -> Model:
    """
    모델 생성
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        model_data: 모델 데이터
    
    Returns:
        생성된 모델 인스턴스
    
    Raises:
        HTTPException: 이미 모델이 있는 경우
    """
    # 중복 체크
    if check_user_has_model(db, user_id):
        from fastapi import HTTPException, status
        from app.utils.error_messages import get_error_message
        error = get_error_message("PORTFOLIO_DUP")  # 동일한 에러 메시지 사용
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "MODEL_DUP",
                "message": error["message"],
                "userMessage": "이미 모델이 등록되어 있습니다.",
            }
        )
    
    model_data["id"] = str(uuid.uuid4())
    model_data["user_id"] = user_id
    
    model = Model(**model_data)
    db.add(model)
    db.flush()  # 세션 변경사항을 DB에 반영 (커밋은 아님)
    db.refresh(model)
    
    return model


def update_model(
    db: Session,
    model_id: str,
    user_id: str,
    user_role: Optional[str] = None,
    update_data: Optional[Dict[str, Any]] = None
) -> Model:
    """
    모델 수정
    
    Args:
        db: 데이터베이스 세션
        model_id: 모델 ID
        user_id: 사용자 ID
        user_role: 사용자 역할
        update_data: 업데이트할 데이터
    
    Returns:
        수정된 모델 인스턴스
    
    Raises:
        HTTPException: 모델을 찾을 수 없거나 권한이 없는 경우
    """
    model = get_model_by_id(db, model_id, user_id, user_role)
    
    if update_data:
        for key, value in update_data.items():
            setattr(model, key, value)
    
    db.refresh(model)
    
    return model


def delete_model(
    db: Session,
    model_id: str,
    user_id: str,
    user_role: Optional[str] = None
) -> None:
    """
    모델 삭제
    
    Args:
        db: 데이터베이스 세션
        model_id: 모델 ID
        user_id: 사용자 ID
        user_role: 사용자 역할
    
    Raises:
        HTTPException: 모델을 찾을 수 없거나 권한이 없는 경우
    """
    model = get_model_by_id(db, model_id, user_id, user_role)
    db.delete(model)
