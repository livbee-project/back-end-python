"""add detailed_content column to campaigns

Revision ID: 20241129_add_detailed_content_to_campaigns
Revises: 20241128_add_application_availability_fields
Create Date: 2025-11-29 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20241129_add_detailed_content_to_campaigns"
down_revision = "20241128_add_application_availability_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS detailed_content VARCHAR"))


def downgrade() -> None:
    op.drop_column("campaigns", "detailed_content")
