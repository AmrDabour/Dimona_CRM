"""lead team routing and source default team

Revision ID: 005
Revises: 004
Create Date: 2026-03-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "leads",
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_leads_team_id", "leads", ["team_id"], unique=False)

    op.add_column(
        "lead_sources",
        sa.Column(
            "default_team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("lead_sources", "default_team_id")
    op.drop_index("ix_leads_team_id", table_name="leads")
    op.drop_column("leads", "team_id")
