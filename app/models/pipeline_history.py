import uuid
from datetime import datetime
from sqlalchemy import Text, DateTime, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.base import generate_uuid
from app.models.lead import LeadStatus


class PipelineHistory(Base):
    __tablename__ = "pipeline_history"

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
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    from_status: Mapped[LeadStatus | None] = mapped_column(
        SQLEnum(LeadStatus, name="lead_status", create_type=False, values_callable=lambda e: [x.value for x in e]),
        nullable=True,
    )
    to_status: Mapped[LeadStatus] = mapped_column(
        SQLEnum(LeadStatus, name="lead_status", create_type=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    lead: Mapped["Lead"] = relationship(
        "Lead",
        back_populates="pipeline_history",
    )
    user: Mapped["User | None"] = relationship("User")
