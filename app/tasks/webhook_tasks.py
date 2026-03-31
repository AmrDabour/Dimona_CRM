import asyncio
from uuid import UUID
from typing import Dict, Any

from app.tasks import celery_app, run_async
from app.database import AsyncSessionLocal
from app.services.whatsapp_service import whatsapp_service


@celery_app.task(name="app.tasks.webhook_tasks.process_facebook_lead")
def process_facebook_lead_task(lead_data: Dict[str, Any]):
    """Async task to process Facebook Lead Ads webhook."""
    run_async(_process_facebook_lead(lead_data))


async def _process_facebook_lead(lead_data: Dict[str, Any]):
    from sqlalchemy import select
    from app.models.lead import Lead, LeadStatus
    from app.models.lead_source import LeadSource

    async with AsyncSessionLocal() as db:
        leadgen_id = lead_data.get("leadgen_id")
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


@celery_app.task(name="app.tasks.webhook_tasks.process_whatsapp_message")
def process_whatsapp_message_task(message_data: Dict[str, Any]):
    """Async task to process WhatsApp incoming message."""
    run_async(_process_whatsapp_message(message_data))


async def _process_whatsapp_message(message_data: Dict[str, Any]):
    from sqlalchemy import select
    from app.models.lead import Lead, LeadStatus
    from app.models.lead_source import LeadSource
    from app.models.activity import Activity, ActivityType

    async with AsyncSessionLocal() as db:
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


@celery_app.task(name="app.tasks.webhook_tasks.send_whatsapp_message")
def send_whatsapp_message_task(to: str, message: str):
    """Async task to send WhatsApp message."""
    run_async(whatsapp_service.send_text_message(to, message))


@celery_app.task(name="app.tasks.webhook_tasks.send_whatsapp_template")
def send_whatsapp_template_task(to: str, template_name: str, language_code: str = "en"):
    """Async task to send WhatsApp template message."""
    run_async(whatsapp_service.send_template_message(to, template_name, language_code))
