from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.activity import ActivityType


class ActivityBase(BaseModel):
    type: ActivityType
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class ActivityCreate(ActivityBase):
    call_recording_url: Optional[str] = Field(None, max_length=500)


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
    lead_id: UUID
    user_id: Optional[UUID]
    call_recording_url: Optional[str]
    is_completed: bool
    google_calendar_event_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    user: Optional[ActivityUserInfo] = None
