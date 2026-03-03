"""add kakao_id to users

Revision ID: 20250303_add_kakao_id_to_users
Revises: 20260112_create_models_table_and_update_relations
Create Date: 2025-03-03

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250303_add_kakao_id_to_users"
down_revision = "20260112_create_models_table_and_update_relations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("kakao_id", sa.String(), nullable=True))
    op.create_index(op.f("ix_users_kakao_id"), "users", ["kakao_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_kakao_id"), table_name="users")
    op.drop_column("users", "kakao_id")
