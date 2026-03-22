from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_roles, PaginationParams
from app.services.lead_service import LeadService
from app.services.lead_source_service import LeadSourceService
from app.core.permissions import UserRole
from app.models.user import User
from app.models.lead import LeadStatus
from app.schemas.lead import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadListResponse,
    LeadStatusUpdate,
    LeadAssign,
)
from app.schemas.lead_source import LeadSourceCreate, LeadSourceResponse, LeadSourceUpdate
from app.schemas.common import PaginatedResponse, MessageResponse

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("", response_model=LeadListResponse)
async def list_leads(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    status: Optional[LeadStatus] = None,
    source_id: Optional[UUID] = None,
    assigned_to: Optional[UUID] = None,
    search: Optional[str] = None,
):
    """
    List leads with RBAC filtering.
    - Admin: sees all leads
    - Manager: sees team's leads
    - Agent: sees only assigned leads
    """
    lead_service = LeadService(db)
    leads, total = await lead_service.list_leads(
        current_user=current_user,
        page=pagination.page,
        page_size=pagination.page_size,
        status=status,
        source_id=source_id,
        assigned_to=assigned_to,
        search=search,
    )

    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return LeadListResponse(
        items=leads,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Create a new lead.
    - Agent: auto-assigned to self
    - Admin/Manager: can assign to anyone
    """
    lead_service = LeadService(db)
    return await lead_service.create_lead(lead_data, current_user)


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get lead details with requirements and activities."""
    lead_service = LeadService(db)
    return await lead_service.get_lead_by_id(lead_id, current_user, include_relations=True)


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    lead_data: LeadUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update lead information."""
    lead_service = LeadService(db)
    return await lead_service.update_lead(lead_id, lead_data, current_user)


@router.delete("/{lead_id}", response_model=MessageResponse)
async def delete_lead(
    lead_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete lead (Admin only, soft delete)."""
    lead_service = LeadService(db)
    await lead_service.delete_lead(lead_id, current_user)
    return MessageResponse(message="Lead deleted successfully")


@router.patch("/{lead_id}/status", response_model=LeadResponse)
async def update_lead_status(
    lead_id: UUID,
    status_data: LeadStatusUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Change lead pipeline stage.
    Mandatory note/reason if marking as Lost.
    """
    lead_service = LeadService(db)
    return await lead_service.update_lead_status(lead_id, status_data, current_user)


@router.post("/{lead_id}/assign", response_model=LeadResponse)
async def assign_lead(
    lead_id: UUID,
    assign_data: LeadAssign,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Reassign lead to another agent (Admin + Manager only).
    Manager can only assign within their team.
    """
    lead_service = LeadService(db)
    return await lead_service.assign_lead(lead_id, assign_data, current_user)


@router.get("/{lead_id}/pipeline-history")
async def get_pipeline_history(
    lead_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get lead's pipeline stage change history."""
    lead_service = LeadService(db)
    history = await lead_service.get_pipeline_history(lead_id, current_user)
    return {"items": history}


# Lead Sources endpoints
@router.get("/sources/", response_model=PaginatedResponse[LeadSourceResponse])
async def list_lead_sources(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
):
    """List all lead sources with lead counts."""
    source_service = LeadSourceService(db)
    sources, total = await source_service.list_sources(
        page=pagination.page,
        page_size=pagination.page_size,
    )

    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return PaginatedResponse(
        items=sources,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.post("/sources/", response_model=LeadSourceResponse)
async def create_lead_source(
    source_data: LeadSourceCreate,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new lead source (Admin only)."""
    source_service = LeadSourceService(db)
    return await source_service.create_source(source_data, current_user)


@router.patch("/sources/{source_id}", response_model=LeadSourceResponse)
async def update_lead_source(
    source_id: UUID,
    source_data: LeadSourceUpdate,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a lead source (Admin only)."""
    source_service = LeadSourceService(db)
    return await source_service.update_source(source_id, source_data, current_user)


@router.delete("/sources/{source_id}", response_model=MessageResponse)
async def delete_lead_source(
    source_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a lead source (Admin only). Cannot delete if leads exist."""
    source_service = LeadSourceService(db)
    await source_service.delete_source(source_id, current_user)
    return MessageResponse(message="Lead source deleted successfully")
