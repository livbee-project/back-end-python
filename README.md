# Livbee Backend API!

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
   git clone https://github.com/livbee-project/porject-livbee-back.git
   cd porject-livbee-back
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

7. **코드 품질 도구 설정** (선택사항)
   ```bash
   # pre-commit 훅 설치
   pre-commit install

   # 코드 포맷팅
   black app tests

   # 타입 체크
   mypy app

   # 린팅
   ruff check app tests
   ```

8. **API 테스트**
   - 기본 엔드포인트: http://localhost:8000/
   - DB 연결 테스트: http://localhost:8000/db-test
   - API 문서: http://localhost:8000/api-docs (Swagger UI)

#### Swagger UI 사용 방법

**접속 URL:**
- 로컬 개발: http://localhost:8000/api-docs
- Dev 환경: https://dev-api.livbee.co.kr/api-docs
- Prod 환경: https://api.livbee.co.kr/api-docs

**사용 방법:**
1. **API 문서 접속**: 위 URL 중 하나로 접속
2. **인증 설정**:
   - 우측 상단의 "Authorize" 버튼 클릭
   - `Bearer {token}` 형식으로 JWT 토큰 입력 (또는 토큰만 입력)
   - 로그인 API(`POST /api/v1/users/login`)에서 받은 토큰 사용
3. **API 테스트**: 각 엔드포인트에서 "Try it out" 버튼을 클릭하여 직접 테스트 가능

---

---

## 📁 프로젝트 구조

```
back-end-python/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 메인 애플리케이션
│   ├── core/                # 핵심 설정 (config, database, security, logging)
│   ├── models/              # SQLAlchemy 모델
│   ├── routes/              # API 라우터 (요청/응답 처리)
│   ├── services/            # 비즈니스 로직 서비스 레이어
│   ├── middleware/          # 인증/권한 미들웨어
│   └── utils/               # 유틸리티 함수
├── tests/                   # 테스트 코드
│   ├── conftest.py          # pytest 설정 및 픽스처
│   ├── test_*_service.py    # 서비스 레이어 단위 테스트
│   └── test_api_*.py        # API 엔드포인트 통합 테스트
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
├── pyproject.toml           # 프로젝트 설정, pytest 설정은 여기 있음 (pytest.ini 없음)
├── Dockerfile               # 런타임 이미지 (베이스 이미지 의존)
├── Dockerfile.base          # Python/시스템 패키지 사전 설치용 베이스 이미지
├── requirements.txt         # Python 패키지 의존성
└── README.md               # 프로젝트 문서
```

### 아키텍처 개요

이 프로젝트는 **서비스 레이어 아키텍처**를 따릅니다:

- **Routes Layer** (`app/routes/`): HTTP 요청/응답 처리, 입력 검증
- **Service Layer** (`app/services/`): 비즈니스 로직, 데이터베이스 조작
- **Model Layer** (`app/models/`): SQLAlchemy ORM 모델
- **Utils Layer** (`app/utils/`): 공통 유틸리티 함수

이 구조를 통해 비즈니스 로직과 프레젠테이션 로직을 분리하여 코드 재사용성과 테스트 용이성을 높였습니다.

#### 서비스 레이어 사용 예시

```python
# ❌ 나쁜 예: 라우트에서 직접 비즈니스 로직 처리
@router.post("/applications")
async def create_application(request: ApplicationCreate, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == request.campaign_id).first()
    if not campaign:
        return fail_response("NOT_FOUND", 404)
    # ... 복잡한 비즈니스 로직 ...

# ✅ 좋은 예: 서비스 레이어 사용
@router.post("/applications")
async def create_application(request: ApplicationCreate, db: Session = Depends(get_db)):
    application = create_application_service(db, request.campaign_id, user_id)
    return success_response({"data": application})
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

### 테스트

이 프로젝트는 `pytest`를 사용하여 테스트를 작성합니다.

#### 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 테스트 파일 실행
pytest tests/test_user_service.py

# 커버리지 포함 실행
pytest --cov=app --cov-report=html

# 커버리지 리포트 확인
# HTML 리포트: htmlcov/index.html
# 터미널 리포트: pytest 실행 시 자동 표시

# 특정 테스트 함수만 실행
pytest tests/test_user_service.py::test_create_user_success

# 커버리지 목표: 70% 이상 (pyproject.toml에 설정됨)
```

#### 테스트 구조

- **단위 테스트** (`test_*_service.py`): 서비스 레이어의 비즈니스 로직 테스트
- **통합 테스트** (`test_api_*.py`): API 엔드포인트 통합 테스트

테스트는 인메모리 SQLite 데이터베이스를 사용하여 실제 데이터베이스에 영향을 주지 않습니다. 테스트는 로컬 또는 CI에서만 실행하며, 배포용 Docker 이미지에는 테스트 코드가 포함되지 않습니다.

### 코드 품질

#### 코드 포맷팅

```bash
# Black으로 코드 포맷팅
black app tests

# 포맷팅 확인만 (변경하지 않음)
black --check app tests
```

#### 타입 체크

```bash
# mypy로 타입 체크
mypy app
```

#### 린팅

```bash
# ruff로 린팅
ruff check app tests

# 자동 수정
ruff check --fix app tests
```

#### Pre-commit 훅

커밋 전 자동으로 코드 품질 검사를 수행하려면:

```bash
# pre-commit 훅 설치
pre-commit install

# 수동 실행
pre-commit run --all-files
```

설치 후 커밋 시 자동으로 다음 검사가 수행됩니다:
- 코드 포맷팅 (Black, app/tests)
- 린팅 (Ruff, app/tests)
- 타입 체크 (mypy, app만)
- 기타 파일 검증 (trailing whitespace, end-of-file, YAML, JSON, TOML 등)

설정 파일: `.pre-commit-config.yaml` (pyproject.toml의 [tool.black], [tool.ruff], [tool.mypy]와 연동)

### API 엔드포인트

모든 API 엔드포인트는 `/api/v1` prefix를 사용합니다.

#### 기본 엔드포인트

- `GET /`: 기본 Hello 메시지 반환
- `GET /healthz`: 헬스체크 (liveness probe)
- `GET /readyz`: 준비 상태 체크 (readiness probe, DB 연결 확인)
- `GET /db-test`: 데이터베이스 연결 테스트 및 버전 정보 반환
- `GET /api-docs`: Swagger UI (모든 환경에서 활성화)

#### 사용자 인증 (`/api/v1/users`)

- `POST /api/v1/users/signup`: 회원가입 (brand/showhost)
- `POST /api/v1/users/login`: 로그인 (JWT 토큰 발급)
- `GET /api/v1/users/me`: 현재 사용자 정보 조회 (인증 필요)

#### 포트폴리오 관리 (`/api/v1/portfolios`)

- `GET /api/v1/portfolios/my/list`: 내 포트폴리오 목록 조회 (showhost, 인증 필요)
- `POST /api/v1/portfolios`: 새 포트폴리오 생성 (showhost, 인증 필요)
- `PUT /api/v1/portfolios/{portfolio_id}`: 포트폴리오 수정 (showhost, 인증 필요)
- `DELETE /api/v1/portfolios/{portfolio_id}`: 포트폴리오 삭제 (showhost, 인증 필요)
- `GET /api/v1/portfolios`: 전체 포트폴리오 목록 조회 (페이지네이션)
- `GET /api/v1/portfolios/{portfolio_id}`: 특정 포트폴리오 상세 조회

#### 모델 관리 (`/api/v1/models`)

- `GET /api/v1/models`: 모델 목록 조회 (페이지네이션, published 상태만)
- `GET /api/v1/models/{model_id}`: 특정 모델 상세 조회
- `POST /api/v1/models`: 새 모델 등록 (showhost, 인증 필요, 포트폴리오와 동일한 데이터)
- `PUT /api/v1/models/{model_id}`: 모델 정보 수정 (showhost, 인증 필요)
- `DELETE /api/v1/models/{model_id}`: 모델 삭제 (showhost, 인증 필요)

> **참고**: `/models` 엔드포인트는 `/portfolios`와 동일한 데이터를 사용하며, 프론트엔드 호환성을 위해 제공됩니다.

#### 캠페인/공고 관리 (`/api/v1/campaigns`)

- `GET /api/v1/campaigns/meta`: 캠페인 메타데이터 조회 (카테고리, 브랜드 목록)
- `POST /api/v1/campaigns`: 새 캠페인 생성 (brand/admin, 인증 필요)
- `GET /api/v1/campaigns`: 전체 캠페인 목록 조회 (검색, 필터링, 페이지네이션)
- `GET /api/v1/campaigns/mine`: 내가 생성한 캠페인 목록 (brand, 인증 필요)
- `GET /api/v1/campaigns/{campaign_id}`: 특정 캠페인 상세 조회
- `PUT /api/v1/campaigns/{campaign_id}`: 캠페인 수정 (brand/admin, 인증 필요)
- `DELETE /api/v1/campaigns/{campaign_id}`: 캠페인 삭제 (brand/admin, 인증 필요)

#### 지원서 관리 (`/api/v1/applications`)

- `GET /api/v1/applications/mine`: 내 지원서 목록 조회 (인증 필요)
- `POST /api/v1/applications`: 새 지원서 생성 (인증 필요, 응답에 `chatRoomId` 포함)
- `GET /api/v1/applications`: 전체 지원서 목록 조회 (brand, 인증 필요, 페이지네이션)
- `PATCH /api/v1/applications/{application_id}`: 지원서 상태 업데이트 (brand, 인증 필요)

> **캠페인 지원 연계**: 지원이 완료되면 자동으로 `chatRoomId`가 생성/재사용되어 응답으로 전달됩니다. 프론트에서 해당 ID로 바로 채팅 화면을 열 수 있습니다.

#### 채팅 (`/api/v1/chat`)

- `GET /api/v1/chat/rooms`: 내가 참여한 채팅방 목록 (최근 메시지 + 미확인 메시지 수 포함)
- `GET /api/v1/chat/rooms/{room_id}`: 채팅방 메시지 히스토리 (페이지네이션)
- `POST /api/v1/chat/rooms`: 캠페인/참가자 조합으로 채팅방 생성 또는 재사용
- `POST /api/v1/chat/rooms/{room_id}/messages`: 메시지 전송
- `POST /api/v1/chat/rooms/{room_id}/read`: 읽음 처리 (`last_read_message_id` 갱신)
- `WebSocket /api/v1/chat/{room_id}`: JWT 인증 후 참여자만 실시간 메시지/읽음 이벤트 수신

모든 응답은 기존 API와 동일하게 `success_response`/`fail_response` 포맷을 사용하며, JWT 토큰의 역할(role)이 `brand` 또는 `showhost`인 사용자만 접근할 수 있습니다.

##### WebSocket 연결 가이드

- **엔드포인트**: `wss://{호스트}/api/v1/chat/{room_id}`
- **인증 방법**: 쿼리스트링 `?token=<JWT>` 또는 헤더 `Authorization: Bearer <JWT>`
- **메시지 예시**
  ```json
  {
    "type": "message.new",
    "payload": {
      "id": "msg-id",
      "roomId": "room-id",
      "content": "안녕하세요!",
      "messageType": "text",
      "sender": { "id": "user-id", "role": "showhost", "name": "홍길동" },
      "createdAt": "2025-11-25T12:34:56.000Z"
    }
  }
  ```
- **읽음 이벤트**
  ```json
  {
    "type": "message.read",
    "payload": {
      "roomId": "room-id",
      "userId": "brand-user-id",
      "lastReadMessageId": "msg-id",
      "lastReadAt": "2025-11-25T12:40:00.000Z"
    }
  }
  ```

> WebSocket에서 `{"type": "ping"}`을 전송하면 서버가 `{"type": "pong"}`으로 응답하여 연결 상태를 확인할 수 있습니다.

#### 제안 관리 (`/api/v1/proposals`)

- `POST /api/v1/proposals`: 새 제안 생성 (brand, 인증 필요)
- `GET /api/v1/proposals/sent`: 내가 보낸 제안 목록 (brand, 인증 필요)
- `GET /api/v1/proposals/received`: 내가 받은 제안 목록 (showhost, 인증 필요)
- `PATCH /api/v1/proposals/{proposal_id}/withdraw`: 제안 철회 (brand, 인증 필요)

#### 뉴스/공지사항 관리 (`/api/v1/news`)

- `GET /api/v1/news`: 전체 뉴스 목록 조회 (페이지네이션)
- `GET /api/v1/news/{news_id}`: 특정 뉴스 상세 조회
- `POST /api/v1/news`: 새 뉴스 생성 (showhost, 인증 필요)
- `PUT /api/v1/news/{news_id}`: 뉴스 수정 (showhost, 인증 필요)
- `DELETE /api/v1/news/{news_id}`: 뉴스 삭제 (showhost, 인증 필요)

#### 스튜디오 관리 (`/api/v1/studios`)

- `POST /api/v1/studios`: 새 스튜디오 정보 생성
- `PUT /api/v1/studios/{studio_id}`: 스튜디오 정보 수정
- `GET /api/v1/studios/{studio_id}`: 특정 스튜디오 정보 조회

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

**배포 방식**
- **자동 배포**: `dev`/`prod` 브랜치 push 시 GitHub Actions가 대상 서버에 SSH 접속 후 `docker run`으로 컨테이너를 실행합니다.
- **수동/로컬 배포**: `deploy/deploy.sh`와 `deploy/docker-compose.yml`을 사용합니다.

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
7. 컨테이너 내부에서 `alembic upgrade head`로 DB 마이그레이션 자동 실행
8. 헬스체크 수행

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

### 한글 깨짐 (커밋 메시지 / git log)

**원인**
Windows에서 Git이 커밋 메시지나 로그 출력에 기본 인코딩(CP949 등)을 쓰거나, 셸이 UTF-8이 아니면 한글이 깨질 수 있습니다.

**해결 및 사전 작업**
이 저장소에는 이미 아래 설정이 로컬(`.git/config`)에 적용되어 있습니다.

- `i18n.commitEncoding=utf-8` — 커밋 메시지를 UTF-8로 해석
- `i18n.logOutputEncoding=utf-8` — `git log` 등 출력을 UTF-8로
- `core.quotepath=false` — 한글 파일명을 이스케이프하지 않고 표시

다른 PC에서 클론한 경우, 프로젝트 루트에서 한 번만 실행하면 됩니다.

```bash
git config i18n.commitEncoding utf-8
git config i18n.logOutputEncoding utf-8
git config core.quotepath false
```

PowerShell에서 커밋/푸시할 때 한글이 깨지면, 명령 실행 전에 UTF-8을 지정한 뒤 진행하세요.

```powershell
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

---

## 📝 라이선스

이 프로젝트는 Livbee 프로젝트의 일부입니다.

---

## 👥 기여

프로젝트에 기여하고 싶으시다면, 이슈를 생성하거나 Pull Request를 제출해주세요.
