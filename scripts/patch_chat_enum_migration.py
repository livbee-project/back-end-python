"""
ENUM 중복 생성 방지: 20241125_add_chat_tables.py 의 ENUM 생성부를
PostgreSQL DO ... EXCEPTION WHEN duplicate_object 로 교체합니다.
실행: 프로젝트 루트에서 python scripts/patch_chat_enum_migration.py
"""
import pathlib

path = pathlib.Path(__file__).resolve().parent.parent / "alembic" / "versions" / "20241125_add_chat_tables.py"
text = path.read_text(encoding="utf-8")

old = """def upgrade() -> None:
    # ENUM은 먼저 checkfirst=True로 생성하고, 테이블 정의에서는 create_type=False로
    # 기존 타입만 참조해 테이블 생성 시 중복 CREATE TYPE 오류를 방지한다.
    sa.Enum("active", "closed", name="chatroomstatus").create(op.get_bind(), checkfirst=True)
    sa.Enum("text", "image", "system", name="chatmessagetype").create(op.get_bind(), checkfirst=True)
    sa.Enum("sent", "delivered", "read", name="chatmessagestatus").create(op.get_bind(), checkfirst=True)
    sa.Enum("brand", "showhost", name="chatparticipantrole").create(op.get_bind(), checkfirst=True)
"""

new = """def upgrade() -> None:
    # ENUM은 raw SQL로 "이미 있으면 무시" 처리해, Dev 등 재실행 시 DuplicateObject 방지.
    conn = op.get_bind()
    for enum_name, values in [
        ("chatroomstatus", ("active", "closed")),
        ("chatmessagetype", ("text", "image", "system")),
        ("chatmessagestatus", ("sent", "delivered", "read")),
        ("chatparticipantrole", ("brand", "showhost")),
    ]:
        vals = ", ".join(repr(v) for v in values)
        conn.execute(
            sa.text(
                f"DO $$ BEGIN CREATE TYPE {enum_name} AS ENUM ({vals}); "
                "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
            )
        )
"""

if old not in text:
    raise SystemExit("ERROR: 기존 ENUM 생성 블록을 찾을 수 없습니다. 파일이 이미 수정되었거나 내용이 다릅니다.")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("OK: alembic/versions/20241125_add_chat_tables.py 패치 적용됨.")
