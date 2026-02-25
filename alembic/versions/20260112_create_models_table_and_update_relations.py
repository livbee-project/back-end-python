"""create models table and update relations

Revision ID: 20260112_create_models_table_and_update_relations
Revises: 20241207_add_qualifications_to_campaigns
Create Date: 2026-01-12 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260112_create_models_table_and_update_relations"
down_revision = "20241207_add_qualifications_to_campaigns"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
    op.create_table(
        "models",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("nickname", sa.String(), nullable=True),
        sa.Column("one_line_intro", sa.String(), nullable=True),
        sa.Column("detailed_intro", sa.String(), nullable=True),
        sa.Column("experience_years", sa.Integer(), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("main_thumbnail_url", sa.String(), nullable=True),
        sa.Column("background_image_url", sa.String(), nullable=True),
        sa.Column("sub_thumbnail_urls", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("status", sa.String(), nullable=True, server_default="published"),
        sa.Column("is_age_public", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column("is_sizing_public", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column("detailed_region", sa.String(), nullable=True),
        sa.Column("gender", sa.String(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("weight", sa.Integer(), nullable=True),
        sa.Column("top_size", sa.String(), nullable=True),
        sa.Column("bottom_size", sa.String(), nullable=True),
        sa.Column("shoe_size", sa.Integer(), nullable=True),
        sa.Column("website_url", sa.String(), nullable=True),
        sa.Column("instagram_url", sa.String(), nullable=True),
        sa.Column("youtube_url", sa.String(), nullable=True),
        sa.Column("tiktok_url", sa.String(), nullable=True),
        sa.Column("contact", sa.String(), nullable=True),
        sa.Column("open_chat", sa.String(), nullable=True),
        sa.Column("registration_type", sa.String(), nullable=True),
        sa.Column("public_scope", sa.String(), nullable=True, server_default="전체공개"),
        sa.Column("is_receiving_offers", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column("attached_file_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_models_user_id"), "models", ["user_id"], unique=False)

    # proposals 테이블에 target_model_id 추가
    op.add_column("proposals", sa.Column("target_model_id", sa.String(), nullable=True))
    op.create_index(op.f("ix_proposals_target_model_id"), "proposals", ["target_model_id"], unique=False)
    op.create_foreign_key(
        "fk_proposals_target_model_id",
        "proposals",
        "models",
        ["target_model_id"],
        ["id"],
        ondelete="CASCADE"
    )
    
    # proposals 테이블의 target_portfolio_id를 nullable로 변경
    op.alter_column("proposals", "target_portfolio_id", nullable=True)

    # applications 테이블에 portfolio_id, model_id 추가
    op.add_column("applications", sa.Column("portfolio_id", sa.String(), nullable=True))
    op.add_column("applications", sa.Column("model_id", sa.String(), nullable=True))
    op.create_index(op.f("ix_applications_portfolio_id"), "applications", ["portfolio_id"], unique=False)
    op.create_index(op.f("ix_applications_model_id"), "applications", ["model_id"], unique=False)
    op.create_foreign_key(
        "fk_applications_portfolio_id",
        "applications",
        "portfolios",
        ["portfolio_id"],
        ["id"],
        ondelete="SET NULL"
    )
    op.create_foreign_key(
        "fk_applications_model_id",
        "applications",
        "models",
        ["model_id"],
        ["id"],
        ondelete="SET NULL"
    )


def downgrade() -> None:
    # applications 테이블의 외래키 및 컬럼 제거
    op.drop_constraint("fk_applications_model_id", "applications", type_="foreignkey")
    op.drop_constraint("fk_applications_portfolio_id", "applications", type_="foreignkey")
    op.drop_index(op.f("ix_applications_model_id"), table_name="applications")
    op.drop_index(op.f("ix_applications_portfolio_id"), table_name="applications")
    op.drop_column("applications", "model_id")
    op.drop_column("applications", "portfolio_id")

    # proposals 테이블의 target_portfolio_id를 다시 NOT NULL로 변경
    op.alter_column("proposals", "target_portfolio_id", nullable=False)
    
    # proposals 테이블의 target_model_id 제거
    op.drop_constraint("fk_proposals_target_model_id", "proposals", type_="foreignkey")
    op.drop_index(op.f("ix_proposals_target_model_id"), table_name="proposals")
    op.drop_column("proposals", "target_model_id")

    # models 테이블 제거
    op.drop_index(op.f("ix_models_user_id"), table_name="models")
    op.drop_table("models")
