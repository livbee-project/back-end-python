"""add qualifications column to campaigns

Revision ID: 20241207_add_qualifications_to_campaigns
Revises: 20241206_remove_product_url_live_stream_url_from_campaigns
Create Date: 2024-12-07 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20241207_add_qualifications_to_campaigns"
down_revision = "20241206_remove_product_url_live_stream_url_from_campaigns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS qualifications TEXT[]"))


def downgrade() -> None:
    op.drop_column("campaigns", "qualifications")
