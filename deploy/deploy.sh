#!/bin/bash

# 공통 배포 스크립트
# 사용법: ./deploy.sh [dev|prod]

set -e  # 에러 발생 시 스크립트 중단

# 환경 변수 확인
ENV=${1:-dev}
if [[ ! "$ENV" =~ ^(dev|prod)$ ]]; then
    echo "❌ 오류: 환경은 'dev' 또는 'prod'여야 합니다."
    exit 1
fi

echo "🚀 [$ENV] 환경 배포 시작..."

# 환경별 변수 설정
if [ "$ENV" = "dev" ]; then
    DB_HOST="${DEV_DB_HOST}"
    DB_PORT="${DEV_DB_PORT:-5432}"
    DB_NAME="${DEV_DB_NAME}"
    DB_USER="${DEV_DB_USER}"
    DB_PASSWORD="${DEV_DB_PASSWORD}"
    IMAGE_TAG="dev-latest"
    COMPOSE_FILE="deploy/docker-compose.yml"
else
    DB_HOST="${PROD_DB_HOST}"
    DB_PORT="${PROD_DB_PORT:-5432}"
    DB_NAME="${PROD_DB_NAME}"
    DB_USER="${PROD_DB_USER}"
    DB_PASSWORD="${PROD_DB_PASSWORD}"
    IMAGE_TAG="prod-latest"
    COMPOSE_FILE="deploy/docker-compose.yml"
fi

# 필수 환경변수 검증
if [ -z "$DB_HOST" ] || [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
    echo "❌ 오류: 필수 데이터베이스 환경변수가 설정되지 않았습니다."
    exit 1
fi

# 작업 디렉토리 확인
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ 오류: $COMPOSE_FILE 파일을 찾을 수 없습니다."
    exit 1
fi

# .env 파일 생성
ENV_FILE=".env"
cat > "$ENV_FILE" <<EOF
# $ENV 환경 변수
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
EOF

echo "✅ 환경변수 파일 생성 완료"

# Docker 이미지 빌드 (로컬에서 빌드하는 경우)
if [ "$BUILD_LOCALLY" = "true" ]; then
    echo "📦 Docker 이미지 빌드 중..."
    docker build -t livbee-backend:$IMAGE_TAG .
    echo "✅ Docker 이미지 빌드 완료"
fi

# Docker Compose로 서비스 재시작
echo "🔄 Docker 컨테이너 재시작 중..."
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build

echo "⏳ 컨테이너 시작 대기 중..."
sleep 5

# 헬스체크
echo "🏥 헬스체크 수행 중..."
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        # 컨테이너가 실행 중이면 헬스체크 엔드포인트 호출
        HEALTH_CHECK_URL="http://localhost:8000/db-test"
        if curl -f -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            echo "✅ 헬스체크 성공!"
            echo "🎉 [$ENV] 환경 배포 완료!"
            exit 0
        fi
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "⏳ 재시도 중... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 3
done

echo "❌ 헬스체크 실패: 배포에 문제가 있을 수 있습니다."
echo "📋 컨테이너 로그 확인:"
docker-compose -f "$COMPOSE_FILE" logs --tail=50

exit 1

