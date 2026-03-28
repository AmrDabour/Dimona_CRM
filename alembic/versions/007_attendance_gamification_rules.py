"""Seed attendance CSV gamification rules

Revision ID: 007
Revises: 006
Create Date: 2026-03-28

"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # Idempotent: skip if event_type already exists
    exists_p = conn.execute(
        sa.text("SELECT 1 FROM point_rules WHERE event_type = 'attendance_present' LIMIT 1")
    ).first()
    if not exists_p:
        op.bulk_insert(
            sa.table(
                "point_rules",
                sa.column("id", postgresql.UUID),
                sa.column("event_type", sa.String),
                sa.column("points", sa.Integer),
                sa.column("category", sa.String),
                sa.column("description", sa.Text),
            ),
            [
                {
                    "id": str(uuid4()),
                    "event_type": "attendance_present",
                    "points": 2,
                    "category": "compliance",
                    "description": "Marked present in attendance CSV import",
                },
            ],
        )

    exists_pen = conn.execute(
        sa.text("SELECT 1 FROM penalty_rules WHERE event_type = 'attendance_absent' LIMIT 1")
    ).first()
    if not exists_pen:
        op.bulk_insert(
            sa.table(
                "penalty_rules",
                sa.column("id", postgresql.UUID),
                sa.column("event_type", sa.String),
                sa.column("points", sa.Integer),
                sa.column("threshold_minutes", sa.Integer),
                sa.column("description", sa.Text),
            ),
            [
                {
                    "id": str(uuid4()),
                    "event_type": "attendance_absent",
                    "points": -5,
                    "threshold_minutes": None,
                    "description": "Marked absent in attendance CSV import",
                },
            ],
        )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM point_rules WHERE event_type = 'attendance_present'")
    )
    op.execute(
        sa.text("DELETE FROM penalty_rules WHERE event_type = 'attendance_absent'")
    )
