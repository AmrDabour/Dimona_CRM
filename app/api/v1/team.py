from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_roles, PaginationParams
from app.core.permissions import UserRole
from app.models.user import User
from app.schemas.team_activity import TeamActivityItem
from app.schemas.common import PaginatedResponse
from app.services.team_activity_service import TeamActivityService

router = APIRouter(prefix="/team", tags=["Team"])


@router.get("/activities", response_model=PaginatedResponse[TeamActivityItem])
async def list_team_activities(
    current_user: Annotated[
        User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    team_id: Annotated[
        Optional[UUID],
        Query(description="Admin only: filter to a specific team's pipeline"),
    ] = None,
    only_today: Annotated[
        bool,
        Query(description="Only activities scheduled on the current UTC date"),
    ] = False,
    overdue_only: Annotated[
        bool,
        Query(description="Only activities whose scheduled time is in the past"),
    ] = False,
):
    """Scheduled, incomplete activities for the manager's team (or entire org for admin)."""
    svc = TeamActivityService(db)
    effective_team = team_id if current_user.role == UserRole.ADMIN else None
    items, total = await svc.list_team_activities(
        current_user=current_user,
        page=pagination.page,
        page_size=pagination.page_size,
        only_today=only_today,
        overdue_only=overdue_only,
        filter_team_id=effective_team,
    )
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )
