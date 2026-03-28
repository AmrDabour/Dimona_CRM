import uuid
from enum import Enum
from datetime import datetime
from sqlalchemy import String, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db_base import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, generate_uuid


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    VIEWING = "viewing"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class Lead(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
    )
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    whatsapp_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[LeadStatus] = mapped_column(
        SQLEnum(LeadStatus, name="lead_status", values_callable=lambda e: [x.value for x in e]),
        default=LeadStatus.NEW,
        nullable=False,
        index=True,
    )
    lost_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    custom_fields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    assigned_user: Mapped["User | None"] = relationship(
        "User",
        back_populates="assigned_leads",
        foreign_keys=[assigned_to],
    )
    source: Mapped["LeadSource | None"] = relationship(
        "LeadSource",
        back_populates="leads",
    )
    team: Mapped["Team | None"] = relationship(
        "Team",
        foreign_keys=[team_id],
    )
    requirements: Mapped[list["LeadRequirement"]] = relationship(
        "LeadRequirement",
        back_populates="lead",
        cascade="all, delete-orphan",
    )
    activities: Mapped[list["Activity"]] = relationship(
        "Activity",
        back_populates="lead",
        cascade="all, delete-orphan",
    )
    pipeline_history: Mapped[list["PipelineHistory"]] = relationship(
        "PipelineHistory",
        back_populates="lead",
        cascade="all, delete-orphan",
    )
    property_matches: Mapped[list["LeadPropertyMatch"]] = relationship(
        "LeadPropertyMatch",
        back_populates="lead",
        cascade="all, delete-orphan",
    )
