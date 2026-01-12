# GHCR 베이스 이미지 사용 (의존성 사전 설치)
ARG GHCR_BASE_IMAGE=ghcr.io/livbee-project/livbee-backend-base:latest
FROM ${GHCR_BASE_IMAGE}

# 애플리케이션 코드 복사 (가장 자주 변경되는 부분을 마지막에)
COPY app/ ./app/

# Alembic 마이그레이션 파일 및 설정 복사
COPY alembic/ ./alembic/
COPY alembic.ini ./

# 포트 노출
EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# uvicorn으로 FastAPI 앱 실행 (단일 워커 - lifespan 이벤트 호환)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

