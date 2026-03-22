from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, PaginationParams
from app.services.activity_service import ActivityService
from app.models.user import User
from app.models.activity import ActivityType
from app.schemas.activity import ActivityCreate, ActivityUpdate, ActivityResponse
from app.schemas.common import PaginatedResponse, MessageResponse

router = APIRouter(prefix="/leads/{lead_id}/activities", tags=["Activities"])


@router.get("", response_model=PaginatedResponse[ActivityResponse])
async def list_activities(
    lead_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    activity_type: Optional[ActivityType] = None,
):
    """Get activity timeline for a lead."""
    activity_service = ActivityService(db)
    activities, total = await activity_service.list_activities(
        lead_id=lead_id,
        current_user=current_user,
        page=pagination.page,
        page_size=pagination.page_size,
        activity_type=activity_type,
    )

    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return PaginatedResponse(
        items=activities,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=ActivityResponse)
async def create_activity(
    lead_id: UUID,
    activity_data: ActivityCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Log an activity (call, note, meeting, WhatsApp message, etc.)."""
    activity_service = ActivityService(db)
    return await activity_service.create_activity(lead_id, activity_data, current_user)


# Separate router for activity operations by ID
activity_router = APIRouter(prefix="/activities", tags=["Activities"])


@activity_router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get activity details."""
    activity_service = ActivityService(db)
    return await activity_service.get_activity_by_id(activity_id, current_user)


@activity_router.patch("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: UUID,
    activity_data: ActivityUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update activity details."""
    activity_service = ActivityService(db)
    return await activity_service.update_activity(activity_id, activity_data, current_user)


@activity_router.post("/{activity_id}/complete", response_model=ActivityResponse)
async def complete_activity(
    activity_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark an activity as completed."""
    activity_service = ActivityService(db)
    return await activity_service.complete_activity(activity_id, current_user)


@activity_router.get("/pending/", response_model=PaginatedResponse[ActivityResponse])
async def get_pending_activities(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
):
    """Get pending/scheduled activities for the current user or team."""
    activity_service = ActivityService(db)
    activities, total = await activity_service.get_pending_activities(
        current_user=current_user,
        page=pagination.page,
        page_size=pagination.page_size,
    )

    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return PaginatedResponse(
        items=activities,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@activity_router.get("/overdue/")
async def get_overdue_activities(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get overdue activities (past scheduled date, not completed)."""
    activity_service = ActivityService(db)
    activities = await activity_service.get_overdue_activities(current_user)
    return {"items": activities, "total": len(activities)}
