from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_roles, PaginationParams
from app.services.team_service import TeamService
from app.core.permissions import UserRole
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse
from app.schemas.common import PaginatedResponse, MessageResponse

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("", response_model=PaginatedResponse[TeamResponse])
async def list_teams(
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    include_members: bool = False,
):
    """List all teams."""
    team_service = TeamService(db)
    teams, total = await team_service.list_teams(
        page=pagination.page,
        page_size=pagination.page_size,
        include_members=include_members,
    )

    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return PaginatedResponse(
        items=teams,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new team (Admin only)."""
    team_service = TeamService(db)
    return await team_service.create_team(team_data, current_user)


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))],
    db: Annotated[AsyncSession, Depends(get_db)],
    include_members: bool = True,
):
    """Get team by ID."""
    team_service = TeamService(db)
    return await team_service.get_team_by_id(team_id, include_members=include_members)


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    team_data: TeamUpdate,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update team by ID (Admin only)."""
    team_service = TeamService(db)
    return await team_service.update_team(team_id, team_data, current_user)


@router.delete("/{team_id}", response_model=MessageResponse)
async def delete_team(
    team_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete team by ID (Admin only)."""
    team_service = TeamService(db)
    await team_service.delete_team(team_id, current_user)
    return MessageResponse(message="Team deleted successfully")


@router.post("/{team_id}/members/{user_id}", response_model=TeamResponse)
async def add_member_to_team(
    team_id: UUID,
    user_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add a member to a team (Admin only)."""
    team_service = TeamService(db)
    return await team_service.add_member_to_team(team_id, user_id, current_user)


@router.delete("/{team_id}/members/{user_id}", response_model=TeamResponse)
async def remove_member_from_team(
    team_id: UUID,
    user_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Remove a member from a team (Admin only)."""
    team_service = TeamService(db)
    return await team_service.remove_member_from_team(team_id, user_id, current_user)
