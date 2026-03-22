from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

from app.models.lead_requirement import PropertyType


class LeadRequirementBase(BaseModel):
    budget_min: Optional[Decimal] = Field(None, ge=0)
    budget_max: Optional[Decimal] = Field(None, ge=0)
    preferred_locations: Optional[List[str]] = None
    min_bedrooms: Optional[int] = Field(None, ge=0)
    min_area_sqm: Optional[Decimal] = Field(None, ge=0)
    property_type: Optional[PropertyType] = None
    notes: Optional[str] = None


class LeadRequirementCreate(LeadRequirementBase):
    pass


class LeadRequirementUpdate(LeadRequirementBase):
    pass


class LeadRequirementResponse(LeadRequirementBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lead_id: UUID
    created_at: datetime
    updated_at: datetime
