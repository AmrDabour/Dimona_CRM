from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.activity import ActivityType


class TeamActivityItem(BaseModel):
    """Scheduled team task row for manager dashboard."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lead_id: UUID
    lead_full_name: str
    type: ActivityType
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    is_completed: bool
    is_overdue: bool
    assigned_to: Optional[UUID] = None
    assignee_name: Optional[str] = None
    owner_user_id: Optional[UUID] = None
    owner_name: Optional[str] = None
