from typing import Annotated

from fastapi import APIRouter, Depends, Query
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse,
)
from app.services.notification_service import NotificationService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    unread_only: bool = False,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    svc = NotificationService(db)
    items, total = await svc.list_for_user(
        current_user, unread_only=unread_only, limit=limit, offset=offset
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(x) for x in items],
        total=total,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = NotificationService(db)
    n = await svc.unread_count(current_user)
    return UnreadCountResponse(count=n)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = NotificationService(db)
    n = await svc.mark_read(notification_id, current_user)
    return NotificationResponse.model_validate(n)


@router.post("/read-all", response_model=UnreadCountResponse)
async def mark_all_read(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = NotificationService(db)
    await svc.mark_all_read(current_user)
    return UnreadCountResponse(count=0)
