"""notifications table and activity reminder flag

Revision ID: 004
Revises: 003
Create Date: 2026-03-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "activities",
        sa.Column("reminder_5m_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "lead_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("leads.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reference_type", sa.String(32), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_user_created", "notifications", ["user_id", "created_at"])
    op.create_index(
        "ix_notifications_user_unread",
        "notifications",
        ["user_id", "read_at"],
    )
    op.create_unique_constraint(
        "uq_notifications_ref_type",
        "notifications",
        ["reference_type", "reference_id", "type"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_notifications_ref_type", "notifications", type_="unique")
    op.drop_index("ix_notifications_user_unread", table_name="notifications")
    op.drop_index("ix_notifications_user_created", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_column("activities", "reminder_5m_sent_at")
