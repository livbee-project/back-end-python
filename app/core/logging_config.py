"""
로깅 설정 모듈
일관된 로깅 설정 제공
"""
import logging
import sys
from typing import Optional


def setup_logging(level: Optional[str] = None) -> None:
    """
    애플리케이션 전역 로깅 설정
    
    Args:
        level: 로깅 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               기본값: INFO
    """
    log_level = getattr(logging, level.upper() if level else "INFO", logging.INFO)
    
    # 로깅 포맷 설정
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 기본 로깅 설정
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # SQLAlchemy 로깅 레벨 조정 (너무 많은 로그 방지)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    모듈별 로거 생성
    
    Args:
        name: 로거 이름 (보통 __name__ 사용)
    
    Returns:
        설정된 로거 인스턴스
    """
    return logging.getLogger(name)

