"""
20241125_add_chat_tables.py 에서 ENUM 컬럼 타입을
sqlalchemy.dialects.postgresql.ENUM 로 명시해 create_type=False 가
DDL 단계에서 확실히 적용되도록 합니다.
(이미 DO ... EXCEPTION 블록이 있어도, create_table 시 dialect 가
CREATE TYPE 를 다시 호출하는 경우 대비)
실행: 프로젝트 루트에서 py scripts/patch_chat_enum_use_postgresql_enum.py
"""
import pathlib

path = pathlib.Path(__file__).resolve().parent.parent / "alembic" / "versions" / "20241125_add_chat_tables.py"
text = path.read_text(encoding="utf-8")

# import 추가 (sa 다음 줄에 postgresql ENUM import)
old_import = "from alembic import op\nimport sqlalchemy as sa"
new_import = "from alembic import op\nimport sqlalchemy as sa\nfrom sqlalchemy.dialects import postgresql"
if "from sqlalchemy.dialects import postgresql" not in text:
    text = text.replace(old_import, new_import, 1)
else:
    old_import = new_import  # 이미 있으면 아래 replace 스킵

# sa.Enum(..., create_type=False) -> postgresql.ENUM(..., create_type=False)
replacements = [
    (
        'chat_room_status_enum = sa.Enum("active", "closed", name="chatroomstatus", create_type=False)',
        'chat_room_status_enum = postgresql.ENUM("active", "closed", name="chatroomstatus", create_type=False)',
    ),
    (
        'chat_message_type_enum = sa.Enum("text", "image", "system", name="chatmessagetype", create_type=False)',
        'chat_message_type_enum = postgresql.ENUM("text", "image", "system", name="chatmessagetype", create_type=False)',
    ),
    (
        'chat_message_status_enum = sa.Enum("sent", "delivered", "read", name="chatmessagestatus", create_type=False)',
        'chat_message_status_enum = postgresql.ENUM("sent", "delivered", "read", name="chatmessagestatus", create_type=False)',
    ),
    (
        'chat_participant_role_enum = sa.Enum("brand", "showhost", name="chatparticipantrole", create_type=False)',
        'chat_participant_role_enum = postgresql.ENUM("brand", "showhost", name="chatparticipantrole", create_type=False)',
    ),
]

for old_line, new_line in replacements:
    if old_line in text:
        text = text.replace(old_line, new_line, 1)

# downgrade 쪽 drop 시 sa.Enum -> postgresql.ENUM (name만 쓰는 경우)
old_drop = 'sa.Enum(name="chatroomstatus").drop(op.get_bind(), checkfirst=True)'
if old_drop in text:
    text = text.replace(
        old_drop,
        'postgresql.ENUM(name="chatroomstatus").drop(op.get_bind(), checkfirst=True)',
        1,
    )
for enum_name in ("chatmessagetype", "chatmessagestatus", "chatparticipantrole"):
    old_d = f'sa.Enum(name="{enum_name}").drop(op.get_bind(), checkfirst=True)'
    if old_d in text:
        text = text.replace(old_d, f'postgresql.ENUM(name="{enum_name}").drop(op.get_bind(), checkfirst=True)', 1)

path.write_text(text, encoding="utf-8")
print("OK: 20241125_add_chat_tables.py 에 postgresql.ENUM 반영됨.")
