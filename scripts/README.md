# scripts/

일회성 **패치 스크립트**가 모여 있는 폴더입니다. 주로 Alembic 마이그레이션 파일을 수정해 **idempotent**(재실행 시 중복 오류 방지)하게 만드는 용도로 사용되었습니다.

## 파일 목록 및 용도

| 파일 | 용도 | 실행 여부 |
|------|------|------------|
| `patch_20241128_idempotent.py` | 해당 일자 마이그레이션 idempotent 패치 | 참고용 (이미 반영된 경우 많음) |
| `patch_20241129_idempotent.py` | 해당 일자 마이그레이션 idempotent 패치 | 참고용 |
| `patch_20241206_idempotent.py` | 해당 일자 마이그레이션 idempotent 패치 | 참고용 |
| `patch_20241207_idempotent.py` | 해당 일자 마이그레이션 idempotent 패치 | 참고용 |
| `patch_20260112_idempotent.py` | `models` 테이블 존재 시 스킵하도록 마이그레이션 패치 | 참고용 |
| `patch_chat_enum_migration.py` | 채팅 ENUM 중복 생성 방지 (20241125_add_chat_tables) | 참고용 |
| `patch_chat_enum_use_postgresql_enum.py` | 채팅 ENUM을 PostgreSQL DO ... EXCEPTION 방식으로 교체 | 참고용 |
| `patch_chat_tables_idempotent.py` | 채팅 테이블 마이그레이션 idempotent 패치 | 참고용 |

## 사용 시 주의

- **재실행 가능 여부:** 각 스크립트는 대상 마이그레이션 파일을 **덮어쓰는** 방식입니다. 이미 패치가 적용된 버전 파일에 다시 실행하면 불필요한 중복 수정이 될 수 있습니다.
- **실행 방법:** 프로젝트 루트에서 `python scripts/<파일명>` 으로 실행합니다. 스크립트 내 docstring에 적힌 대상 파일 경로가 현재 `alembic/versions/` 구조와 일치하는지 확인한 뒤 실행하세요.
- **권장:** 새 환경에서 마이그레이션을 처음 적용하는 경우에는 보통 Alembic 버전 파일이 이미 패치 반영된 상태로 관리되므로, 이 스크립트들은 **과거에 어떻게 idempotent 처리를 했는지 참고용**으로만 두고, 필요 시 동일한 로직을 새 마이그레이션에 직접 적용하는 것을 권장합니다.
