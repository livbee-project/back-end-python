"""
User 라우트
사용자 인증 및 관리
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.middleware.auth import get_current_user
from app.models.user import User, UserRole
from app.utils.response import success_response, fail_response
from app.utils.error_messages import get_error_message
from app.utils.common import mask_email, mask_phone, normalize_phone_number
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
    role: UserRole


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

    # 동일한 이메일로 가입된 사용자가 있는지 확인
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return fail_response("DUPLICATE", status.HTTP_409_CONFLICT)

    # 비밀번호 해시
    hashed_password = get_password_hash(password)

    # 사용자 데이터 생성
    phone_value = (request.phone or "").strip() if request.phone else None

    user_data = {
        "id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "password": hashed_password,
        "role": role.value,
        "phone": phone_value,
    }

    # 역할에 따라 해당 역할 전용 정보 추가
    if role == UserRole.BRAND:
        user_data["brand_name"] = (request.brand_name or "").strip() if request.brand_name else None
        user_data["company_name"] = (request.company_name or "").strip() if request.company_name else None
        user_data["business_number"] = (request.business_number or "").strip() if request.business_number else None
    else:  # showhost
        user_data["nickname"] = (request.nickname or "").strip() if request.nickname else None
        user_data["sns_link"] = (request.sns_link or "").strip() if request.sns_link else None
        user_data["introduction"] = (request.introduction or "").strip() if request.introduction else None

    # 사용자 생성
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)

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
    이메일, 비밀번호, 역할을 받아 로그인 처리 후 JWT 토큰을 발급
    """
    email = request.email.lower().strip()
    password = request.password
    role = request.role

    if not email or not password or not role:
        return fail_response("VALIDATION_MISSING_FIELDS", status.HTTP_400_BAD_REQUEST)

    # 이메일로 사용자 찾기
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return fail_response("INVALID_CREDENTIALS", status.HTTP_401_UNAUTHORIZED)

    # 역할 확인
    if user.role != role.value:
        return fail_response("ROLE_MISMATCH", status.HTTP_401_UNAUTHORIZED)

    # 비밀번호 확인
    if not verify_password(password, user.password):
        return fail_response("INVALID_CREDENTIALS", status.HTTP_401_UNAUTHORIZED)

    # JWT 토큰 생성
    token = create_access_token(
        data={"sub": user.id, "role": user.role},
    )

    return success_response({
        "token": token,
        "name": user.name,
        "role": user.role
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

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return fail_response("NOT_FOUND", status.HTTP_404_NOT_FOUND)

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

