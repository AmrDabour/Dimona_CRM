from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

if TYPE_CHECKING:
    from app.schemas.user import UserResponse

class BranchBase(BaseModel):
    name: str = Field(..., max_length=100)
    location: str | None = Field(None, max_length=255)
    manager_id: uuid.UUID | None = None

class BranchCreate(BranchBase):
    pass

class BranchUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=255)
    manager_id: uuid.UUID | None = None

class BranchResponse(BranchBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BranchWithDetailsResponse(BranchResponse):
    manager: Optional["UserResponse"] = None
