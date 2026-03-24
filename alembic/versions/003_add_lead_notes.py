"""add notes column to leads

Revision ID: 003_add_lead_notes
Revises: 002_gamification
Create Date: 2026-03-24

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("leads", "notes")
