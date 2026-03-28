from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case, false as sql_false

from app.models.lead import Lead, LeadStatus
from app.models.lead_source import LeadSource
from app.models.activity import Activity
from app.models.user import User
from app.models.team import Team
from app.models.pipeline_history import PipelineHistory
from app.core.permissions import UserRole
from app.core.redis import redis_client
from app.services.gamification_service import GamificationService


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._gamification = GamificationService(db)

    async def get_agent_performance(
        self,
        agent_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get performance metrics for a specific agent."""
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        cache_key = f"agent_perf:{agent_id}:{start_date.date()}:{end_date.date()}"
        cached = await redis_client.get_json(cache_key)
        if cached:
            return cached

        user_result = await self.db.execute(
            select(User).where(User.id == agent_id)
        )
        agent = user_result.scalar_one_or_none()

        total_leads = await self.db.scalar(
            select(func.count(Lead.id)).where(
                Lead.assigned_to == agent_id,
                Lead.is_deleted == False,
                Lead.created_at.between(start_date, end_date),
            )
        )

        won_leads = await self.db.scalar(
            select(func.count(Lead.id)).where(
                Lead.assigned_to == agent_id,
                Lead.is_deleted == False,
                Lead.status == LeadStatus.WON,
                Lead.updated_at.between(start_date, end_date),
            )
        )

        lost_leads = await self.db.scalar(
            select(func.count(Lead.id)).where(
                Lead.assigned_to == agent_id,
                Lead.is_deleted == False,
                Lead.status == LeadStatus.LOST,
                Lead.updated_at.between(start_date, end_date),
            )
        )

        status_query = select(Lead.status, func.count(Lead.id)).where(
            Lead.assigned_to == agent_id,
            Lead.is_deleted == False,
        ).group_by(Lead.status)

        status_result = await self.db.execute(status_query)
        pipeline_breakdown = {row[0].value: row[1] for row in status_result.fetchall()}

        total_activities = await self.db.scalar(
            select(func.count(Activity.id)).where(
                Activity.user_id == agent_id,
                Activity.created_at.between(start_date, end_date),
            )
        )

        calls = await self.db.scalar(
            select(func.count(Activity.id)).where(
                Activity.user_id == agent_id,
                Activity.type == "call",
                Activity.created_at.between(start_date, end_date),
            )
        )

        meetings = await self.db.scalar(
            select(func.count(Activity.id)).where(
                Activity.user_id == agent_id,
                Activity.type == "meeting",
                Activity.created_at.between(start_date, end_date),
            )
        )

        avg_response_hours = None

        conversion_rate = (won_leads / total_leads * 100) if total_leads > 0 else 0
        closed_leads = won_leads + lost_leads
        win_rate = (won_leads / closed_leads * 100) if closed_leads > 0 else 0

        report = {
            "agent": {
                "id": str(agent_id),
                "name": agent.full_name if agent else "Unknown",
                "email": agent.email if agent else None,
            },
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "leads": {
                "total": total_leads,
                "won": won_leads,
                "lost": lost_leads,
                "active": total_leads - won_leads - lost_leads,
                "pipeline_breakdown": pipeline_breakdown,
            },
            "activities": {
                "total": total_activities,
                "calls": calls,
                "meetings": meetings,
            },
            "metrics": {
                "conversion_rate": round(conversion_rate, 2),
                "win_rate": round(win_rate, 2),
                "avg_response_hours": avg_response_hours,
            },
        }

        await redis_client.set_json(cache_key, report, expire=1800)

        return report

    async def get_team_performance(
        self,
        team_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get performance metrics for a team."""
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        team_result = await self.db.execute(
            select(Team).where(Team.id == team_id)
        )
        team = team_result.scalar_one_or_none()

        members_query = select(User.id).where(
            User.team_id == team_id,
            User.is_deleted == False,
        )
        members_result = await self.db.execute(members_query)
        member_ids = [m[0] for m in members_result.fetchall()]

        if not member_ids:
            return {"error": "No team members found"}

        total_leads = await self.db.scalar(
            select(func.count(Lead.id)).where(
                Lead.assigned_to.in_(member_ids),
                Lead.is_deleted == False,
                Lead.created_at.between(start_date, end_date),
            )
        )

        won_leads = await self.db.scalar(
            select(func.count(Lead.id)).where(
                Lead.assigned_to.in_(member_ids),
                Lead.is_deleted == False,
                Lead.status == LeadStatus.WON,
                Lead.updated_at.between(start_date, end_date),
            )
        )

        agent_query = select(
            User.id,
            User.full_name,
            func.count(Lead.id).label("total_leads"),
            func.count(case((Lead.status == LeadStatus.WON, 1))).label("won_leads"),
        ).join(Lead, Lead.assigned_to == User.id, isouter=True).where(
            User.id.in_(member_ids),
            Lead.is_deleted == False,
        ).group_by(User.id, User.full_name)

        agent_result = await self.db.execute(agent_query)
        agent_stats = []
        for row in agent_result.fetchall():
            total = row.total_leads or 0
            won = row.won_leads or 0
            agent_stats.append({
                "agent_id": str(row.id),
                "name": row.full_name,
                "total_leads": total,
                "won_leads": won,
                "conversion_rate": round((won / total * 100), 2) if total > 0 else 0,
            })

        agent_stats.sort(key=lambda x: x["won_leads"], reverse=True)

        return {
            "team": {
                "id": str(team_id),
                "name": team.name if team else "Unknown",
            },
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": {
                "total_leads": total_leads,
                "won_leads": won_leads,
                "conversion_rate": round((won_leads / total_leads * 100), 2) if total_leads > 0 else 0,
                "member_count": len(member_ids),
            },
            "agents": agent_stats,
        }

    async def get_marketing_roi(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get marketing ROI by source/campaign."""
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        cache_key = f"marketing_roi:{start_date.date()}:{end_date.date()}"
        cached = await redis_client.get_json(cache_key)
        if cached:
            return cached

        query = select(
            LeadSource.id,
            LeadSource.name,
            LeadSource.campaign_name,
            LeadSource.campaign_cost,
            func.count(Lead.id).label("total_leads"),
            func.count(case((Lead.status == LeadStatus.WON, 1))).label("won_leads"),
            func.count(case((Lead.status == LeadStatus.LOST, 1))).label("lost_leads"),
        ).join(Lead, Lead.source_id == LeadSource.id, isouter=True).where(
            Lead.is_deleted == False,
            Lead.created_at.between(start_date, end_date),
        ).group_by(
            LeadSource.id,
            LeadSource.name,
            LeadSource.campaign_name,
            LeadSource.campaign_cost,
        )

        result = await self.db.execute(query)

        sources = []
        total_cost = Decimal("0")
        total_leads = 0
        total_won = 0

        for row in result.fetchall():
            leads = row.total_leads or 0
            won = row.won_leads or 0
            cost = row.campaign_cost or Decimal("0")

            cost_per_lead = float(cost / leads) if leads > 0 else 0
            cost_per_won = float(cost / won) if won > 0 else 0
            conversion_rate = (won / leads * 100) if leads > 0 else 0

            sources.append({
                "source_id": str(row.id),
                "source_name": row.name,
                "campaign_name": row.campaign_name,
                "campaign_cost": float(cost),
                "total_leads": leads,
                "won_leads": won,
                "lost_leads": row.lost_leads or 0,
                "cost_per_lead": round(cost_per_lead, 2),
                "cost_per_won": round(cost_per_won, 2),
                "conversion_rate": round(conversion_rate, 2),
            })

            total_cost += cost
            total_leads += leads
            total_won += won

        sources.sort(key=lambda x: x["cost_per_won"] if x["cost_per_won"] > 0 else float("inf"))

        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": {
                "total_campaign_cost": float(total_cost),
                "total_leads": total_leads,
                "total_won": total_won,
                "avg_cost_per_lead": round(float(total_cost / total_leads), 2) if total_leads > 0 else 0,
                "avg_cost_per_won": round(float(total_cost / total_won), 2) if total_won > 0 else 0,
                "overall_conversion": round((total_won / total_leads * 100), 2) if total_leads > 0 else 0,
            },
            "sources": sources,
        }

        await redis_client.set_json(cache_key, report, expire=3600)

        return report

    async def get_dashboard_summary(
        self,
        current_user: User,
    ) -> Dict[str, Any]:
        """Get dashboard summary based on user role."""
        cache_key = f"dashboard:{current_user.id}:{current_user.role.value}"
        cached = await redis_client.get_json(cache_key)
        if cached:
            return cached

        today = datetime.now(timezone.utc).date()
        week_ago = today - timedelta(days=7)

        member_ids: list | None = None
        if current_user.role == UserRole.MANAGER:
            members_result = await self.db.execute(
                select(User.id).where(
                    User.team_id == current_user.team_id,
                    User.is_deleted == False,
                )
            )
            member_ids = [m[0] for m in members_result.fetchall()]

        # Lead list scope: admin = all; agent = own; manager = team + unassigned routed to team
        lead_scope: list = [Lead.is_deleted == False]
        if current_user.role == UserRole.AGENT:
            lead_scope.append(Lead.assigned_to == current_user.id)
        elif current_user.role == UserRole.MANAGER:
            if not current_user.team_id:
                lead_scope.append(sql_false())
            else:
                unassigned_team = and_(
                    Lead.assigned_to.is_(None),
                    Lead.team_id == current_user.team_id,
                )
                if member_ids:
                    lead_scope.append(
                        or_(Lead.assigned_to.in_(member_ids), unassigned_team)
                    )
                else:
                    lead_scope.append(unassigned_team)

        status_result = await self.db.execute(
            select(Lead.status, func.count(Lead.id))
            .where(*lead_scope)
            .group_by(Lead.status)
        )
        pipeline = {row[0].value: row[1] for row in status_result.fetchall()}

        new_today = await self.db.scalar(
            select(func.count(Lead.id)).where(
                *lead_scope,
                func.date(Lead.created_at) == today,
            )
        )

        new_this_week = await self.db.scalar(
            select(func.count(Lead.id)).where(
                *lead_scope,
                Lead.created_at >= datetime.combine(week_ago, datetime.min.time()),
            )
        )

        # Scheduled activities: agent = own; manager = all team members; admin = entire org
        activity_user_scope: list = []
        if current_user.role == UserRole.AGENT:
            activity_user_scope.append(Activity.user_id == current_user.id)
        elif current_user.role == UserRole.MANAGER:
            if member_ids:
                activity_user_scope.append(Activity.user_id.in_(member_ids))
            else:
                activity_user_scope.append(sql_false())

        pending_activities = await self.db.scalar(
            select(func.count(Activity.id)).where(
                Activity.is_completed == False,
                Activity.scheduled_at != None,
                *activity_user_scope,
            )
        )

        overdue_activities = await self.db.scalar(
            select(func.count(Activity.id)).where(
                Activity.is_completed == False,
                Activity.scheduled_at != None,
                Activity.scheduled_at < datetime.now(timezone.utc),
                *activity_user_scope,
            )
        )

        gamification_data = await self._gamification.get_user_monthly_points(current_user.id)

        dashboard = {
            "user": {
                "id": str(current_user.id),
                "name": current_user.full_name,
                "role": current_user.role.value,
            },
            "pipeline": pipeline,
            "leads": {
                "new_today": new_today,
                "new_this_week": new_this_week,
                "total_active": sum(v for k, v in pipeline.items() if k not in ["won", "lost"]),
            },
            "activities": {
                "pending": pending_activities,
                "overdue": overdue_activities,
            },
            "gamification": {
                "total_points": gamification_data["total_points"],
                "tier": gamification_data["tier"],
                "rank": gamification_data["rank"],
                "activity_points": gamification_data["activity_points"],
                "compliance_points": gamification_data["compliance_points"],
                "conversion_points": gamification_data["conversion_points"],
                "penalty_points": gamification_data["penalty_points"],
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        await redis_client.set_json(cache_key, dashboard, expire=300)

        return dashboard
