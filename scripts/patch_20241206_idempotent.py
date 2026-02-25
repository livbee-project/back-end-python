"""
컬럼이 이미 없을 때 drop_column 오류 방지.
실행: 프로젝트 루트에서 py scripts/patch_20241206_idempotent.py
"""
import pathlib

path = pathlib.Path(__file__).resolve().parent.parent / "alembic" / "versions" / "20241206_remove_product_url_live_stream_url_from_campaigns.py"
text = path.read_text(encoding="utf-8")

old = """def upgrade() -> None:
    op.drop_column("campaigns", "product_url")
    op.drop_column("campaigns", "live_stream_url")"""

new = """def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE campaigns DROP COLUMN IF EXISTS product_url"))
    conn.execute(sa.text("ALTER TABLE campaigns DROP COLUMN IF EXISTS live_stream_url"))"""

if old not in text:
    raise SystemExit("ERROR: upgrade() 블록을 찾을 수 없습니다.")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("OK: 20241206_remove_product_url_live_stream_url_from_campaigns.py idempotent 적용됨.")
