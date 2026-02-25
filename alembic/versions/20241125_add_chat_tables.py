"""채팅 테이블 생성

Revision ID: 20241125_add_chat_tables
Revises: None
Create Date: 2024-11-25
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20241125_add_chat_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ENUM은 먼저 checkfirst=True로 생성하고, 테이블 정의에서는 create_type=False로
    # 기존 타입만 참조해 테이블 생성 시 중복 CREATE TYPE 오류를 방지한다.
    sa.Enum("active", "closed", name="chatroomstatus").create(op.get_bind(), checkfirst=True)
    sa.Enum("text", "image", "system", name="chatmessagetype").create(op.get_bind(), checkfirst=True)
    sa.Enum("sent", "delivered", "read", name="chatmessagestatus").create(op.get_bind(), checkfirst=True)
    sa.Enum("brand", "showhost", name="chatparticipantrole").create(op.get_bind(), checkfirst=True)

    chat_room_status_enum = sa.Enum("active", "closed", name="chatroomstatus", create_type=False)
    chat_message_type_enum = sa.Enum("text", "image", "system", name="chatmessagetype", create_type=False)
    chat_message_status_enum = sa.Enum("sent", "delivered", "read", name="chatmessagestatus", create_type=False)
    chat_participant_role_enum = sa.Enum("brand", "showhost", name="chatparticipantrole", create_type=False)

    op.create_table(
        "chat_rooms",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("campaign_id", sa.String(length=36), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("brand_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("showhost_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", sa.String(length=36), sa.ForeignKey("applications.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", chat_room_status_enum, nullable=False, server_default="active"),
        sa.Column("last_message_id", sa.String(length=36), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("campaign_id", "brand_user_id", "showhost_user_id", name="uq_chat_room_campaign_pair"),
    )
    op.create_index("ix_chat_rooms_campaign_id", "chat_rooms", ["campaign_id"])
    op.create_index("ix_chat_rooms_brand_user_id", "chat_rooms", ["brand_user_id"])
    op.create_index("ix_chat_rooms_showhost_user_id", "chat_rooms", ["showhost_user_id"])
    op.create_index("ix_chat_rooms_application_id", "chat_rooms", ["application_id"])
    op.create_index("ix_chat_rooms_last_message_at", "chat_rooms", ["last_message_at"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("room_id", sa.String(length=36), sa.ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("message_type", chat_message_type_enum, nullable=False, server_default="text"),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column("status", chat_message_status_enum, nullable=False, server_default="sent"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_chat_messages_room_id", "chat_messages", ["room_id"])
    op.create_index("ix_chat_messages_room_created_at", "chat_messages", ["room_id", "created_at"])
    op.create_index("ix_chat_messages_sender_id", "chat_messages", ["sender_id"])

    op.create_table(
        "chat_participants",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("room_id", sa.String(length=36), sa.ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", chat_participant_role_enum, nullable=False),
        sa.Column("last_read_message_id", sa.String(length=36), nullable=True),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("room_id", "user_id", name="uq_chat_participant_room_user"),
    )
    op.create_index("ix_chat_participants_room_id", "chat_participants", ["room_id"])
    op.create_index("ix_chat_participants_user_id", "chat_participants", ["user_id"])
    op.create_index("ix_chat_participants_user_role", "chat_participants", ["user_id", "role"])

    op.create_foreign_key(
        "fk_chat_rooms_last_message",
        "chat_rooms",
        "chat_messages",
        ["last_message_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_chat_participants_last_read_message",
        "chat_participants",
        "chat_messages",
        ["last_read_message_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_chat_participants_last_read_message", "chat_participants", type_="foreignkey")
    op.drop_constraint("fk_chat_rooms_last_message", "chat_rooms", type_="foreignkey")

    op.drop_index("ix_chat_participants_user_role", table_name="chat_participants")
    op.drop_index("ix_chat_participants_user_id", table_name="chat_participants")
    op.drop_index("ix_chat_participants_room_id", table_name="chat_participants")
    op.drop_table("chat_participants")

    op.drop_index("ix_chat_messages_sender_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_room_created_at", table_name="chat_messages")
    op.drop_index("ix_chat_messages_room_id", table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index("ix_chat_rooms_last_message_at", table_name="chat_rooms")
    op.drop_index("ix_chat_rooms_application_id", table_name="chat_rooms")
    op.drop_index("ix_chat_rooms_showhost_user_id", table_name="chat_rooms")
    op.drop_index("ix_chat_rooms_brand_user_id", table_name="chat_rooms")
    op.drop_index("ix_chat_rooms_campaign_id", table_name="chat_rooms")
    op.drop_table("chat_rooms")

    sa.Enum(name="chatparticipantrole").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="chatmessagestatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="chatmessagetype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="chatroomstatus").drop(op.get_bind(), checkfirst=True)

