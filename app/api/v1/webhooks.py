import hmac
import hashlib
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.models.lead import Lead, LeadStatus
from app.models.lead_source import LeadSource
from app.models.activity import Activity, ActivityType
from app.services.whatsapp_service import whatsapp_service

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def verify_facebook_signature(request: Request, payload: bytes) -> bool:
    """Verify Facebook webhook signature."""
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not signature:
        return False

    expected_signature = "sha256=" + hmac.new(
        settings.facebook_app_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


@router.get("/facebook")
async def verify_facebook_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
):
    """Facebook webhook verification endpoint."""
    if hub_mode == "subscribe" and hub_verify_token == settings.facebook_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/facebook")
async def handle_facebook_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Handle Facebook/Instagram Lead Ads webhooks.
    Creates new leads from form submissions.
    """
    payload = await request.body()

    if not verify_facebook_signature(request, payload):
        raise HTTPException(status_code=403, detail="Invalid signature")

    data = await request.json()

    if data.get("object") != "page":
        return {"status": "ignored"}

    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") == "leadgen":
                await process_facebook_lead(db, change.get("value", {}))

    return {"status": "ok"}


async def process_facebook_lead(db: AsyncSession, lead_data: dict):
    """Process a Facebook Lead Ads submission."""
    from sqlalchemy import select

    leadgen_id = lead_data.get("leadgen_id")
    page_id = lead_data.get("page_id")
    form_id = lead_data.get("form_id")
    ad_id = lead_data.get("ad_id")

    source_result = await db.execute(
        select(LeadSource).where(LeadSource.name == "Facebook")
    )
    source = source_result.scalar_one_or_none()

    if not source:
        source = LeadSource(name="Facebook", campaign_name=f"Form {form_id}")
        db.add(source)
        await db.flush()

    field_data = lead_data.get("field_data", [])
    lead_info = {}
    for field in field_data:
        name = field.get("name", "").lower()
        values = field.get("values", [])
        if values:
            lead_info[name] = values[0]

    full_name = lead_info.get("full_name") or f"{lead_info.get('first_name', '')} {lead_info.get('last_name', '')}".strip()
    phone = lead_info.get("phone_number") or lead_info.get("phone", "")
    email = lead_info.get("email")

    if not phone:
        return

    existing = await db.execute(
        select(Lead).where(Lead.phone == phone, Lead.is_deleted == False)
    )
    if existing.scalar_one_or_none():
        return

    new_lead = Lead(
        full_name=full_name or "Facebook Lead",
        phone=phone,
        email=email,
        status=LeadStatus.NEW,
        source_id=source.id,
        team_id=source.default_team_id,
        custom_fields={"facebook_leadgen_id": leadgen_id, "ad_id": ad_id},
    )

    db.add(new_lead)
    await db.commit()


@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
):
    """WhatsApp webhook verification endpoint."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp")
async def handle_whatsapp_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Handle WhatsApp Cloud API webhooks.
    Logs incoming messages and creates leads if not exists.
    """
    data = await request.json()

    message_data = whatsapp_service.parse_webhook_message(data)
    if not message_data:
        return {"status": "ignored"}

    from sqlalchemy import select

    phone = message_data["from"]
    if phone.startswith("0"):
        phone = phone[1:]

    lead_result = await db.execute(
        select(Lead).where(Lead.phone.contains(phone), Lead.is_deleted == False)
    )
    lead = lead_result.scalar_one_or_none()

    if not lead:
        lead_result = await db.execute(
            select(Lead).where(Lead.whatsapp_number == phone, Lead.is_deleted == False)
        )
        lead = lead_result.scalar_one_or_none()

    if lead:
        activity = Activity(
            lead_id=lead.id,
            user_id=None,
            type=ActivityType.WHATSAPP,
            description=f"Incoming message: {message_data.get('text', '[Media]')}",
            is_completed=True,
        )
        db.add(activity)
        await db.commit()
    else:
        source_result = await db.execute(
            select(LeadSource).where(LeadSource.name == "WhatsApp")
        )
        source = source_result.scalar_one_or_none()

        if not source:
            source = LeadSource(name="WhatsApp")
            db.add(source)
            await db.flush()

        new_lead = Lead(
            full_name=message_data.get("contact_name") or "WhatsApp Contact",
            phone=phone,
            whatsapp_number=phone,
            status=LeadStatus.NEW,
            source_id=source.id,
            team_id=source.default_team_id,
        )
        db.add(new_lead)
        await db.commit()

    return {"status": "ok"}


@router.post("/website")
async def handle_website_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Handle website contact form submissions.
    Expected payload: {full_name, phone, email?, message?}
    """
    data = await request.json()

    full_name = data.get("full_name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email")
    message = data.get("message")

    if not full_name or not phone:
        raise HTTPException(status_code=400, detail="full_name and phone are required")

    from sqlalchemy import select

    existing = await db.execute(
        select(Lead).where(Lead.phone == phone, Lead.is_deleted == False)
    )
    if existing.scalar_one_or_none():
        return {"status": "duplicate", "message": "Lead already exists"}

    source_result = await db.execute(
        select(LeadSource).where(LeadSource.name == "Website")
    )
    source = source_result.scalar_one_or_none()

    if not source:
        source = LeadSource(name="Website")
        db.add(source)
        await db.flush()

    new_lead = Lead(
        full_name=full_name,
        phone=phone,
        email=email,
        status=LeadStatus.NEW,
        source_id=source.id,
        team_id=source.default_team_id,
        custom_fields={"initial_message": message} if message else None,
    )

    db.add(new_lead)
    await db.commit()

    return {"status": "created", "lead_id": str(new_lead.id)}
