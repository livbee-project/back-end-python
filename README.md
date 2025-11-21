# Livbee Backend API

FastAPI 기반 백엔드 API 서버입니다.

## 📋 프로젝트 개요

- **Framework**: FastAPI (Python 3.10)
- **Database**: PostgreSQL 16
- **Deployment**: Docker + GitHub Actions CI/CD
- **Infrastructure**: Oracle Cloud Free Tier (OCI)
- **Web Server**: Nginx (Reverse Proxy)
- **SSL**: Let's Encrypt (Certbot)

### 브랜치 전략

- **`dev` 브랜치**: 개발 환경 자동 배포
- **`prod` 브랜치**: 운영 환경 자동 배포

---

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
   .\venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   ```

3. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

4. **환경변수 설정**
   
   프로젝트 루트에 `.env` 파일을 생성하고 다음 환경변수를 설정하세요:
   
   ```ini
   DB_HOST=your_database_host
   DB_PORT=5432
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   ```
   
   **⚠️ 보안 주의:** `.env` 파일은 절대 Git에 커밋하지 마세요. `.gitignore`에 포함되어 있습니다.

5. **데이터베이스 마이그레이션** (선택사항)
   ```bash
   # 초기 마이그레이션 생성 (첫 실행 시)
   alembic revision --autogenerate -m "Initial migration"
   
   # 마이그레이션 적용
   alembic upgrade head
   ```
   
   > **참고**: 로컬 개발 환경에서는 `init_db()` 함수가 자동으로 테이블을 생성하지만, 프로덕션 환경에서는 Alembic 마이그레이션을 사용하는 것을 권장합니다.

6. **서버 실행**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **API 테스트**
   - 기본 엔드포인트: http://localhost:8000/
   - DB 연결 테스트: http://localhost:8000/db-test
   - API 문서: http://localhost:8000/api-docs

---

## 📁 프로젝트 구조

```
back-end-python/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 메인 애플리케이션
│   ├── core/                # 핵심 설정 (config, database, security)
│   ├── models/              # SQLAlchemy 모델
│   ├── routes/              # API 라우터
│   ├── middleware/          # 인증/권한 미들웨어
│   └── utils/               # 유틸리티 함수
├── alembic/                 # Alembic 마이그레이션
│   ├── versions/            # 마이그레이션 파일
│   ├── env.py               # Alembic 환경 설정
│   └── script.py.mako       # 마이그레이션 템플릿
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
├── alembic.ini              # Alembic 설정 파일
├── Dockerfile               # 런타임 이미지 (베이스 이미지 의존)
├── Dockerfile.base          # Python/시스템 패키지 사전 설치용 베이스 이미지
├── requirements.txt         # Python 패키지 의존성
└── README.md               # 프로젝트 문서
```

---

## 🔧 개발

### 데이터베이스 마이그레이션

이 프로젝트는 [Alembic](https://alembic.sqlalchemy.org/)을 사용하여 데이터베이스 스키마 버전 관리를 수행합니다.

#### 초기 마이그레이션 생성

```bash
# 가상환경 활성화 후
alembic revision --autogenerate -m "Initial migration"
```

#### 마이그레이션 적용

```bash
# 최신 마이그레이션 적용
alembic upgrade head

# 특정 리비전으로 업그레이드
alembic upgrade <revision>

# 한 단계 롤백
alembic downgrade -1

# 특정 리비전으로 롤백
alembic downgrade <revision>
```

#### 마이그레이션 상태 확인

```bash
# 현재 마이그레이션 상태 확인
alembic current

# 마이그레이션 히스토리 확인
alembic history
```

**참고**: 프로덕션 환경에서는 `init_db()` 대신 Alembic 마이그레이션을 사용하여 데이터베이스 스키마를 관리합니다.

### API 엔드포인트

- `GET /`: 기본 Hello 메시지 반환
- `GET /db-test`: 데이터베이스 연결 테스트 및 버전 정보 반환
- `GET /api-docs`: Swagger UI (개발 환경에서만 활성화)

### 환경변수

필요한 환경변수:

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `DB_HOST` | 데이터베이스 호스트 주소 | - |
| `DB_PORT` | 데이터베이스 포트 | `5432` |
| `DB_NAME` | 데이터베이스 이름 | - |
| `DB_USER` | 데이터베이스 사용자명 | - |
| `DB_PASSWORD` | 데이터베이스 비밀번호 | - |
| `GHCR_USERNAME` | (선택) GHCR 로그인용 GitHub 사용자명 (패키지가 Private일 때 필요) | Secrets |
| `GHCR_TOKEN` | (선택) GHCR PAT (read/write:packages) | Secrets |

> 📝 `GHCR_USERNAME`/`GHCR_TOKEN`을 설정하지 않으면 GitHub Actions는 `GITHUB_TOKEN`으로 push하고, 서버는 익명으로 pull을 시도합니다.  
> 이 경우 GHCR 패키지를 Public로 공개해야 합니다.

### 유틸리티 모듈

- `app/utils/common.py`: HTML 정리(`sanitize_html`, `strip_tags`), 요약(`truncate_text`), 마스킹(`mask_email`, `mask_phone`), 전화번호 정규화(`normalize_phone_number`), Cloudinary 썸네일(`to_thumb`) 등
- `app/utils/pagination.py`: `normalize_pagination`, `apply_pagination`, `build_paginated_payload`로 일관된 리스트 응답을 구성
- `app/utils/response.py`: `success_response`, `fail_response`로 성공/실패 응답 포맷을 통일

**보안 주의:** 
- `.env` 파일은 절대 Git에 커밋하지 마세요
- 모든 민감 정보는 GitHub Secrets로 관리됩니다
- 프로덕션 환경은 수동 승인 단계가 포함되어 있습니다

---

## 🚢 배포

이 프로젝트는 GitHub Actions를 사용하여 자동 배포를 수행합니다.

### 배포 프로세스

1. **Dev 환경**: `dev` 브랜치에 push하면 자동 배포
2. **Prod 환경**: `prod` 브랜치에 push하면 자동 배포 (수동 승인 가능)

### 배포 시나리오

1. 코드를 브랜치에 push
2. GitHub Actions 워크플로우 자동 실행
3. Docker 베이스 이미지(`Dockerfile.base`) 빌드 후 GHCR에 push
4. 애플리케이션 이미지(`Dockerfile`) 빌드 후 GHCR에 push
5. 대상 서버에서 GHCR Pull + `.env` 동적 생성 (GitHub Actions가 기본 `GITHUB_TOKEN`을 SSH 세션으로 전달하여 로그인)
6. 기존 컨테이너 중지/삭제 후 새 컨테이너 실행
7. 헬스체크 수행

### 배포 전 필수 작업

1. **GitHub Secrets 설정**
   - 레포지토리 Settings → Secrets and variables → Actions
   - 서버 호스트, SSH 키, 데이터베이스 정보
   - (선택) GHCR 패키지가 Private인 경우 `GHCR_USERNAME`, `GHCR_TOKEN` 추가  
     👉 Secrets를 제공하지 않으면 워크플로우가 기본 `GITHUB_TOKEN`(단일 실행 동안만 유효)을 서버로 전달해 pull을 수행합니다.

2. **서버 초기 설정**
   - Docker 및 Docker Compose 설치
   - Nginx 설치 및 설정
   - SSL 인증서 발급 (Let's Encrypt)

3. **SSH 키 설정**
   - 배포용 SSH 키 생성 및 서버에 등록

---

## 🏗️ 인프라 구조

### 환경 분리

- **개발 환경 (Dev)**: 개발 및 테스트용
- **운영 환경 (Prod)**: 프로덕션 서비스용

### 기술 스택

- **컨테이너**: Docker
- **웹 서버**: Nginx (Reverse Proxy)
- **SSL/TLS**: Let's Encrypt (Certbot)
- **CI/CD**: GitHub Actions
- **클라우드**: Oracle Cloud Infrastructure (OCI)

---

## 🔒 보안

- ✅ 모든 민감 정보는 GitHub Secrets로 관리
- ✅ `.env` 파일은 절대 Git에 커밋하지 않음
- ✅ 프로덕션 환경은 수동 승인 단계 포함
- ✅ SSH 키는 안전하게 관리
- ✅ SSL/TLS 인증서로 HTTPS 통신

---

## 🛠️ 문제 해결

### 빠른 확인 사항

- **배포 실패**: GitHub Actions 로그 확인
- **502 에러**: Docker 컨테이너 및 Nginx 상태 확인
- **DB 연결 실패**: 환경변수 및 방화벽 설정 확인

---

## 📝 라이선스

이 프로젝트는 Livbee 프로젝트의 일부입니다.

---

## 👥 기여

프로젝트에 기여하고 싶으시다면, 이슈를 생성하거나 Pull Request를 제출해주세요.
