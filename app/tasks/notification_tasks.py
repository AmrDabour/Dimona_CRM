import asyncio
from datetime import datetime, timezone, timedelta
from typing import List

from app.tasks import celery_app
from app.database import AsyncSessionLocal


@celery_app.task(name="app.tasks.notification_tasks.check_overdue_activities")
def check_overdue_activities():
    """Check for overdue activities and notify agents."""
    asyncio.run(_check_overdue_activities())


async def _check_overdue_activities():
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.activity import Activity
    from app.models.lead import Lead
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)

        query = select(Activity).where(
            Activity.is_completed == False,
            Activity.scheduled_at != None,
            Activity.scheduled_at < now,
        ).options(
            selectinload(Activity.lead),
            selectinload(Activity.user),
        )

        result = await db.execute(query)
        overdue_activities = result.scalars().all()

        for activity in overdue_activities:
            if activity.user and activity.user.email:
                pass


@celery_app.task(name="app.tasks.notification_tasks.send_followup_reminder")
def send_followup_reminder(activity_id: str, user_id: str):
    """Send a follow-up reminder notification."""
    asyncio.run(_send_followup_reminder(activity_id, user_id))


async def _send_followup_reminder(activity_id: str, user_id: str):
    from uuid import UUID
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.activity import Activity

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Activity)
            .where(Activity.id == UUID(activity_id))
            .options(selectinload(Activity.lead), selectinload(Activity.user))
        )
        activity = result.scalar_one_or_none()

        if activity and not activity.is_completed:
            pass


@celery_app.task(name="app.tasks.notification_tasks.notify_new_lead_assignment")
def notify_new_lead_assignment(lead_id: str, agent_id: str):
    """Notify agent of new lead assignment."""
    asyncio.run(_notify_new_lead_assignment(lead_id, agent_id))


async def _notify_new_lead_assignment(lead_id: str, agent_id: str):
    from uuid import UUID
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.lead import Lead
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        lead_result = await db.execute(
            select(Lead).where(Lead.id == UUID(lead_id)).options(selectinload(Lead.source))
        )
        lead = lead_result.scalar_one_or_none()

        agent_result = await db.execute(
            select(User).where(User.id == UUID(agent_id))
        )
        agent = agent_result.scalar_one_or_none()

        if lead and agent:
            pass


@celery_app.task(name="app.tasks.notification_tasks.check_stuck_leads")
def check_stuck_leads():
    """Check for leads stuck in a stage for too long (SLA monitoring)."""
    asyncio.run(_check_stuck_leads())


async def _check_stuck_leads():
    from sqlalchemy import select, func
    from sqlalchemy.orm import selectinload
    from app.models.lead import Lead, LeadStatus
    from app.models.pipeline_history import PipelineHistory

    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        threshold = now - timedelta(hours=48)

        active_statuses = [LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.VIEWING, LeadStatus.NEGOTIATION]

        query = select(Lead).where(
            Lead.is_deleted == False,
            Lead.status.in_(active_statuses),
            Lead.updated_at < threshold,
        ).options(selectinload(Lead.assigned_user))

        result = await db.execute(query)
        stuck_leads = result.scalars().all()

        for lead in stuck_leads:
            if lead.assigned_user:
                pass
