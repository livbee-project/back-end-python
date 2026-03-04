"""
Auth 도메인 스키마
SMS 인증 요청/응답
"""

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class SendSmsRequest(BaseModel):
    """SMS 인증번호 발송 요청"""

    phone_number: str = Field(..., min_length=1, alias="phoneNumber")

    class Config:
        populate_by_name = True


class VerifySmsRequest(BaseModel):
    """SMS 인증번호 검증 요청"""

    phone_number: str = Field(..., min_length=1, alias="phoneNumber")
    code: str = Field(..., min_length=6, max_length=6)

    class Config:
        populate_by_name = True


class KakaoLoginRequest(BaseModel):
    """카카오 간편 로그인 요청"""

    kakao_id: str = Field(..., min_length=1, alias="kakaoId")
    email: EmailStr
    name: str
    role: UserRole

    class Config:
        populate_by_name = True
