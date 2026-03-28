from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any
from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.lead import LeadStatus


class LeadImportResult(BaseModel):
    created: int
    failed: int
    errors: List[str] = Field(default_factory=list)


class LeadBase(BaseModel):
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        validation_alias=AliasChoices("full_name", "fullName", "name"),
    )
    phone: str = Field(
        ...,
        min_length=8,
        max_length=20,
        validation_alias=AliasChoices("phone", "phoneNumber", "phone_number", "mobile"),
    )
    email: Optional[EmailStr] = None
    whatsapp_number: Optional[str] = Field(
        None,
        max_length=20,
        validation_alias=AliasChoices("whatsapp_number", "whatsappNumber", "whatsapp"),
    )

    @field_validator("email", "whatsapp_number", mode="before")
    @classmethod
    def normalize_optional_string_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value

    @field_validator("full_name", "phone", mode="before")
    @classmethod
    def strip_required_string_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value


class LeadCreate(LeadBase):
    source_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("source_id", "sourceId"),
    )
    assigned_to: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("assigned_to", "assignedTo"),
    )
    team_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("team_id", "teamId"),
    )
    custom_fields: Optional[dict] = None
    notes: Optional[str] = None

    @field_validator("source_id", "assigned_to", "notes", mode="before")
    @classmethod
    def normalize_optional_create_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


class LeadUpdate(BaseModel):
    team_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("team_id", "teamId"),
    )
    full_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        validation_alias=AliasChoices("full_name", "fullName", "name"),
    )
    phone: Optional[str] = Field(
        None,
        min_length=8,
        max_length=20,
        validation_alias=AliasChoices("phone", "phoneNumber", "phone_number", "mobile"),
    )
    email: Optional[EmailStr] = None
    whatsapp_number: Optional[str] = Field(
        None,
        max_length=20,
        validation_alias=AliasChoices("whatsapp_number", "whatsappNumber", "whatsapp"),
    )
    custom_fields: Optional[dict] = None
    notes: Optional[str] = None

    @field_validator("email", "whatsapp_number", "notes", mode="before")
    @classmethod
    def normalize_optional_update_string_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value

    @field_validator("full_name", "phone", mode="before")
    @classmethod
    def strip_update_required_string_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value


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
    notes: Optional[str]
    assigned_to: Optional[UUID]
    team_id: Optional[UUID]
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
