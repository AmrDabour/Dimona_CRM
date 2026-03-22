import uuid
from decimal import Decimal
from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class LeadSource(Base, TimestampMixin):
    __tablename__ = "lead_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    campaign_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    campaign_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    # Relationships
    leads: Mapped[list["Lead"]] = relationship(
        "Lead",
        back_populates="source",
    )
