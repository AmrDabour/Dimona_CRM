"""activities: nullable lead_id, assigned_by_id for manager tasks

Revision ID: 006
Revises: 005
Create Date: 2026-03-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "activities",
        "lead_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    op.add_column(
        "activities",
        sa.Column(
            "assigned_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_activities_assigned_by_id", "activities", ["assigned_by_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_activities_assigned_by_id", table_name="activities")
    op.drop_column("activities", "assigned_by_id")
    op.alter_column(
        "activities",
        "lead_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
