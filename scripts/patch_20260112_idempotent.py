"""
models 테이블/관련 컬럼 이미 있을 때 Duplicate 방지:
20260112_create_models_table_and_update_relations.py upgrade()에서
models 테이블 존재 시 스킵하도록 패치합니다.
실행: 프로젝트 루트에서 py scripts/patch_20260112_idempotent.py
"""
import pathlib

path = pathlib.Path(__file__).resolve().parent.parent / "alembic" / "versions" / "20260112_create_models_table_and_update_relations.py"
text = path.read_text(encoding="utf-8")

old = """def upgrade() -> None:
    # models 테이블 생성
    op.create_table("""

new = """def upgrade() -> None:
    conn = op.get_bind()
    r = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = 'models'"
        )
    ).scalar()
    if r is not None:
        return

    # models 테이블 생성
    op.create_table("""

if old not in text:
    raise SystemExit("ERROR: upgrade() 블록을 찾을 수 없습니다.")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("OK: 20260112_create_models_table_and_update_relations.py idempotent 적용됨.")
