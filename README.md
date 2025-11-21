# Livbee Backend API

FastAPI 기반 백엔드 API 서버입니다.

## 📋 프로젝트 개요

- **Framework**: FastAPI (Python 3.10)
- **Database**: PostgreSQL 16
- **Deployment**: Docker + GitHub Actions CI/CD
- **Infrastructure**: Oracle Cloud Free Tier

## 🚀 빠른 시작

### 로컬 개발 환경 설정

1. **저장소 클론**
   ```bash
   git clone https://github.com/livbee-project/back-end-python.git
   cd back-end-python
   ```

2. **가상환경 생성 및 활성화**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

4. **환경변수 설정**
   ```bash
   # .env 파일을 생성하고 다음 환경변수를 설정하세요
   # DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
   ```

5. **서버 실행**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **API 테스트**
   - 기본 엔드포인트: http://localhost:8000/
   - DB 연결 테스트: http://localhost:8000/db-test

## 📁 프로젝트 구조

```
back-end-python/
├── app/
│   ├── __init__.py
│   └── main.py              # FastAPI 메인 애플리케이션
├── .github/
│   └── workflows/
│       ├── deploy-dev.yml   # Dev 환경 배포 워크플로우
│       └── deploy-prod.yml  # Prod 환경 배포 워크플로우
├── deploy/
│   ├── deploy.sh            # 공통 배포 스크립트
│   └── docker-compose.yml   # Docker Compose 설정
├── nginx/
│   ├── nginx-dev.conf       # Dev Nginx 설정
│   └── nginx-prod.conf      # Prod Nginx 설정
├── docs/
│   └── DEPLOYMENT.md        # 상세 배포 가이드
├── Dockerfile               # Docker 이미지 빌드 설정
├── requirements.txt         # Python 패키지 의존성
└── README.md               # 프로젝트 문서
```

## 🔧 개발

### API 엔드포인트

- `GET /`: 기본 Hello 메시지
- `GET /db-test`: 데이터베이스 연결 테스트

### 환경변수

필요한 환경변수:
- `DB_HOST`: 데이터베이스 호스트 주소
- `DB_PORT`: 데이터베이스 포트 (기본값: 5432)
- `DB_NAME`: 데이터베이스 이름
- `DB_USER`: 데이터베이스 사용자명
- `DB_PASSWORD`: 데이터베이스 비밀번호

**보안 주의:** `.env` 파일은 절대 Git에 커밋하지 마세요. 모든 민감 정보는 GitHub Secrets로 관리됩니다.

## 🚢 배포

자세한 배포 가이드는 [DEPLOYMENT.md](docs/DEPLOYMENT.md)를 참고하세요.

### 간단한 배포 프로세스

1. **Dev 환경**: `dev` 브랜치에 push하면 자동 배포
2. **Prod 환경**: `main` 또는 `master` 브랜치에 push하면 배포

### 배포 전 필수 작업

1. GitHub Secrets 설정 (레포지토리 설정 → Secrets and variables → Actions)
2. 서버 초기 설정 (Docker, Nginx 설치)
3. Nginx 설정 및 SSL 인증서 발급

## 📚 문서

- [배포 가이드](docs/DEPLOYMENT.md) - 상세한 배포 및 설정 가이드

## 🔒 보안

- 모든 민감 정보는 GitHub Secrets로 관리
- `.env` 파일은 절대 Git에 커밋하지 않음
- 프로덕션 환경은 수동 승인 단계 포함

## 📝 라이선스

이 프로젝트는 Livbee 프로젝트의 일부입니다.