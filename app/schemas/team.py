from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class TeamBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)


class TeamCreate(TeamBase):
    manager_id: Optional[UUID] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    manager_id: Optional[UUID] = None


class TeamMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: str


class TeamResponse(TeamBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    manager_id: Optional[UUID]
    created_at: datetime
    members: Optional[List[TeamMemberResponse]] = None
