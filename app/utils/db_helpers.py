"""
데이터베이스 조회 및 권한 확인 헬퍼 함수
"""
from typing import TypeVar, Type, Optional, Callable, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from fastapi import status, HTTPException
from app.utils.response import fail_response
from app.utils.error_messages import get_error_message

T = TypeVar('T')


def get_or_404(
    db: Session,
    model: Type[T],
    filter_condition: Callable,
    error_key: str = "NOT_FOUND",
    error_message: Optional[str] = None
) -> T:
    """
    모델을 조회하고 없으면 404 응답 반환
    
    Args:
        db: 데이터베이스 세션
        model: SQLAlchemy 모델 클래스
        filter_condition: 필터 조건 함수 (예: lambda q: q.filter(Model.id == id))
        error_key: 에러 키 (기본값: "NOT_FOUND")
        error_message: 커스텀 에러 메시지
    
    Returns:
        모델 인스턴스
    
    Raises:
        HTTPException: 리소스를 찾을 수 없는 경우
    """
    query = db.query(model)
    query = filter_condition(query)
    instance = query.first()
    
    if not instance:
        error = get_error_message(error_key)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": error_key,
                "message": error_message or error["message"],
                "userMessage": error["userMessage"],
            }
        )
    
    return instance


def check_ownership(
    resource: Any,
    owner_id: str,
    owner_field: str = "created_by",
    allow_admin: bool = True,
    user_role: Optional[str] = None
) -> bool:
    """
    리소스 소유권 확인
    
    Args:
        resource: 리소스 인스턴스
        owner_id: 소유자 ID
        owner_field: 소유자 필드명 (기본값: "created_by")
        allow_admin: admin 역할 허용 여부
        user_role: 사용자 역할
    
    Returns:
        소유권이 있으면 True
    """
    if not resource:
        return False
    
    # admin은 모든 리소스에 접근 가능
    if allow_admin and user_role == "admin":
        return True
    
    # 소유자 확인
    resource_owner_id = getattr(resource, owner_field, None)
    return resource_owner_id == owner_id


def require_ownership_or_admin(
    resource: Any,
    user_id: str,
    user_role: Optional[str] = None,
    owner_field: str = "created_by",
    error_key: str = "FORBIDDEN"
) -> None:
    """
    리소스 소유권 확인, 없으면 403 에러 발생
    
    Args:
        resource: 리소스 인스턴스
        user_id: 사용자 ID
        user_role: 사용자 역할
        owner_field: 소유자 필드명
        error_key: 에러 키
    
    Raises:
        HTTPException: 소유권이 없는 경우
    """
    if not check_ownership(resource, user_id, owner_field, allow_admin=True, user_role=user_role):
        error = get_error_message(error_key)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": error_key,
                "message": error["message"],
                "userMessage": error["userMessage"],
            }
        )

