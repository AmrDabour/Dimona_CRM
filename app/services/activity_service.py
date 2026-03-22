from uuid import UUID
from typing import Optional, List, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.activity import Activity, ActivityType
from app.models.lead import Lead
from app.models.user import User
from app.core.exceptions import NotFoundException, BadRequestException, PermissionDeniedException
from app.core.permissions import UserRole
from app.schemas.activity import ActivityCreate, ActivityUpdate
from app.services.gamification_service import GamificationService


class ActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._gamification = GamificationService(db)

    async def _verify_lead_access(self, lead_id: UUID, current_user: User) -> Lead:
        query = select(Lead).where(Lead.id == lead_id, Lead.is_deleted == False)
        query = query.options(selectinload(Lead.assigned_user))

        result = await self.db.execute(query)
        lead = result.scalar_one_or_none()

        if not lead:
            raise NotFoundException("Lead")

        if current_user.role == UserRole.AGENT and lead.assigned_to != current_user.id:
            raise PermissionDeniedException("You don't have access to this lead")

        if current_user.role == UserRole.MANAGER:
            if lead.assigned_user and lead.assigned_user.team_id != current_user.team_id:
                raise PermissionDeniedException("You don't have access to this lead")

        return lead

    async def get_activity_by_id(
        self,
        activity_id: UUID,
        current_user: User,
    ) -> Activity:
        query = select(Activity).where(Activity.id == activity_id)
        query = query.options(selectinload(Activity.user))

        result = await self.db.execute(query)
        activity = result.scalar_one_or_none()

        if not activity:
            raise NotFoundException("Activity")

        await self._verify_lead_access(activity.lead_id, current_user)

        return activity

    async def list_activities(
        self,
        lead_id: UUID,
        current_user: User,
        page: int = 1,
        page_size: int = 50,
        activity_type: Optional[ActivityType] = None,
    ) -> Tuple[List[Activity], int]:
        await self._verify_lead_access(lead_id, current_user)

        query = select(Activity).where(Activity.lead_id == lead_id)
        query = query.options(selectinload(Activity.user))

        if activity_type:
            query = query.where(Activity.type == activity_type)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(Activity.created_at.desc())

        result = await self.db.execute(query)
        activities = result.scalars().all()

        return list(activities), total

    async def create_activity(
        self,
        lead_id: UUID,
        activity_data: ActivityCreate,
        current_user: User,
    ) -> Activity:
        await self._verify_lead_access(lead_id, current_user)

        new_activity = Activity(
            lead_id=lead_id,
            user_id=current_user.id,
            type=activity_data.type,
            description=activity_data.description,
            scheduled_at=activity_data.scheduled_at,
            call_recording_url=activity_data.call_recording_url,
            is_completed=False if activity_data.scheduled_at else True,
        )

        self.db.add(new_activity)
        await self.db.commit()

        # ── Gamification: activity creation points ───────────────────
        if activity_data.type == ActivityType.CALL:
            await self._gamification.award_points(
                current_user.id, "call_logged",
                reference_id=new_activity.id, reference_type="activity",
            )
        elif activity_data.type == ActivityType.MEETING and activity_data.scheduled_at:
            await self._gamification.award_points(
                current_user.id, "viewing_scheduled",
                reference_id=new_activity.id, reference_type="activity",
            )
        await self.db.commit()

        return await self.get_activity_by_id(new_activity.id, current_user)

    async def update_activity(
        self,
        activity_id: UUID,
        activity_data: ActivityUpdate,
        current_user: User,
    ) -> Activity:
        activity = await self.get_activity_by_id(activity_id, current_user)

        if activity_data.description is not None:
            activity.description = activity_data.description
        if activity_data.scheduled_at is not None:
            activity.scheduled_at = activity_data.scheduled_at
        if activity_data.is_completed is not None:
            activity.is_completed = activity_data.is_completed

        await self.db.commit()
        return await self.get_activity_by_id(activity_id, current_user)

    async def complete_activity(
        self,
        activity_id: UUID,
        current_user: User,
    ) -> Activity:
        activity = await self.get_activity_by_id(activity_id, current_user)

        activity.is_completed = True

        await self.db.commit()

        # ── Gamification: viewing completed points ───────────────────
        if activity.type == ActivityType.MEETING:
            await self._gamification.award_points(
                current_user.id, "viewing_completed",
                reference_id=activity.id, reference_type="activity",
            )
            await self.db.commit()

        return await self.get_activity_by_id(activity_id, current_user)

    async def get_pending_activities(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Activity], int]:
        """Get pending/scheduled activities for the current user or their team."""
        query = select(Activity).where(
            Activity.is_completed == False,
            Activity.scheduled_at != None,
        )
        query = query.options(
            selectinload(Activity.user),
            selectinload(Activity.lead),
        )

        if current_user.role == UserRole.AGENT:
            query = query.where(Activity.user_id == current_user.id)
        elif current_user.role == UserRole.MANAGER:
            team_members_query = select(User.id).where(
                User.team_id == current_user.team_id,
                User.is_deleted == False,
            )
            team_members = await self.db.execute(team_members_query)
            member_ids = [m[0] for m in team_members.fetchall()]
            query = query.where(Activity.user_id.in_(member_ids))

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(Activity.scheduled_at.asc())

        result = await self.db.execute(query)
        activities = result.scalars().all()

        return list(activities), total

    async def get_overdue_activities(
        self,
        current_user: User,
    ) -> List[Activity]:
        """Get overdue activities (scheduled_at is in the past and not completed)."""
        now = datetime.now(timezone.utc)

        query = select(Activity).where(
            Activity.is_completed == False,
            Activity.scheduled_at != None,
            Activity.scheduled_at < now,
        )
        query = query.options(
            selectinload(Activity.user),
            selectinload(Activity.lead),
        )

        if current_user.role == UserRole.AGENT:
            query = query.where(Activity.user_id == current_user.id)
        elif current_user.role == UserRole.MANAGER:
            team_members_query = select(User.id).where(
                User.team_id == current_user.team_id,
                User.is_deleted == False,
            )
            team_members = await self.db.execute(team_members_query)
            member_ids = [m[0] for m in team_members.fetchall()]
            query = query.where(Activity.user_id.in_(member_ids))

        query = query.order_by(Activity.scheduled_at.asc())

        result = await self.db.execute(query)
        return list(result.scalars().all())
