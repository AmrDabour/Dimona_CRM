from __future__ import annotations

from uuid import UUID
from typing import Optional, Tuple, List
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, true as sql_true
from sqlalchemy.orm import selectinload

from app.models.activity import Activity
from app.models.lead import Lead
from app.models.user import User
from app.core.permissions import UserRole
from app.core.exceptions import PermissionDeniedException
from app.schemas.team_activity import TeamActivityItem


class TeamActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _lead_scope_for_manager(
        member_ids: List[UUID],
        manager_team_id: UUID,
    ):
        unassigned_team = and_(
            Lead.assigned_to.is_(None),
            Lead.team_id == manager_team_id,
        )
        if member_ids:
            return or_(Lead.assigned_to.in_(member_ids), unassigned_team)
        return unassigned_team

    async def list_team_activities(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        only_today: bool = False,
        overdue_only: bool = False,
        filter_team_id: Optional[UUID] = None,
    ) -> Tuple[List[TeamActivityItem], int]:
        """
        Incomplete scheduled activities for leads the user can manage.
        Admin: all teams, optional filter_team_id.
        Manager: own team only.
        """
        if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
            raise PermissionDeniedException("Team activities require manager or admin role")

        lead_scope: object = sql_true()

        if current_user.role == UserRole.MANAGER:
            if not current_user.team_id:
                return [], 0
            res = await self.db.execute(
                select(User.id).where(
                    User.team_id == current_user.team_id,
                    User.is_deleted == False,
                )
            )
            member_ids = [r[0] for r in res.fetchall()]
            lead_scope = self._lead_scope_for_manager(member_ids, current_user.team_id)
        elif filter_team_id:
            res = await self.db.execute(
                select(User.id).where(
                    User.team_id == filter_team_id,
                    User.is_deleted == False,
                )
            )
            member_ids = [r[0] for r in res.fetchall()]
            lead_scope = self._lead_scope_for_manager(member_ids, filter_team_id)

        utc_now = datetime.now(timezone.utc)
        utc_today = utc_now.date()

        where_base = [
            Lead.is_deleted == False,
            Activity.is_completed == False,
            Activity.scheduled_at.isnot(None),
            lead_scope,
        ]
        if overdue_only:
            where_base.append(Activity.scheduled_at < utc_now)
        elif only_today:
            where_base.append(func.date(Activity.scheduled_at) == utc_today)

        count_stmt = (
            select(func.count(Activity.id))
            .select_from(Activity)
            .join(Lead, Lead.id == Activity.lead_id)
            .where(*where_base)
        )
        total = await self.db.scalar(count_stmt) or 0

        data_stmt = (
            select(Activity)
            .join(Lead, Lead.id == Activity.lead_id)
            .where(*where_base)
            .options(
                selectinload(Activity.user),
                selectinload(Activity.lead).selectinload(Lead.assigned_user),
            )
            .order_by(Activity.scheduled_at.asc().nulls_last())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(data_stmt)
        rows = result.scalars().unique().all()

        items: List[TeamActivityItem] = []
        for act in rows:
            lead = act.lead
            assignee = lead.assigned_user if lead else None
            owner = act.user
            overdue = bool(
                act.scheduled_at and act.scheduled_at < utc_now and not act.is_completed
            )
            items.append(
                TeamActivityItem(
                    id=act.id,
                    lead_id=act.lead_id,
                    lead_full_name=lead.full_name if lead else "",
                    type=act.type,
                    description=act.description,
                    scheduled_at=act.scheduled_at,
                    is_completed=act.is_completed,
                    is_overdue=overdue,
                    assigned_to=lead.assigned_to if lead else None,
                    assignee_name=assignee.full_name if assignee else None,
                    owner_user_id=act.user_id,
                    owner_name=owner.full_name if owner else None,
                )
            )

        return items, total
