"""
애플리케이션 설정 관리
환경변수를 통한 설정 로드 및 검증
"""

import re
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 데이터베이스 설정
    DB_HOST: str
    DB_PORT: str = "5432"
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    # JWT 설정
    JWT_SECRET: str  # 필수 (애플리케이션 실행 시 필요)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24  # 기본값 24시간
    JWT_EXPIRES_IN: Optional[str] = None  # "7d", "24h" 등 (선택적, JWT_EXPIRATION_HOURS 우선)

    # Cloudinary 설정
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None
    CLOUDINARY_THUMB: str = "c_fill,g_auto,w_640,h_360,f_auto,q_auto"
    CLOUDINARY_FOLDER: Optional[str] = None  # 업로드 폴더 경로
    CLOUDINARY_URL: Optional[str] = (
        None  # cloudinary://API_KEY:API_SECRET 형식 (선택적, 자동 파싱용)
    )

    # API 설정
    API_BASE_PATH: str = "/api/v1"
    JSON_LIMIT: str = "1mb"

    # 환경 설정
    ENVIRONMENT: str = "development"
    NODE_ENV: str = "development"

    # CORS 설정
    CORS_ORIGINS: Optional[str] = (
        None  # 쉼표로 구분된 origin 목록 (예: "http://localhost:5173,https://dev.livbee.co.kr")
    )

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 추가 환경변수 허용


# 전역 설정 인스턴스
_settings_instance = None


def get_settings() -> Settings:
    """Settings 인스턴스 가져오기 (CLOUDINARY_URL 자동 파싱)"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()

        # CLOUDINARY_URL이 있으면 자동으로 파싱
        if _settings_instance.CLOUDINARY_URL and not _settings_instance.CLOUDINARY_API_KEY:
            try:
                # cloudinary://API_KEY:API_SECRET@CLOUD_NAME 또는 cloudinary://API_KEY:API_SECRET 형식
                match = re.match(
                    r"cloudinary://([^:]+):([^@]+)(?:@(.+))?", _settings_instance.CLOUDINARY_URL
                )
                if match:
                    api_key, api_secret, cloud_name = match.groups()
                    if not _settings_instance.CLOUDINARY_API_KEY:
                        _settings_instance.CLOUDINARY_API_KEY = api_key
                    if not _settings_instance.CLOUDINARY_API_SECRET:
                        _settings_instance.CLOUDINARY_API_SECRET = api_secret
                    if cloud_name and not _settings_instance.CLOUDINARY_CLOUD_NAME:
                        _settings_instance.CLOUDINARY_CLOUD_NAME = cloud_name
            except Exception:
                pass  # 파싱 실패 시 무시

        # JWT_EXPIRES_IN이 있으면 JWT_EXPIRATION_HOURS로 변환
        if _settings_instance.JWT_EXPIRES_IN and _settings_instance.JWT_EXPIRATION_HOURS == 24:
            try:
                expires_in = _settings_instance.JWT_EXPIRES_IN.lower()
                if expires_in.endswith("d"):
                    days = int(expires_in[:-1])
                    _settings_instance.JWT_EXPIRATION_HOURS = days * 24
                elif expires_in.endswith("h"):
                    _settings_instance.JWT_EXPIRATION_HOURS = int(expires_in[:-1])
            except Exception:
                pass  # 변환 실패 시 기본값 유지

    return _settings_instance


# 전역 설정 인스턴스 (하위 호환성)
settings = get_settings()
