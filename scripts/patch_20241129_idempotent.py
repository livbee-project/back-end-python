"""
campaigns.detailed_content 이미 있을 때 DuplicateColumn 방지.
실행: 프로젝트 루트에서 py scripts/patch_20241129_idempotent.py
"""
import pathlib

path = pathlib.Path(__file__).resolve().parent.parent / "alembic" / "versions" / "20241129_add_detailed_content_to_campaigns.py"
text = path.read_text(encoding="utf-8")

old = 'def upgrade() -> None:\n    op.add_column("campaigns", sa.Column("detailed_content", sa.String(), nullable=True))'
new = """def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS detailed_content VARCHAR"))"""

if old not in text:
    raise SystemExit("ERROR: upgrade() 블록을 찾을 수 없습니다.")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("OK: 20241129_add_detailed_content_to_campaigns.py idempotent 적용됨.")
