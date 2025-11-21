"""
애플리케이션 설정 관리
환경변수를 통한 설정 로드 및 검증
"""
import os
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
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Cloudinary 설정
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None
    CLOUDINARY_THUMB: str = "c_fill,g_auto,w_640,h_360,f_auto,q_auto"
    
    # API 설정
    API_BASE_PATH: str = "/api/v1"
    JSON_LIMIT: str = "1mb"
    
    # 환경 설정
    ENVIRONMENT: str = "development"
    NODE_ENV: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 전역 설정 인스턴스
settings = Settings()

