from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_roles, PaginationParams
from app.services.user_service import UserService
from app.core.permissions import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserPasswordUpdate
from app.schemas.common import PaginatedResponse, MessageResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current authenticated user's profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update current authenticated user's profile."""
    user_service = UserService(db)
    return await user_service.update_user(current_user.id, user_data, current_user)


@router.post("/me/change-password", response_model=MessageResponse)
async def change_password(
    password_data: UserPasswordUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Change current user's password."""
    user_service = UserService(db)
    await user_service.change_password(
        current_user.id,
        password_data.current_password,
        password_data.new_password,
    )
    return MessageResponse(message="Password changed successfully")


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    team_id: Optional[UUID] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
):
    """List all users (Admin: all, Manager: team only)."""
    user_service = UserService(db)

    if current_user.role == UserRole.MANAGER:
        team_id = current_user.team_id

    users, total = await user_service.list_users(
        page=pagination.page,
        page_size=pagination.page_size,
        team_id=team_id,
        role=role,
        is_active=is_active,
    )

    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return PaginatedResponse(
        items=users,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new user (Admin only)."""
    user_service = UserService(db)
    return await user_service.create_user(user_data, current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get user by ID."""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)

    if current_user.role == UserRole.MANAGER and user.team_id != current_user.team_id:
        from app.core.exceptions import PermissionDeniedException
        raise PermissionDeniedException("You can only view users in your team")

    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update user by ID (Admin only)."""
    user_service = UserService(db)
    return await user_service.update_user(user_id, user_data, current_user)


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete user by ID (Admin only, soft delete)."""
    user_service = UserService(db)
    await user_service.delete_user(user_id, current_user)
    return MessageResponse(message="User deleted successfully")


@router.post("/{user_id}/reset-password", response_model=MessageResponse)
async def reset_user_password(
    user_id: UUID,
    new_password: str,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reset user's password (Admin only)."""
    user_service = UserService(db)
    await user_service.reset_password(user_id, new_password, current_user)
    return MessageResponse(message="Password reset successfully")
