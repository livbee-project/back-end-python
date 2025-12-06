"""remove product_url and live_stream_url columns from campaigns

Revision ID: 20241206_remove_product_url_live_stream_url_from_campaigns
Revises: 20241129_add_detailed_content_to_campaigns
Create Date: 2025-12-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20241206_remove_product_url_live_stream_url_from_campaigns"
down_revision = "20241129_add_detailed_content_to_campaigns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("campaigns", "product_url")
    op.drop_column("campaigns", "live_stream_url")


def downgrade() -> None:
    op.add_column("campaigns", sa.Column("product_url", sa.String(), nullable=True))
    op.add_column("campaigns", sa.Column("live_stream_url", sa.String(), nullable=True))

