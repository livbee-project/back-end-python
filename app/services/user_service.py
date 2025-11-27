"""
사용자 관련 비즈니스 로직 서비스
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.core.security import verify_password, get_password_hash, create_access_token
from app.utils.db_helpers import get_or_404
import uuid


def get_user_by_email(
    db: Session,
    email: str
) -> Optional[User]:
    """
    이메일로 사용자 조회
    
    Args:
        db: 데이터베이스 세션
        email: 이메일 주소
    
    Returns:
        사용자 인스턴스 또는 None
    """
    return db.query(User).filter(User.email == email.lower().strip()).first()


def get_user_by_id(
    db: Session,
    user_id: str
) -> User:
    """
    사용자 ID로 조회
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
    
    Returns:
        사용자 인스턴스
    
    Raises:
        HTTPException: 사용자를 찾을 수 없는 경우
    """
    return get_or_404(
        db,
        User,
        lambda q: q.filter(User.id == user_id),
        error_key="NOT_FOUND"
    )


def create_user(
    db: Session,
    name: str,
    email: str,
    password: str,
    role: UserRole,
    phone: Optional[str] = None,
    brand_name: Optional[str] = None,
    company_name: Optional[str] = None,
    business_number: Optional[str] = None,
    nickname: Optional[str] = None,
    sns_link: Optional[str] = None,
    introduction: Optional[str] = None
) -> User:
    """
    사용자 생성
    
    Args:
        db: 데이터베이스 세션
        name: 이름
        email: 이메일
        password: 비밀번호 (평문)
        role: 역할
        phone: 전화번호
        brand_name: 브랜드명 (brand 역할일 때)
        company_name: 회사명 (brand 역할일 때)
        business_number: 사업자번호 (brand 역할일 때)
        nickname: 닉네임 (showhost 역할일 때)
        sns_link: SNS 링크 (showhost 역할일 때)
        introduction: 소개 (showhost 역할일 때)
    
    Returns:
        생성된 사용자 인스턴스
    
    Raises:
        HTTPException: 이미 존재하는 이메일인 경우
    """
    # 중복 이메일 확인
    existing_user = get_user_by_email(db, email)
    if existing_user:
        from fastapi import HTTPException, status
        from app.utils.error_messages import get_error_message
        error = get_error_message("DUPLICATE")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "DUPLICATE",
                "message": error["message"],
                "userMessage": error["userMessage"],
            }
        )
    
    # 비밀번호 해시
    hashed_password = get_password_hash(password)
    
    # 사용자 데이터 생성
    user_data = {
        "id": str(uuid.uuid4()),
        "name": name.strip(),
        "email": email.lower().strip(),
        "password": hashed_password,
        "role": role.value,
        "phone": phone.strip() if phone else None,
    }
    
    # 역할에 따라 해당 역할 전용 정보 추가
    if role == UserRole.BRAND:
        user_data["brand_name"] = brand_name.strip() if brand_name else None
        user_data["company_name"] = company_name.strip() if company_name else None
        user_data["business_number"] = business_number.strip() if business_number else None
    else:  # showhost
        user_data["nickname"] = nickname.strip() if nickname else None
        user_data["sns_link"] = sns_link.strip() if sns_link else None
        user_data["introduction"] = introduction.strip() if introduction else None
    
    user = User(**user_data)
    db.add(user)
    db.refresh(user)
    
    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
    requested_role: Optional[UserRole] = None
) -> tuple[User, str]:
    """
    사용자 인증 및 JWT 토큰 생성
    
    Args:
        db: 데이터베이스 세션
        email: 이메일
        password: 비밀번호 (평문)
        requested_role: 요청한 역할 (선택적)
    
    Returns:
        (사용자 인스턴스, JWT 토큰) 튜플
    
    Raises:
        HTTPException: 인증 실패 시
    """
    # 이메일로 사용자 찾기
    user = get_user_by_email(db, email)
    if not user:
        from fastapi import HTTPException, status
        from app.utils.error_messages import get_error_message
        error = get_error_message("INVALID_CREDENTIALS")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_CREDENTIALS",
                "message": error["message"],
                "userMessage": error["userMessage"],
            }
        )
    
    # 비밀번호 확인
    if not user.password or not verify_password(password, user.password):
        from fastapi import HTTPException, status
        from app.utils.error_messages import get_error_message
        error = get_error_message("INVALID_CREDENTIALS")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_CREDENTIALS",
                "message": error["message"],
                "userMessage": error["userMessage"],
            }
        )
    
    # 역할 확인
    user_role_value = user.role.value if hasattr(user.role, 'value') else str(user.role)
    if requested_role:
        requested_role_value = requested_role.value if hasattr(requested_role, 'value') else str(requested_role)
        if user_role_value != requested_role_value:
            from fastapi import HTTPException, status
            from app.utils.error_messages import get_error_message
            error = get_error_message("ROLE_MISMATCH")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "ROLE_MISMATCH",
                    "message": error["message"],
                    "userMessage": error["userMessage"],
                }
            )
    
    # JWT 토큰 생성
    from app.core.config import settings
    if not settings.JWT_SECRET or not settings.JWT_SECRET.strip():
        from fastapi import HTTPException, status
        from app.utils.error_messages import get_error_message
        error = get_error_message("INTERNAL_ERROR")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": error["message"],
                "userMessage": error["userMessage"],
            }
        )
    
    token = create_access_token(
        data={"sub": user.id, "role": user_role_value},
    )
    
    return user, token

