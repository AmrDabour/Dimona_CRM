from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class LeadSourceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    campaign_name: Optional[str] = Field(None, max_length=255)
    campaign_cost: Optional[Decimal] = Field(None, ge=0)
    default_team_id: Optional[UUID] = Field(
        None,
        description="Leads from this source inherit this team for manager routing",
    )


class LeadSourceCreate(LeadSourceBase):
    pass


class LeadSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    campaign_name: Optional[str] = Field(None, max_length=255)
    campaign_cost: Optional[Decimal] = Field(None, ge=0)
    default_team_id: Optional[UUID] = None


class LeadSourceResponse(LeadSourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    lead_count: Optional[int] = None
