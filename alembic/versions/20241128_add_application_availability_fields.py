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
    op.add_column("applications", sa.Column("available_date", sa.Date(), nullable=True))
    op.add_column("applications", sa.Column("available_time", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("applications", "available_time")
    op.drop_column("applications", "available_date")

