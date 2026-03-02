"""
User 도메인 스키마
사용자 인증 및 관리 관련 요청/응답
"""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


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
