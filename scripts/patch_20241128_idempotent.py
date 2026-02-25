"""
applications 컬럼 이미 있을 때 DuplicateColumn 방지:
20241128_add_application_availability_fields.py upgrade()를
ADD COLUMN IF NOT EXISTS 로 idempotent 하게 패치합니다.
실행: 프로젝트 루트에서 py scripts/patch_20241128_idempotent.py
"""
import pathlib

path = pathlib.Path(__file__).resolve().parent.parent / "alembic" / "versions" / "20241128_add_application_availability_fields.py"
text = path.read_text(encoding="utf-8")

old_upgrade = """def upgrade() -> None:
    op.add_column("applications", sa.Column("available_date", sa.Date(), nullable=True))
    op.add_column("applications", sa.Column("available_time", sa.String(), nullable=True))"""

new_upgrade = """def upgrade() -> None:
    # Dev 등에서 컬럼이 이미 있는 경우(이전 부분 적용) DuplicateColumn 방지
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE applications ADD COLUMN IF NOT EXISTS available_date DATE"))
    conn.execute(sa.text("ALTER TABLE applications ADD COLUMN IF NOT EXISTS available_time VARCHAR"))"""

if old_upgrade not in text:
    raise SystemExit("ERROR: upgrade() 블록을 찾을 수 없습니다. 파일 내용이 예상과 다릅니다.")
path.write_text(text.replace(old_upgrade, new_upgrade, 1), encoding="utf-8")
print("OK: alembic/versions/20241128_add_application_availability_fields.py idempotent 적용됨.")
