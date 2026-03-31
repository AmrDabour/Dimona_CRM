import asyncio
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.tasks import celery_app, run_async
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.notification_tasks.send_transactional_email")
def send_transactional_email(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
):
    """Queue-friendly wrapper: send one transactional email via SMTP."""
    from app.services.email_service import send_email_sync

    logger.info(
        "send_transactional_email task running: to=%s subject=%s",
        to_email,
        subject[:80] if subject else "",
    )
    ok = send_email_sync([to_email], subject, body_text, body_html)
    if not ok:
        logger.warning(
            "send_transactional_email did not send (see email_service warnings above): to=%s",
            to_email,
        )


@celery_app.task(name="app.tasks.notification_tasks.dispatch_activity_reminders")
def dispatch_activity_reminders():
    """Create in-app notifications ~5 minutes before scheduled activities start."""
    run_async(_dispatch_activity_reminders())


async def _dispatch_activity_reminders():
    from app.config import settings as app_settings
    from app.models.activity import Activity, ActivityType
    from app.models.notification import Notification
    from app.models.lead import Lead
    from app.models.user import User
    from app.services.notification_service import (
        NOTIFICATION_TYPE_ACTIVITY_REMINDER_5M,
        REFERENCE_TYPE_ACTIVITY,
    )

    labels = {
        ActivityType.CALL: "Call",
        ActivityType.WHATSAPP: "WhatsApp",
        ActivityType.MEETING: "Viewing",
        ActivityType.NOTE: "Note",
        ActivityType.EMAIL: "Email",
        ActivityType.STATUS_CHANGE: "Status update",
    }

    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        window_end = now + timedelta(minutes=5)

        result = await db.execute(
            select(Activity)
            .where(
                Activity.is_completed.is_(False),
                Activity.scheduled_at.isnot(None),
                Activity.scheduled_at > now,
                Activity.scheduled_at <= window_end,
                Activity.reminder_5m_sent_at.is_(None),
                Activity.user_id.isnot(None),
            )
        )
        activities = list(result.scalars().all())

    title = "Upcoming activity"
    for activity in activities:
        async with AsyncSessionLocal() as session:
            try:
                fresh = await session.get(Activity, activity.id)
                if (
                    not fresh
                    or fresh.is_completed
                    or fresh.reminder_5m_sent_at is not None
                    or fresh.scheduled_at is None
                ):
                    continue
                now2 = datetime.now(timezone.utc)
                if not (fresh.scheduled_at > now2 and fresh.scheduled_at <= now2 + timedelta(minutes=5)):
                    continue

                lead = await session.get(Lead, fresh.lead_id) if fresh.lead_id else None
                label2 = labels.get(fresh.type, fresh.type.value)
                if lead:
                    body2 = f"{label2} with {lead.full_name} starts in 5 minutes."
                else:
                    desc = (fresh.description or "").strip()
                    body2 = (
                        f"{label2} starts in 5 minutes."
                        if not desc
                        else f"{label2}: {desc[:120]} — starts in 5 minutes."
                    )

                session.add(
                    Notification(
                        user_id=fresh.user_id,
                        type=NOTIFICATION_TYPE_ACTIVITY_REMINDER_5M,
                        title=title,
                        body=body2,
                        lead_id=fresh.lead_id,
                        reference_type=REFERENCE_TYPE_ACTIVITY,
                        reference_id=fresh.id,
                    )
                )
                fresh.reminder_5m_sent_at = now2
                await session.commit()

                user_row = await session.get(User, fresh.user_id)
                if user_row and user_row.email:
                    send_transactional_email.delay(user_row.email, title, body2)

                if (
                    app_settings.email_notify_leads_on_meeting
                    and lead
                    and lead.email
                    and fresh.type == ActivityType.MEETING
                ):
                    when = fresh.scheduled_at.isoformat() if fresh.scheduled_at else ""
                    lead_body = (
                        f"Reminder: your meeting or viewing is coming up soon (scheduled {when} UTC).\n"
                        f"{body2}"
                    )
                    send_transactional_email.delay(lead.email, title, lead_body)
            except IntegrityError:
                await session.rollback()
                logger.debug(
                    "Skip duplicate reminder for activity %s", activity.id
                )


@celery_app.task(name="app.tasks.notification_tasks.check_overdue_activities")
def check_overdue_activities():
    """Check for overdue activities and notify agents."""
    run_async(_check_overdue_activities())


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
    run_async(_send_followup_reminder(activity_id, user_id))


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
    run_async(_notify_new_lead_assignment(lead_id, agent_id))


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
    run_async(_check_stuck_leads())


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


@celery_app.task(name="app.tasks.notification_tasks.run_daily_manager_task_schedules")
def run_daily_manager_task_schedules():
    """Spawn manager recurring tasks for matching UTC weekdays (once per day)."""
    run_async(_run_daily_manager_task_schedules())


async def _run_daily_manager_task_schedules():
    from app.services.activity_service import ActivityService

    async with AsyncSessionLocal() as db:
        svc = ActivityService(db)
        n = await svc.run_daily_manager_schedules()
        logger.info("run_daily_manager_task_schedules: created %s activities", n)
