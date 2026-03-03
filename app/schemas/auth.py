"""
Auth 도메인 스키마
SMS 인증 요청/응답
"""

from pydantic import BaseModel, Field


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
