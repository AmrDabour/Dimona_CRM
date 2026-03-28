import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db_base import Base
from app.models.base import TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.lead import Lead
    from app.models.user import User


class ManagerTaskSchedule(Base, TimestampMixin):
    """Recurring manager-assigned tasks (weekly on selected weekdays, UTC)."""

    __tablename__ = "manager_task_schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    assignee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=True, index=True
    )
    activity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_points: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    weekdays: Mapped[List[int]] = mapped_column(JSONB, nullable=False)
    schedule_hour_utc: Mapped[int] = mapped_column(Integer, nullable=False, server_default="9")
    schedule_minute_utc: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    last_fired_on: Mapped[date | None] = mapped_column(Date, nullable=True)

    assignee: Mapped["User"] = relationship("User", foreign_keys=[assignee_id])
    assigned_by: Mapped["User"] = relationship("User", foreign_keys=[assigned_by_id])
    lead: Mapped["Lead | None"] = relationship("Lead", foreign_keys=[lead_id])
    activities: Mapped[List["Activity"]] = relationship(
        "Activity", back_populates="manager_schedule"
    )

    def due_at_utc(self, on_date: date) -> datetime:
        return datetime(
            on_date.year,
            on_date.month,
            on_date.day,
            self.schedule_hour_utc,
            self.schedule_minute_utc,
            tzinfo=timezone.utc,
        )
