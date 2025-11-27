"""
PostgreSQL 데이터베이스 연결 관리
SQLAlchemy를 사용한 연결 풀 관리
"""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# 데이터베이스 URL 생성
DATABASE_URL = (
    f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# SQLAlchemy 엔진 생성 (연결 풀 사용)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 연결 유효성 검사
    pool_size=10,  # 연결 풀 크기
    max_overflow=20,  # 최대 오버플로우
    pool_recycle=3600,  # 1시간마다 연결 재생성
    echo=False,  # SQL 쿼리 로깅 (개발 시 True)
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 (모델 상속용)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 의존성
    FastAPI의 Depends에서 사용
    자동 커밋/롤백 처리
    """
    db = SessionLocal()
    try:
        yield db
        # 예외가 없으면 자동 커밋
        db.commit()
    except SQLAlchemyError as e:
        # 데이터베이스 오류 발생 시 롤백
        db.rollback()
        logger.error(f"Database error, rolling back: {e}", exc_info=True)
        raise
    except Exception as e:
        # 기타 예외 발생 시 롤백
        db.rollback()
        logger.error(f"Unexpected error, rolling back: {e}", exc_info=True)
        raise
    finally:
        db.close()


@contextmanager
def get_db_transaction() -> Generator[Session, None, None]:
    """
    트랜잭션 컨텍스트 매니저
    명시적 트랜잭션 관리가 필요한 경우 사용
    
    Usage:
        with get_db_transaction() as db:
            # 작업 수행
            db.add(model)
            # 자동 커밋 (예외 없을 시)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in transaction, rolling back: {e}", exc_info=True)
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in transaction, rolling back: {e}", exc_info=True)
        raise
    finally:
        db.close()


def init_db():
    """
    데이터베이스 초기화
    테이블 생성 등
    """
    # 모든 모델 import (테이블 생성용)
    # 모델들이 Base를 상속받아 자동으로 메타데이터에 등록됨
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)

