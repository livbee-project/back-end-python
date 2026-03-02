"""
FastAPI 메인 애플리케이션
PostgreSQL 데이터베이스 연결 및 기본 엔드포인트 제공
"""

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import engine, init_db
from app.core.logging_config import get_logger, setup_logging
from app.core.rate_limit import limiter
from app.utils.response import fail_response, success_response

# 로깅 설정
setup_logging()
logger = get_logger(__name__)


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
        # Prod: Alembic으로 마이그레이션 관리 → init_db 스킵
        # Dev 등: 로컬 개발 편의를 위해 init_db 호출
        if settings.ENVIRONMENT != "production":
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
    description="Livbee 백엔드 API 서버 - 쇼호스트와 브랜드를 연결하는 플랫폼",
    lifespan=lifespan,
    docs_url="/api-docs",  # 모든 환경에서 Swagger UI 활성화
    redoc_url=None,
)

# Rate Limiting 설정 (slowapi)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Rate limit 초과 시 429 응답 (fail_response 형식)"""
    return fail_response("RATE_LIMIT_EXCEEDED", status.HTTP_429_TOO_MANY_REQUESTS)


# Swagger UI에 JWT 인증 추가
def custom_openapi():
    """OpenAPI 스키마 커스터마이징 - JWT 인증 추가"""
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # JWT Bearer 인증 스키마 추가
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT 토큰을 입력하세요. 로그인 API에서 받은 토큰을 사용합니다.",
        }
    }

    # 모든 엔드포인트에 기본 보안 적용 (인증이 필요한 경우)
    # 실제로는 각 라우터에서 security를 지정하므로 여기서는 스키마만 정의

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# CORS 설정
def get_cors_origins():
    """
    CORS 허용 origin 목록 반환
    환경변수 CORS_ORIGINS가 설정되어 있으면 해당 값 사용
    없으면 개발 환경에서는 localhost와 dev 도메인 허용
    """
    if settings.CORS_ORIGINS:
        # 환경변수에서 쉼표로 구분된 origin 목록 파싱
        origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
        logger.info(f"✅ CORS origins from env: {origins}")
        return origins

    # 기본값: 개발 환경용 origin 목록
    default_origins = [
        "http://localhost:5173",  # Vite 기본 포트
        "http://localhost:3000",  # React 기본 포트
        "http://localhost:5174",  # 추가 개발 포트
        "https://dev-api.livbee.co.kr",  # 개발 API 서버
        "https://dev.livbee.co.kr",  # 개발 프론트엔드
    ]

    # 프로덕션 환경인 경우 프로덕션 도메인 추가
    if settings.ENVIRONMENT == "production":
        default_origins.extend(
            [
                "https://api.livbee.co.kr",
                "https://livbee.co.kr",
                "https://www.livbee.co.kr",
            ]
        )

    logger.info(f"✅ CORS origins (default): {default_origins}")
    return default_origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)


# 전역 예외 핸들러
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTPException 응답을 fail_response 형식으로 통일
    - detail이 dict({ error, message, userMessage }) → 최상위로 펼쳐서 반환
    - detail이 문자열 → userMessage로 사용
    프론트에서 response.userMessage로 일관되게 추출 가능
    """
    detail = exc.detail
    if isinstance(detail, dict):
        error = detail.get("error", "ERROR")
        message = detail.get("message", "An error occurred")
        user_message = detail.get("userMessage", message)
    else:
        error = "ERROR"
        message = str(detail) if detail else "An error occurred"
        user_message = message

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "ok": False,
            "error": error,
            "message": message,
            "userMessage": user_message,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """요청 검증 오류 처리 - 필드별 오류(loc, msg, type) 포함 (민감정보 아님)"""
    errors = [
        {"loc": list(e.get("loc", ())), "msg": e.get("msg", ""), "type": e.get("type", "")}
        for e in exc.errors()
    ]
    return fail_response(
        "VALIDATION_FAILED",
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        additional_data={"errors": errors},
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """데이터베이스 오류 처리"""
    logger.error(f"Database error: {exc}", exc_info=True)
    # CORS는 미들웨어에서 처리되므로 별도 헤더 추가 불필요
    return fail_response("INTERNAL_ERROR", status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    # CORS는 미들웨어에서 처리되므로 별도 헤더 추가 불필요
    return fail_response("INTERNAL_ERROR", status.HTTP_500_INTERNAL_SERVER_ERROR)


# 라우터 등록
from app.routes import (
    applications,
    campaigns,
    chat,
    models,
    news,
    portfolios,
    proposals,
    studios,
    uploads,
    users,
)

app.include_router(users.router, prefix=settings.API_BASE_PATH)
app.include_router(portfolios.router, prefix=settings.API_BASE_PATH)
app.include_router(models.router, prefix=settings.API_BASE_PATH)
app.include_router(campaigns.router, prefix=settings.API_BASE_PATH)
app.include_router(applications.router, prefix=settings.API_BASE_PATH)
app.include_router(proposals.router, prefix=settings.API_BASE_PATH)
app.include_router(news.router, prefix=settings.API_BASE_PATH)
app.include_router(studios.router, prefix=settings.API_BASE_PATH)
app.include_router(chat.router, prefix=settings.API_BASE_PATH)
app.include_router(uploads.router, prefix=settings.API_BASE_PATH)


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

        return success_response(
            {"message": "데이터베이스 연결 성공", "database_version": db_version}
        )
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return fail_response("INTERNAL_ERROR", status.HTTP_500_INTERNAL_SERVER_ERROR)
