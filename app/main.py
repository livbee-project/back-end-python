"""
FastAPI 메인 애플리케이션
PostgreSQL 데이터베이스 연결 및 기본 엔드포인트 제공
"""
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.core.database import engine, init_db
from app.utils.response import success_response, fail_response
from app.utils.error_messages import get_error_message

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리
    시작 시 DB 초기화, 종료 시 정리 작업
    """
    # 시작 시
    logger.info("🚀 Livbee Backend API 시작 중...")
    
    # 필수 환경변수 검증
    required_vars = [
        ("DB_HOST", "데이터베이스 호스트"),
        ("DB_NAME", "데이터베이스 이름"),
        ("DB_USER", "데이터베이스 사용자"),
        ("DB_PASSWORD", "데이터베이스 비밀번호"),
        ("JWT_SECRET", "JWT 토큰 서명용 비밀키"),
    ]
    
    missing_vars = []
    for var_name, description in required_vars:
        if not getattr(settings, var_name, None):
            missing_vars.append(f"{var_name}: {description}")
    
    if missing_vars:
        logger.error("❌ 필수 환경 변수가 누락되었습니다:")
        for var in missing_vars:
            logger.error(f"   - {var}")
        logger.error("서버를 시작할 수 없습니다.")
        sys.exit(1)
    
    logger.info("✅ 필수 환경 변수 검증 완료")
    
    # 데이터베이스 연결 테스트 및 테이블 생성
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ 데이터베이스 연결 확인 완료")
        
        # 테이블 생성 (모델이 정의된 경우)
        try:
            init_db()
            logger.info("✅ 데이터베이스 테이블 초기화 완료")
        except Exception as e:
            logger.warning(f"⚠️ 테이블 초기화 실패 (계속 진행): {e}")
    except Exception as e:
        logger.warning(f"⚠️ 데이터베이스 연결 실패 (계속 진행): {e}")
        # 연결 실패해도 앱은 시작 (나중에 재시도 가능)
    
    yield
    
    # 종료 시
    logger.info("🛑 Livbee Backend API 종료 중...")


# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="Livbee Backend API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api-docs" if settings.NODE_ENV != "production" else None,
    redoc_url=None,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 전역 예외 핸들러
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """요청 검증 오류 처리"""
    return fail_response("VALIDATION_FAILED", status.HTTP_422_UNPROCESSABLE_ENTITY)


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """데이터베이스 오류 처리"""
    logger.error(f"Database error: {exc}")
    return fail_response("INTERNAL_ERROR", status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return fail_response("INTERNAL_ERROR", status.HTTP_500_INTERNAL_SERVER_ERROR)


# 기본 라우트
@app.get("/")
async def root():
    """기본 라우트 - Hello 메시지 반환"""
    return success_response({"message": "Hello Livbee"})


@app.get("/healthz")
async def healthz():
    """헬스체크 엔드포인트 (Kubernetes liveness probe용)"""
    return success_response({"status": "healthy"})


@app.get("/readyz")
async def readyz():
    """준비 상태 체크 엔드포인트 (Kubernetes readiness probe용)"""
    # 데이터베이스 연결 확인
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return success_response({"status": "ready"})
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return fail_response("INTERNAL_ERROR", status.HTTP_503_SERVICE_UNAVAILABLE)


@app.get("/db-test")
async def db_test():
    """데이터베이스 연결 테스트 엔드포인트"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            db_version = result.fetchone()[0] if result else "Unknown"
        
        return success_response({
            "message": "데이터베이스 연결 성공",
            "database_version": db_version
        })
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return fail_response("INTERNAL_ERROR", status.HTTP_500_INTERNAL_SERVER_ERROR)

