from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

from app.models.lead_requirement import PropertyType
from app.models.unit import UnitStatus, FinishingType


# Developer schemas
class DeveloperBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None


class DeveloperCreate(DeveloperBase):
    logo_url: Optional[str] = Field(None, max_length=500)


class DeveloperUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)


class DeveloperResponse(DeveloperBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    logo_url: Optional[str]
    created_at: datetime
    project_count: Optional[int] = None


# Project schemas
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    location: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    developer_id: UUID
    lat: Optional[Decimal] = None
    lng: Optional[Decimal] = None
    brochure_url: Optional[str] = Field(None, max_length=500)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    location: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    lat: Optional[Decimal] = None
    lng: Optional[Decimal] = None
    description: Optional[str] = None
    brochure_url: Optional[str] = Field(None, max_length=500)


class ProjectDeveloperInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    developer_id: UUID
    lat: Optional[Decimal]
    lng: Optional[Decimal]
    brochure_url: Optional[str]
    created_at: datetime
    developer: Optional[ProjectDeveloperInfo] = None
    unit_count: Optional[int] = None


# Unit schemas
class UnitBase(BaseModel):
    unit_number: str = Field(..., min_length=1, max_length=50)
    property_type: PropertyType
    price: Decimal = Field(..., ge=0)
    area_sqm: Decimal = Field(..., ge=0)
    bedrooms: int = Field(..., ge=0)
    bathrooms: int = Field(..., ge=0)
    finishing: FinishingType


class UnitCreate(UnitBase):
    project_id: UUID
    floor: Optional[int] = None
    status: UnitStatus = UnitStatus.AVAILABLE
    notes: Optional[str] = None
    specs: Optional[dict] = None


class UnitUpdate(BaseModel):
    unit_number: Optional[str] = Field(None, min_length=1, max_length=50)
    property_type: Optional[PropertyType] = None
    price: Optional[Decimal] = Field(None, ge=0)
    area_sqm: Optional[Decimal] = Field(None, ge=0)
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[int] = Field(None, ge=0)
    floor: Optional[int] = None
    finishing: Optional[FinishingType] = None
    status: Optional[UnitStatus] = None
    notes: Optional[str] = None
    specs: Optional[dict] = None


class UnitProjectInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    location: Optional[str]
    city: Optional[str]


class UnitImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    image_url: str
    sort_order: int


class UnitResponse(UnitBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    floor: Optional[int]
    status: UnitStatus
    notes: Optional[str]
    specs: Optional[dict]
    created_at: datetime
    project: Optional[UnitProjectInfo] = None
    images: Optional[List[UnitImageResponse]] = None


class UnitImageCreate(BaseModel):
    image_url: str = Field(..., max_length=500)
    sort_order: int = 0


# Search/Filter schemas
class UnitSearchParams(BaseModel):
    price_min: Optional[Decimal] = None
    price_max: Optional[Decimal] = None
    bedrooms_min: Optional[int] = None
    bedrooms_max: Optional[int] = None
    area_min: Optional[Decimal] = None
    area_max: Optional[Decimal] = None
    property_type: Optional[PropertyType] = None
    status: Optional[UnitStatus] = None
    city: Optional[str] = None
    location: Optional[str] = None
    developer_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
