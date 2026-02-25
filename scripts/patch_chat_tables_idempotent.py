"""
채팅 테이블 이미 있을 때 DuplicateTable 방지:
20241125_add_chat_tables.py upgrade()에서 chat_rooms 존재 시 스킵하도록 패치합니다.
실행: 프로젝트 루트에서 python scripts/patch_chat_tables_idempotent.py
"""
import pathlib

path = pathlib.Path(__file__).resolve().parent.parent / "alembic" / "versions" / "20241125_add_chat_tables.py"
text = path.read_text(encoding="utf-8")

# ENUM 블록 직후, chat_room_status_enum 정의 직전에 "테이블 있으면 스킵" 삽입
old = """            )
        )

    chat_room_status_enum = postgresql.ENUM("active", "closed", name="chatroomstatus", create_type=False)"""

new = """            )
        )

    # Dev 등에서 테이블이 이미 있는 경우(이전 부분 적용·수동 생성) DuplicateTable 방지
    r = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = 'chat_rooms'"
        )
    ).scalar()
    if r is not None:
        return

    chat_room_status_enum = postgresql.ENUM("active", "closed", name="chatroomstatus", create_type=False)"""

if old not in text:
    raise SystemExit("ERROR: 삽입 위치를 찾을 수 없습니다. 파일 내용이 예상과 다릅니다.")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("OK: alembic/versions/20241125_add_chat_tables.py 에 테이블 idempotent 스킵 로직 적용됨.")
