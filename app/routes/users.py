"""
User 라우트
사용자 인증 및 관리
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.middleware.auth import get_current_user
from app.models.user import User, UserRole
from app.utils.response import success_response, fail_response
from app.utils.error_messages import get_error_message
from app.utils.common import mask_email, mask_phone, normalize_phone_number
from app.services.user_service import (
    create_user,
    authenticate_user,
    get_user_by_id
)
import uuid

router = APIRouter(prefix="/users", tags=["users"])


# Pydantic 스키마
class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=1)
    role: UserRole
    phone: Optional[str] = None
    # brand용
    brand_name: Optional[str] = Field(None, alias="brandName")
    company_name: Optional[str] = Field(None, alias="companyName")
    business_number: Optional[str] = Field(None, alias="businessNumber")
    # showhost용
    nickname: Optional[str] = None
    sns_link: Optional[str] = Field(None, alias="snsLink")
    introduction: Optional[str] = None

    class Config:
        populate_by_name = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: Optional[UserRole] = None  # 선택적: 제공되지 않으면 사용자의 실제 role 사용


class UserResponse(BaseModel):
    id: str
    name: str
    role: str


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    db: Session = Depends(get_db)
):
    """
    회원가입
    역할('brand', 'showhost')에 따라 다른 정보를 받아 사용자를 생성
    """
    # 입력값 검증
    name = request.name.strip()
    email = request.email.lower().strip()
    password = request.password
    role = request.role

    if not name or not email or not password or not role:
        return fail_response("VALIDATION_MISSING_FIELDS", status.HTTP_400_BAD_REQUEST)

    # 'brand' 역할의 경우, 'brandName' 필드가 필수
    if role == UserRole.BRAND and not (request.brand_name or "").strip():
        return fail_response(
            "VALIDATION_MISSING_FIELDS",
            status.HTTP_400_BAD_REQUEST,
            {"userMessage": "브랜드 이름은 필수 입력 항목입니다."}
        )

    # 서비스를 통한 사용자 생성
    user = create_user(
        db,
        name=name,
        email=email,
        password=password,
        role=role,
        phone=request.phone,
        brand_name=request.brand_name,
        company_name=request.company_name,
        business_number=request.business_number,
        nickname=request.nickname,
        sns_link=request.sns_link,
        introduction=request.introduction
    )

    return success_response(
        {"userId": user.id, "role": user.role},
        status_code=status.HTTP_201_CREATED
    )


@router.post("/login")
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    로그인
    이메일, 비밀번호를 받아 로그인 처리 후 JWT 토큰을 발급
    역할(role)은 선택적이며, 제공되지 않으면 사용자의 실제 역할을 사용
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 입력값 검증 및 정규화
    email = request.email.lower().strip() if request.email else ""
    password = request.password or ""
    requested_role = request.role

    logger.info(f"Login attempt for email: {email[:3]}*** (role: {requested_role})")

    if not email or not password:
        logger.warning(f"Login failed: Missing email or password")
        return fail_response("VALIDATION_MISSING_FIELDS", status.HTTP_400_BAD_REQUEST)

    # 서비스를 통한 사용자 인증
    try:
        user, token = authenticate_user(
            db,
            email=email,
            password=password,
            requested_role=requested_role
        )
        user_role_value = user.role.value if hasattr(user.role, 'value') else str(user.role)
        logger.info(f"Login successful for user: {user.id} (email: {email[:3]}***)")
    except Exception as e:
        # HTTPException은 그대로 전파
        raise

    return success_response({
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user_role_value
        }
    })


@router.get("/me")
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    현재 로그인된 사용자의 기본 정보 조회
    """
    user_id = current_user.get("sub")
    if not user_id:
        return fail_response("AUTH_REQUIRED", status.HTTP_401_UNAUTHORIZED)

    user = get_user_by_id(db, user_id)

    normalized_phone = normalize_phone_number(user.phone) if user.phone else None

    return success_response({
        "id": user.id,
        "name": user.name,
        "role": user.role,
        "email": user.email,
        "maskedEmail": mask_email(user.email),
        "phone": user.phone,
        "maskedPhone": mask_phone(user.phone),
        "normalizedPhone": normalized_phone,
    })

