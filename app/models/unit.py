import uuid
from decimal import Decimal
from enum import Enum
from sqlalchemy import String, Text, Integer, Numeric, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db_base import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, generate_uuid
from app.models.lead_requirement import PropertyType


class UnitStatus(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"


class FinishingType(str, Enum):
    FINISHED = "finished"
    SEMI_FINISHED = "semi_finished"
    CORE_SHELL = "core_shell"


class Unit(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "units"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    unit_number: Mapped[str] = mapped_column(String(50), nullable=False)
    property_type: Mapped[PropertyType] = mapped_column(
        SQLEnum(PropertyType, name="property_type", create_type=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, index=True)
    area_sqm: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    bedrooms: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    bathrooms: Mapped[int] = mapped_column(Integer, nullable=False)
    floor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    finishing: Mapped[FinishingType] = mapped_column(
        SQLEnum(FinishingType, name="finishing_type", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    status: Mapped[UnitStatus] = mapped_column(
        SQLEnum(UnitStatus, name="unit_status", values_callable=lambda e: [x.value for x in e]),
        default=UnitStatus.AVAILABLE,
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    specs: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="units",
    )
    images: Mapped[list["UnitImage"]] = relationship(
        "UnitImage",
        back_populates="unit",
        cascade="all, delete-orphan",
    )
    property_matches: Mapped[list["LeadPropertyMatch"]] = relationship(
        "LeadPropertyMatch",
        back_populates="unit",
        cascade="all, delete-orphan",
    )
