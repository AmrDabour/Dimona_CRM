from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.lead import LeadStatus


class LeadBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=8, max_length=20)
    email: Optional[EmailStr] = None
    whatsapp_number: Optional[str] = Field(None, max_length=20)


class LeadCreate(LeadBase):
    source_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    custom_fields: Optional[dict] = None


class LeadUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=8, max_length=20)
    email: Optional[EmailStr] = None
    whatsapp_number: Optional[str] = Field(None, max_length=20)
    custom_fields: Optional[dict] = None


class LeadStatusUpdate(BaseModel):
    status: LeadStatus
    note: Optional[str] = None
    lost_reason: Optional[str] = None


class LeadAssign(BaseModel):
    assigned_to: UUID


class LeadSourceInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    campaign_name: Optional[str] = None


class LeadAssignedUserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: str


class LeadResponse(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: LeadStatus
    lost_reason: Optional[str]
    assigned_to: Optional[UUID]
    source_id: Optional[UUID]
    custom_fields: Optional[dict]
    created_at: datetime
    updated_at: datetime
    source: Optional[LeadSourceInfo] = None
    assigned_user: Optional[LeadAssignedUserInfo] = None


class LeadListResponse(BaseModel):
    items: List[LeadResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
