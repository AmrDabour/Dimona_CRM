"""Manager recurring tasks + activity bonus points

Revision ID: 008
Revises: 007
Create Date: 2026-03-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "manager_task_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("assignee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "assigned_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=True),
        sa.Column("activity_type", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task_points", sa.Integer(), server_default="0", nullable=False),
        sa.Column("weekdays", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("schedule_hour_utc", sa.Integer(), server_default="9", nullable=False),
        sa.Column("schedule_minute_utc", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("last_fired_on", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_manager_task_schedules_assignee_id", "manager_task_schedules", ["assignee_id"])
    op.create_index("ix_manager_task_schedules_assigned_by_id", "manager_task_schedules", ["assigned_by_id"])
    op.create_index("ix_manager_task_schedules_lead_id", "manager_task_schedules", ["lead_id"])

    op.add_column(
        "activities",
        sa.Column("manager_schedule_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "activities",
        sa.Column("task_bonus_points", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_foreign_key(
        "fk_activities_manager_schedule_id",
        "activities",
        "manager_task_schedules",
        ["manager_schedule_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_activities_manager_schedule_id", "activities", ["manager_schedule_id"])


def downgrade() -> None:
    op.drop_index("ix_activities_manager_schedule_id", table_name="activities")
    op.drop_constraint("fk_activities_manager_schedule_id", "activities", type_="foreignkey")
    op.drop_column("activities", "task_bonus_points")
    op.drop_column("activities", "manager_schedule_id")
    op.drop_table("manager_task_schedules")
