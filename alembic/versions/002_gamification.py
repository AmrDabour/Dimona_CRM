"""Gamification: points, tiers, leaderboard

Revision ID: 002
Revises: 001
Create Date: 2026-03-21 00:00:00.000000

"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── point_rules ──────────────────────────────────────────────────
    op.create_table(
        "point_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(50), unique=True, nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(30), nullable=False, server_default="activity"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # ── penalty_rules ────────────────────────────────────────────────
    op.create_table(
        "penalty_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(50), unique=True, nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("threshold_minutes", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # ── point_transactions (immutable ledger) ────────────────────────
    op.create_table(
        "point_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("point_rules.id", ondelete="SET NULL"), nullable=True),
        sa.Column("penalty_rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("penalty_rules.id", ondelete="SET NULL"), nullable=True),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reference_type", sa.String(30), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("period_month", sa.Date(), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── user_points_summary (denormalised monthly rollup) ────────────
    op.create_table(
        "user_points_summary",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("total_points", sa.Integer(), server_default="0", nullable=False),
        sa.Column("activity_points", sa.Integer(), server_default="0", nullable=False),
        sa.Column("compliance_points", sa.Integer(), server_default="0", nullable=False),
        sa.Column("conversion_points", sa.Integer(), server_default="0", nullable=False),
        sa.Column("penalty_points", sa.Integer(), server_default="0", nullable=False),
        sa.UniqueConstraint("user_id", "month", name="uq_user_month"),
    )

    # ── tier_config ──────────────────────────────────────────────────
    op.create_table(
        "tier_config",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(20), nullable=False),
        sa.Column("min_points", sa.Integer(), nullable=False),
        sa.Column("commission_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("bonus_amount", sa.Numeric(10, 2), server_default="0", nullable=False),
        sa.Column("perks", postgresql.JSONB(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
    )

    # ── Seed default point rules ─────────────────────────────────────
    point_rules = sa.table(
        "point_rules",
        sa.column("id", postgresql.UUID),
        sa.column("event_type", sa.String),
        sa.column("points", sa.Integer),
        sa.column("category", sa.String),
        sa.column("description", sa.Text),
    )
    op.bulk_insert(point_rules, [
        {"id": str(uuid4()), "event_type": "call_logged", "points": 1, "category": "activity", "description": "Phone call logged (>1 min)"},
        {"id": str(uuid4()), "event_type": "inventory_added", "points": 3, "category": "activity", "description": "New inventory unit added with full details"},
        {"id": str(uuid4()), "event_type": "viewing_scheduled", "points": 5, "category": "activity", "description": "Property viewing scheduled"},
        {"id": str(uuid4()), "event_type": "viewing_completed", "points": 10, "category": "activity", "description": "Property viewing completed on-site"},
        {"id": str(uuid4()), "event_type": "lead_profile_complete", "points": 5, "category": "compliance", "description": "Lead profile fully filled (name, budget, area, payment prefs)"},
        {"id": str(uuid4()), "event_type": "no_overdue_weekly", "points": 10, "category": "compliance", "description": "Zero overdue tasks for the entire week"},
        {"id": str(uuid4()), "event_type": "negotiation_reached", "points": 20, "category": "conversion", "description": "Lead moved to Negotiation stage"},
        {"id": str(uuid4()), "event_type": "rent_won", "points": 50, "category": "conversion", "description": "Rental deal closed (Won)"},
        {"id": str(uuid4()), "event_type": "sale_won", "points": 100, "category": "conversion", "description": "Sale deal closed (Won)"},
    ])

    # ── Seed default penalty rules ───────────────────────────────────
    penalty_rules = sa.table(
        "penalty_rules",
        sa.column("id", postgresql.UUID),
        sa.column("event_type", sa.String),
        sa.column("points", sa.Integer),
        sa.column("threshold_minutes", sa.Integer),
        sa.column("description", sa.Text),
    )
    op.bulk_insert(penalty_rules, [
        {"id": str(uuid4()), "event_type": "slow_response", "points": -5, "threshold_minutes": 60, "description": "Responded to new lead after >60 minutes"},
        {"id": str(uuid4()), "event_type": "lost_no_reason", "points": -10, "threshold_minutes": None, "description": "Lead marked as Lost without a clear reason"},
        {"id": str(uuid4()), "event_type": "missed_meeting", "points": -15, "threshold_minutes": None, "description": "Missed scheduled meeting/viewing without prior notice"},
    ])

    # ── Seed default tiers ───────────────────────────────────────────
    tier_config = sa.table(
        "tier_config",
        sa.column("id", postgresql.UUID),
        sa.column("name", sa.String),
        sa.column("min_points", sa.Integer),
        sa.column("commission_pct", sa.Numeric),
        sa.column("bonus_amount", sa.Numeric),
        sa.column("perks", postgresql.JSONB),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(tier_config, [
        {"id": str(uuid4()), "name": "bronze", "min_points": 0, "commission_pct": 15, "bonus_amount": 0, "perks": None, "sort_order": 1},
        {"id": str(uuid4()), "name": "silver", "min_points": 300, "commission_pct": 20, "bonus_amount": 1000, "perks": None, "sort_order": 2},
        {"id": str(uuid4()), "name": "gold", "min_points": 600, "commission_pct": 25, "bonus_amount": 3000, "perks": '{"priority_leads": true}', "sort_order": 3},
    ])


def downgrade() -> None:
    op.drop_table("tier_config")
    op.drop_table("user_points_summary")
    op.drop_table("point_transactions")
    op.drop_table("penalty_rules")
    op.drop_table("point_rules")
