import uuid
from decimal import Decimal
from enum import Enum
from sqlalchemy import String, Text, Numeric, Integer, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class PropertyType(str, Enum):
    APARTMENT = "apartment"
    VILLA = "villa"
    OFFICE = "office"
    LAND = "land"
    DUPLEX = "duplex"
    PENTHOUSE = "penthouse"


class LeadRequirement(Base, TimestampMixin):
    __tablename__ = "lead_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    preferred_locations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    min_bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_area_sqm: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    property_type: Mapped[PropertyType | None] = mapped_column(
        SQLEnum(PropertyType, name="property_type", values_callable=lambda e: [x.value for x in e]),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    lead: Mapped["Lead"] = relationship(
        "Lead",
        back_populates="requirements",
    )
