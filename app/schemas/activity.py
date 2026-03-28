from uuid import UUID
from datetime import date, datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.activity import ActivityType


class ActivityBase(BaseModel):
    type: ActivityType
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class ActivityCreate(ActivityBase):
    call_recording_url: Optional[str] = Field(None, max_length=500)


class ManagerTaskAssign(BaseModel):
    assignee_id: UUID
    type: ActivityType
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    lead_id: Optional[UUID] = None
    task_points: int = Field(0, ge=0, le=500)
    recurrence: Literal["once", "weekly"] = "once"
    """once: single task. weekly: repeat on selected weekdays (0=Mon .. 6=Sun, UTC)."""
    weekdays: Optional[List[int]] = None

    @model_validator(mode="after")
    def _weekly_requires_weekdays(self):
        if self.recurrence == "weekly":
            if not self.weekdays:
                raise ValueError("weekdays is required for weekly recurrence")
            for d in self.weekdays:
                if d < 0 or d > 6:
                    raise ValueError("weekdays must be integers 0-6 (Mon-Sun)")
        return self


class ActivityUpdate(BaseModel):
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    is_completed: Optional[bool] = None


class ActivityUserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: str


class ActivityResponse(ActivityBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lead_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    assigned_by_id: Optional[UUID] = None
    call_recording_url: Optional[str]
    is_completed: bool
    google_calendar_event_id: Optional[str]
    task_bonus_points: int = 0
    manager_schedule_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    user: Optional[ActivityUserInfo] = None
    assigned_by: Optional[ActivityUserInfo] = None


class ManagerTaskScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assignee_id: UUID
    assignee_name: str
    assigned_by_id: UUID
    lead_id: Optional[UUID] = None
    activity_type: ActivityType
    description: Optional[str] = None
    task_points: int
    weekdays: List[int]
    schedule_hour_utc: int
    schedule_minute_utc: int
    is_active: bool
    last_fired_on: Optional[date] = None


class ManagerTaskAssignResult(BaseModel):
    activity: Optional[ActivityResponse] = None
    schedule_id: Optional[UUID] = None
    detail: Optional[str] = None
