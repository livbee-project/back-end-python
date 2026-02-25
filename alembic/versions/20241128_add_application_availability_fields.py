"""add available date/time columns to applications

Revision ID: 20241128_add_application_availability_fields
Revises: 20241125_add_chat_tables
Create Date: 2025-11-28 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20241128_add_application_availability_fields"
down_revision = "20241125_add_chat_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Dev 등에서 컬럼이 이미 있는 경우(이전 부분 적용) DuplicateColumn 방지
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE applications ADD COLUMN IF NOT EXISTS available_date DATE"))
    conn.execute(sa.text("ALTER TABLE applications ADD COLUMN IF NOT EXISTS available_time VARCHAR"))


def downgrade() -> None:
    op.drop_column("applications", "available_time")
    op.drop_column("applications", "available_date")

