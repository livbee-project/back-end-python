"""make users.password nullable (카카오 전용 가입 시 비밀번호 생략)

Revision ID: 20250304_password_nullable
Revises: 20250303_add_kakao_id_to_users
Create Date: 2025-03-04

"""

from alembic import op
import sqlalchemy as sa


revision = "20250304_password_nullable"
down_revision = "20250303_add_kakao_id_to_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "password",
        existing_type=sa.String(),
        nullable=True,
    )


def downgrade() -> None:
    # 기존에 password가 NULL인 행이 있으면 downgrade 실패할 수 있음
    op.alter_column(
        "users",
        "password",
        existing_type=sa.String(),
        nullable=False,
    )
