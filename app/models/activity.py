import uuid
from enum import Enum
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Enum as SQLEnum, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db_base import Base
from app.models.base import TimestampMixin, generate_uuid


class ActivityType(str, Enum):
    CALL = "call"
    WHATSAPP = "whatsapp"
    MEETING = "meeting"
    NOTE = "note"
    EMAIL = "email"
    STATUS_CHANGE = "status_change"


class Activity(Base, TimestampMixin):
    __tablename__ = "activities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    type: Mapped[ActivityType] = mapped_column(
        SQLEnum(ActivityType, name="activity_type", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    call_recording_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reminder_5m_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    google_calendar_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    lead: Mapped["Lead"] = relationship(
        "Lead",
        back_populates="activities",
    )
    user: Mapped["User | None"] = relationship(
        "User",
        back_populates="activities",
        foreign_keys="Activity.user_id",
    )
    assigned_by: Mapped["User | None"] = relationship(
        "User",
        back_populates="assigned_tasks",
        foreign_keys="Activity.assigned_by_id",
    )
