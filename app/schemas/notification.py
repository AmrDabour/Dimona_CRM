from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    title: str
    body: Optional[str] = None
    lead_id: Optional[UUID] = None
    read_at: Optional[datetime] = None
    created_at: datetime
    reference_type: str
    reference_id: UUID


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int


class UnreadCountResponse(BaseModel):
    count: int
