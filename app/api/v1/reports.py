from typing import Annotated, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.services.report_service import ReportService
from app.core.permissions import UserRole
from app.core.exceptions import PermissionDeniedException
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


@router.get("/dashboard")
async def get_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get dashboard summary for current user.
    Content is filtered based on role:
    - Agent: Personal stats only
    - Manager: Team stats
    - Admin: All stats
    """
    report_service = ReportService(db)
    return await report_service.get_dashboard_summary(current_user)


@router.get("/agent-performance/{agent_id}")
async def get_agent_performance(
    agent_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Get performance report for a specific agent.
    - Agent: Can only view own report
    - Manager: Can view team members' reports
    - Admin: Can view any agent's report
    """
    if current_user.role == UserRole.AGENT and current_user.id != agent_id:
        raise PermissionDeniedException("You can only view your own performance report")

    if current_user.role == UserRole.MANAGER:
        from sqlalchemy import select
        from app.models.user import User as UserModel

        agent_result = await db.execute(
            select(UserModel).where(UserModel.id == agent_id)
        )
        agent = agent_result.scalar_one_or_none()
        if not agent or agent.team_id != current_user.team_id:
            raise PermissionDeniedException("You can only view your team members' reports")

    report_service = ReportService(db)
    return await report_service.get_agent_performance(agent_id, start_date, end_date)


@router.get("/my-performance")
async def get_my_performance(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """Get current user's performance report."""
    report_service = ReportService(db)
    return await report_service.get_agent_performance(current_user.id, start_date, end_date)


@router.get("/team-performance/{team_id}")
async def get_team_performance(
    team_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Get performance report for a team.
    - Manager: Can only view own team
    - Admin: Can view any team
    """
    if current_user.role == UserRole.MANAGER and current_user.team_id != team_id:
        raise PermissionDeniedException("You can only view your own team's report")

    report_service = ReportService(db)
    return await report_service.get_team_performance(team_id, start_date, end_date)


@router.get("/my-team-performance")
async def get_my_team_performance(
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """Get current user's team performance report."""
    if not current_user.team_id:
        return {"error": "You are not assigned to any team"}

    report_service = ReportService(db)
    return await report_service.get_team_performance(current_user.team_id, start_date, end_date)


@router.get("/marketing-roi")
async def get_marketing_roi(
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Get marketing ROI report by source/campaign.
    Admin only - shows campaign costs and cost per lead/conversion.
    """
    report_service = ReportService(db)
    return await report_service.get_marketing_roi(start_date, end_date)


@router.get("/conversion-funnel")
async def get_conversion_funnel(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(30, ge=1, le=365),
):
    """
    Get conversion funnel analysis.
    Shows drop-off rates between pipeline stages.
    """
    from sqlalchemy import select, func
    from app.models.lead import Lead, LeadStatus
    from datetime import timezone

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    base_where = [Lead.is_deleted == False, Lead.created_at >= start_date]

    if current_user.role == UserRole.AGENT:
        base_where.append(Lead.assigned_to == current_user.id)
    elif current_user.role == UserRole.MANAGER:
        members_query = select(User.id).where(
            User.team_id == current_user.team_id,
            User.is_deleted == False,
        )
        members_result = await db.execute(members_query)
        member_ids = [m[0] for m in members_result.fetchall()]
        base_where.append(Lead.assigned_to.in_(member_ids))

    status_query = select(Lead.status, func.count(Lead.id)).where(*base_where).group_by(Lead.status)
    result = await db.execute(status_query)
    counts = {row[0].value: row[1] for row in result.fetchall()}

    stages = ["new", "contacted", "viewing", "negotiation", "won"]
    funnel = []
    prev_count = None

    for stage in stages:
        count = counts.get(stage, 0)
        if stage in ["won", "lost"]:
            pass
        else:
            if prev_count is not None:
                drop_off = ((prev_count - count) / prev_count * 100) if prev_count > 0 else 0
            else:
                drop_off = 0

            funnel.append({
                "stage": stage,
                "count": count,
                "drop_off_rate": round(drop_off, 2) if prev_count else None,
            })
            prev_count = count

    total_new = counts.get("new", 0) + counts.get("contacted", 0) + counts.get("viewing", 0) + counts.get("negotiation", 0) + counts.get("won", 0) + counts.get("lost", 0)
    total_won = counts.get("won", 0)

    return {
        "period_days": days,
        "funnel": funnel,
        "summary": {
            "total_leads": total_new,
            "total_won": total_won,
            "total_lost": counts.get("lost", 0),
            "overall_conversion": round((total_won / total_new * 100), 2) if total_new > 0 else 0,
        },
    }


@router.get("/activity-summary")
async def get_activity_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(30, ge=1, le=365),
):
    """Get activity summary grouped by type."""
    from sqlalchemy import select, func
    from app.models.activity import Activity, ActivityType
    from datetime import timezone

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    base_where = [Activity.created_at >= start_date]

    if current_user.role == UserRole.AGENT:
        base_where.append(Activity.user_id == current_user.id)
    elif current_user.role == UserRole.MANAGER:
        members_query = select(User.id).where(
            User.team_id == current_user.team_id,
            User.is_deleted == False,
        )
        members_result = await db.execute(members_query)
        member_ids = [m[0] for m in members_result.fetchall()]
        base_where.append(Activity.user_id.in_(member_ids))

    type_query = select(Activity.type, func.count(Activity.id)).where(*base_where).group_by(Activity.type)
    result = await db.execute(type_query)
    by_type = {row[0].value: row[1] for row in result.fetchall()}

    total = sum(by_type.values())

    return {
        "period_days": days,
        "by_type": by_type,
        "total": total,
    }
