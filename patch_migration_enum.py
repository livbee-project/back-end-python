# One-off script: patch 20241125_add_chat_tables.py for idempotent ENUM creation
import pathlib

path = pathlib.Path("alembic/versions/20241125_add_chat_tables.py")
text = path.read_text(encoding="utf-8")

old = '''def upgrade() -> None:
    # ENUM은 먼저 checkfirst=True로 생성하고, 테이블 정의에서는 create_type=False로
    # 기존 타입만 참조해 테이블 생성 시 중복 CREATE TYPE 오류를 방지한다.
    sa.Enum("active", "closed", name="chatroomstatus").create(op.get_bind(), checkfirst=True)
    sa.Enum("text", "image", "system", name="chatmessagetype").create(op.get_bind(), checkfirst=True)
    sa.Enum("sent", "delivered", "read", name="chatmessagestatus").create(op.get_bind(), checkfirst=True)
    sa.Enum("brand", "showhost", name="chatparticipantrole").create(op.get_bind(), checkfirst=True)
'''

new = '''def upgrade() -> None:
    # PostgreSQL: ENUM은 "이미 있으면 무시"하는 raw SQL로 생성해, 재실행/부분 적용 시에도
    # DuplicateObject를 방지한다. 테이블 정의에서는 create_type=False로 기존 타입만 참조.
    conn = op.get_bind()
    for name, values in [
        ("chatroomstatus", ("active", "closed")),
        ("chatmessagetype", ("text", "image", "system")),
        ("chatmessagestatus", ("sent", "delivered", "read")),
        ("chatparticipantrole", ("brand", "showhost")),
    ]:
        vals = ", ".join(repr(v) for v in values)
        conn.execute(
            sa.text(
                f"DO $$ BEGIN CREATE TYPE {name} AS ENUM ({vals}); "
                "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
            )
        )
'''

if old not in text:
    print("Old block not found (maybe already patched or different line endings)")
    raise SystemExit(1)

path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Patched alembic/versions/20241125_add_chat_tables.py")
