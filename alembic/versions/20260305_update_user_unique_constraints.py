"""update users unique constraints for email/role and kakao_id/role

Revision ID: 20260305_update_user_unique_constraints
Revises: 20250304_password_nullable
Create Date: 2026-03-05

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260305_update_user_unique_constraints"
down_revision = "20250304_password_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 기존 email unique 제약 제거 (컬럼 레벨 unique 또는 제약/인덱스 둘 다 고려)
    conn = op.get_bind()

    # PostgreSQL 기본 unique constraint 이름 시도
    conn.execute(sa.text("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_key"))

    # Alembic 가 생성했을 수 있는 unique 인덱스/제약도 방어적으로 제거
    conn.execute(
        sa.text(
            "DO $$ BEGIN "
            "IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_users_email') THEN "
            "ALTER TABLE users DROP CONSTRAINT uq_users_email; "
            "END IF; "
            "END $$;"
        )
    )

    # 이메일 + 역할 조합에 대한 유니크 제약 추가
    op.create_unique_constraint(
        "uq_users_email_role",
        "users",
        ["email", "role"],
    )

    # kakao_id + 역할 조합에 대한 유니크 제약 추가 (kakao_id는 NULL 허용)
    op.create_unique_constraint(
        "uq_users_kakao_id_role",
        "users",
        ["kakao_id", "role"],
    )


def downgrade() -> None:
    # kakao_id/role, email/role 유니크 제약 제거
    op.drop_constraint("uq_users_kakao_id_role", "users", type_="unique")
    op.drop_constraint("uq_users_email_role", "users", type_="unique")

    # email 단일 컬럼 유니크 제약은 필요 시 수동으로 복원
    # (기존 데이터 상태에 따라 안전하지 않을 수 있으므로 여기서는 자동으로 복구하지 않음)
