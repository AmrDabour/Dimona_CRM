from typing import Annotated, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.services.whatsapp_service import whatsapp_service
from app.services.calendar_service import calendar_service
from app.services.activity_service import ActivityService
from app.models.user import User
from app.models.activity import Activity, ActivityType
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/integrations", tags=["Integrations"])


# WhatsApp endpoints
@router.post("/whatsapp/send")
async def send_whatsapp_message(
    lead_id: UUID,
    message: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Send a WhatsApp message to a lead."""
    from app.services.lead_service import LeadService

    lead_service = LeadService(db)
    lead = await lead_service.get_lead_by_id(lead_id, current_user)

    phone = lead.whatsapp_number or lead.phone
    if not phone:
        raise HTTPException(status_code=400, detail="Lead has no phone number")

    result = await whatsapp_service.send_text_message(phone, message)

    activity = Activity(
        lead_id=lead.id,
        user_id=current_user.id,
        type=ActivityType.WHATSAPP,
        description=f"Sent: {message}",
        is_completed=True,
    )
    db.add(activity)
    await db.commit()

    return {"status": "sent", "whatsapp_response": result}


@router.post("/whatsapp/send-document")
async def send_whatsapp_document(
    lead_id: UUID,
    document_url: str,
    filename: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    caption: Optional[str] = None,
):
    """Send a document (brochure, PDF) via WhatsApp."""
    from app.services.lead_service import LeadService

    lead_service = LeadService(db)
    lead = await lead_service.get_lead_by_id(lead_id, current_user)

    phone = lead.whatsapp_number or lead.phone
    if not phone:
        raise HTTPException(status_code=400, detail="Lead has no phone number")

    result = await whatsapp_service.send_document(phone, document_url, filename, caption)

    activity = Activity(
        lead_id=lead.id,
        user_id=current_user.id,
        type=ActivityType.WHATSAPP,
        description=f"Sent document: {filename}",
        is_completed=True,
    )
    db.add(activity)
    await db.commit()

    return {"status": "sent", "whatsapp_response": result}


# Google Calendar endpoints
@router.get("/google/auth-url")
async def get_google_auth_url(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get Google OAuth authorization URL."""
    auth_url = calendar_service.get_auth_url(current_user.id)
    return {"auth_url": auth_url}


@router.get("/google/callback")
async def google_oauth_callback(
    code: str,
    state: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Handle Google OAuth callback."""
    try:
        user_id = UUID(state)
        await calendar_service.exchange_code(code, user_id)
        return {"status": "connected", "message": "Google Calendar connected successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/google/status")
async def check_google_connection(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Check if Google Calendar is connected for current user."""
    credentials = await calendar_service.get_credentials(current_user.id)
    return {"connected": credentials is not None}


@router.post("/calendar/sync-activity")
async def sync_activity_to_calendar(
    activity_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Sync an activity (meeting/call) to Google Calendar."""
    activity_service = ActivityService(db)
    activity = await activity_service.get_activity_by_id(activity_id, current_user)

    if not activity.scheduled_at:
        raise HTTPException(status_code=400, detail="Activity has no scheduled time")

    if activity.google_calendar_event_id:
        raise HTTPException(status_code=400, detail="Activity already synced to calendar")

    from app.services.lead_service import LeadService
    lead_service = LeadService(db)
    lead = await lead_service.get_lead_by_id(activity.lead_id, current_user)

    event = await calendar_service.create_event(
        user_id=current_user.id,
        summary=f"{activity.type.value.title()}: {lead.full_name}",
        start_time=activity.scheduled_at,
        description=activity.description,
    )

    if event:
        activity.google_calendar_event_id = event["id"]
        await db.commit()
        return {"status": "synced", "event_id": event["id"]}
    else:
        raise HTTPException(status_code=400, detail="Failed to create calendar event. Please connect Google Calendar first.")


@router.get("/calendar/events")
async def list_calendar_events(
    current_user: Annotated[User, Depends(get_current_user)],
    days: int = 30,
):
    """List upcoming calendar events."""
    events = await calendar_service.list_events(
        user_id=current_user.id,
        max_results=50,
    )

    if not events:
        return {"events": [], "message": "No events found or Calendar not connected"}

    return {"events": events}
