import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import json

from app.tasks import celery_app, run_async
from app.database import AsyncSessionLocal
from app.core.redis import redis_client


@celery_app.task(name="app.tasks.report_tasks.generate_daily_report")
def generate_daily_report():
    """Generate daily performance report."""
    run_async(_generate_daily_report())


async def _generate_daily_report():
    from sqlalchemy import select, func
    from app.models.lead import Lead, LeadStatus
    from app.models.activity import Activity
    from app.models.user import User
    from app.core.permissions import UserRole

    async with AsyncSessionLocal() as db:
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)

        new_leads = await db.scalar(
            select(func.count(Lead.id)).where(
                Lead.is_deleted == False,
                func.date(Lead.created_at) == yesterday,
            )
        )

        won_leads = await db.scalar(
            select(func.count(Lead.id)).where(
                Lead.is_deleted == False,
                Lead.status == LeadStatus.WON,
                func.date(Lead.updated_at) == yesterday,
            )
        )

        lost_leads = await db.scalar(
            select(func.count(Lead.id)).where(
                Lead.is_deleted == False,
                Lead.status == LeadStatus.LOST,
                func.date(Lead.updated_at) == yesterday,
            )
        )

        activities = await db.scalar(
            select(func.count(Activity.id)).where(
                func.date(Activity.created_at) == yesterday,
            )
        )

        report = {
            "date": str(yesterday),
            "new_leads": new_leads,
            "won_leads": won_leads,
            "lost_leads": lost_leads,
            "total_activities": activities,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        await redis_client.set_json(
            f"daily_report:{yesterday}",
            report,
            expire=86400 * 30,
        )


@celery_app.task(name="app.tasks.report_tasks.generate_agent_performance_report")
def generate_agent_performance_report(agent_id: str):
    """Generate performance report for a specific agent."""
    run_async(_generate_agent_performance_report(agent_id))


async def _generate_agent_performance_report(agent_id: str):
    from uuid import UUID
    from sqlalchemy import select, func
    from app.models.lead import Lead, LeadStatus
    from app.models.activity import Activity

    async with AsyncSessionLocal() as db:
        agent_uuid = UUID(agent_id)

        total_leads = await db.scalar(
            select(func.count(Lead.id)).where(
                Lead.assigned_to == agent_uuid,
                Lead.is_deleted == False,
            )
        )

        won_leads = await db.scalar(
            select(func.count(Lead.id)).where(
                Lead.assigned_to == agent_uuid,
                Lead.is_deleted == False,
                Lead.status == LeadStatus.WON,
            )
        )

        lost_leads = await db.scalar(
            select(func.count(Lead.id)).where(
                Lead.assigned_to == agent_uuid,
                Lead.is_deleted == False,
                Lead.status == LeadStatus.LOST,
            )
        )

        active_leads = await db.scalar(
            select(func.count(Lead.id)).where(
                Lead.assigned_to == agent_uuid,
                Lead.is_deleted == False,
                Lead.status.in_([LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.VIEWING, LeadStatus.NEGOTIATION]),
            )
        )

        total_activities = await db.scalar(
            select(func.count(Activity.id)).where(
                Activity.user_id == agent_uuid,
            )
        )

        conversion_rate = (won_leads / total_leads * 100) if total_leads > 0 else 0

        report = {
            "agent_id": agent_id,
            "total_leads": total_leads,
            "won_leads": won_leads,
            "lost_leads": lost_leads,
            "active_leads": active_leads,
            "total_activities": total_activities,
            "conversion_rate": round(conversion_rate, 2),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        await redis_client.set_json(
            f"agent_report:{agent_id}",
            report,
            expire=3600,
        )

        return report


@celery_app.task(name="app.tasks.report_tasks.cache_pipeline_stats")
def cache_pipeline_stats():
    """Cache pipeline statistics for quick dashboard access."""
    run_async(_cache_pipeline_stats())


async def _cache_pipeline_stats():
    from sqlalchemy import select, func
    from app.models.lead import Lead, LeadStatus

    async with AsyncSessionLocal() as db:
        query = select(Lead.status, func.count(Lead.id)).where(
            Lead.is_deleted == False
        ).group_by(Lead.status)

        result = await db.execute(query)
        status_counts = {row[0].value: row[1] for row in result.fetchall()}

        stats = {
            "stages": {
                "new": status_counts.get("new", 0),
                "contacted": status_counts.get("contacted", 0),
                "viewing": status_counts.get("viewing", 0),
                "negotiation": status_counts.get("negotiation", 0),
                "won": status_counts.get("won", 0),
                "lost": status_counts.get("lost", 0),
            },
            "total": sum(status_counts.values()),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        await redis_client.set_json("pipeline_stats", stats, expire=300)

        return stats
