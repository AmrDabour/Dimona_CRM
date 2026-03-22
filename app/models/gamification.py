import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class PointRule(Base, TimestampMixin):
    __tablename__ = "point_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    event_type: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False, server_default="activity")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)


class PenaltyRule(Base, TimestampMixin):
    __tablename__ = "penalty_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    event_type: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    threshold_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)


class PointTransaction(Base):
    __tablename__ = "point_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("point_rules.id", ondelete="SET NULL"), nullable=True,
    )
    penalty_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("penalty_rules.id", ondelete="SET NULL"), nullable=True,
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    period_month: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    rule: Mapped["PointRule | None"] = relationship("PointRule", foreign_keys=[rule_id])
    penalty_rule: Mapped["PenaltyRule | None"] = relationship("PenaltyRule", foreign_keys=[penalty_rule_id])


class UserPointsSummary(Base):
    __tablename__ = "user_points_summary"
    __table_args__ = (UniqueConstraint("user_id", "month", name="uq_user_month"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    month: Mapped[date] = mapped_column(Date, nullable=False)
    total_points: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    activity_points: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    compliance_points: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    conversion_points: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    penalty_points: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class TierConfig(Base):
    __tablename__ = "tier_config"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    min_points: Mapped[int] = mapped_column(Integer, nullable=False)
    commission_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    bonus_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), server_default="0", nullable=False)
    perks: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
