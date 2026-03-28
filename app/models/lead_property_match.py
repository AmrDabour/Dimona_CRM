import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy import Boolean, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db_base import Base
from app.models.base import generate_uuid


class LeadPropertyMatch(Base):
    __tablename__ = "lead_property_matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relevance_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    is_suggested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    lead: Mapped["Lead"] = relationship(
        "Lead",
        back_populates="property_matches",
    )
    unit: Mapped["Unit"] = relationship(
        "Unit",
        back_populates="property_matches",
    )
