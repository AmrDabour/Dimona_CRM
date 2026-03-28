from uuid import UUID
from typing import Optional, List, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, nulls_last
from sqlalchemy.orm import selectinload

from app.models.activity import Activity, ActivityType
from app.models.lead import Lead
from app.models.user import User
from app.core.exceptions import NotFoundException, BadRequestException, PermissionDeniedException
from app.core.permissions import UserRole
from app.schemas.activity import ActivityCreate, ActivityUpdate, ManagerTaskAssign
from app.services.gamification_service import GamificationService
from app.services.lead_access import can_access_lead as lead_can_access
from app.services.notification_service import NotificationService


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

        if not lead_can_access(lead, current_user):
            raise PermissionDeniedException("You don't have access to this lead")

        return lead

    async def _can_access_standalone_activity(self, activity: Activity, current_user: User) -> bool:
        """Access when activity has no lead (general task/note)."""
        if current_user.role == UserRole.ADMIN:
            return True
        if activity.user_id == current_user.id:
            return True
        if activity.assigned_by_id == current_user.id:
            return True
        if current_user.role == UserRole.MANAGER and activity.user_id:
            r = await self.db.execute(
                select(User).where(User.id == activity.user_id, User.is_deleted == False)
            )
            assignee = r.scalar_one_or_none()
            if assignee and current_user.team_id and assignee.team_id == current_user.team_id:
                return True
        return False

    async def _ensure_activity_access(self, activity: Activity, current_user: User) -> None:
        if activity.lead_id is not None:
            await self._verify_lead_access(activity.lead_id, current_user)
            return
        if not await self._can_access_standalone_activity(activity, current_user):
            raise PermissionDeniedException("You don't have access to this activity")

    async def get_activity_by_id(
        self,
        activity_id: UUID,
        current_user: User,
    ) -> Activity:
        query = select(Activity).where(Activity.id == activity_id)
        query = query.options(
            selectinload(Activity.user),
            selectinload(Activity.assigned_by),
        )

        result = await self.db.execute(query)
        activity = result.scalar_one_or_none()

        if not activity:
            raise NotFoundException("Activity")

        await self._ensure_activity_access(activity, current_user)

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
        query = query.options(
            selectinload(Activity.user),
            selectinload(Activity.assigned_by),
        )

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
            assigned_by_id=None,
            type=activity_data.type,
            description=activity_data.description,
            scheduled_at=activity_data.scheduled_at,
            call_recording_url=activity_data.call_recording_url,
            is_completed=False if activity_data.scheduled_at else True,
        )

        self.db.add(new_activity)
        await self.db.commit()

        # ── Gamification: activity creation points (self-logged only) ──
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

    async def assign_task_from_manager(
        self,
        data: ManagerTaskAssign,
        current_user: User,
    ) -> Activity:
        if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
            raise PermissionDeniedException("Only admins and managers can assign tasks")

        result = await self.db.execute(
            select(User).where(
                User.id == data.assignee_id,
                User.is_deleted == False,
            )
        )
        assignee = result.scalar_one_or_none()
        if not assignee:
            raise NotFoundException("User")
        if not assignee.is_active:
            raise BadRequestException("Assignee is inactive")

        if current_user.role == UserRole.MANAGER:
            if not current_user.team_id or assignee.team_id != current_user.team_id:
                raise PermissionDeniedException(
                    "You can only assign tasks to members of your team"
                )

        lead_id = data.lead_id
        if lead_id is not None:
            await self._verify_lead_access(lead_id, current_user)

        new_activity = Activity(
            lead_id=lead_id,
            user_id=data.assignee_id,
            assigned_by_id=current_user.id,
            type=data.type,
            description=data.description,
            scheduled_at=data.scheduled_at,
            call_recording_url=None,
            is_completed=False,
        )

        self.db.add(new_activity)
        await self.db.commit()
        await self.db.refresh(new_activity)

        lead_name: str | None = None
        if lead_id is not None:
            lr = await self.db.execute(select(Lead).where(Lead.id == lead_id))
            ld = lr.scalar_one_or_none()
            lead_name = ld.full_name if ld else None

        ns = NotificationService(self.db)
        await ns.notify_manager_task_assigned(
            assignee=assignee,
            activity=new_activity,
            assigner_name=current_user.full_name,
            lead_name=lead_name,
        )

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
            old_sched = activity.scheduled_at
            new_sched = activity_data.scheduled_at
            if old_sched != new_sched:
                activity.reminder_5m_sent_at = None
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

    async def _apply_pending_role_filter(self, query, current_user: User):
        if current_user.role == UserRole.AGENT:
            return query.where(Activity.user_id == current_user.id)
        if current_user.role == UserRole.MANAGER:
            team_members = await self.db.execute(
                select(User.id).where(
                    User.team_id == current_user.team_id,
                    User.is_deleted == False,
                )
            )
            member_ids = [m[0] for m in team_members.fetchall()]
            return query.where(Activity.user_id.in_(member_ids))
        # ADMIN: no extra filter
        return query

    async def get_pending_activities(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Activity], int]:
        """Pending: incomplete scheduled items OR open manager-assigned tasks."""
        query = select(Activity).where(
            Activity.is_completed == False,
            or_(
                Activity.scheduled_at != None,
                Activity.assigned_by_id != None,
            ),
        )
        query = query.options(
            selectinload(Activity.user),
            selectinload(Activity.assigned_by),
            selectinload(Activity.lead),
        )

        query = await self._apply_pending_role_filter(query, current_user)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(
            nulls_last(Activity.scheduled_at.asc()),
            Activity.created_at.desc(),
        )

        result = await self.db.execute(query)
        activities = result.scalars().all()

        return list(activities), total

    async def get_overdue_activities(
        self,
        current_user: User,
    ) -> List[Activity]:
        """Overdue: scheduled in the past, not completed."""
        now = datetime.now(timezone.utc)

        query = select(Activity).where(
            Activity.is_completed == False,
            Activity.scheduled_at != None,
            Activity.scheduled_at < now,
        )
        query = query.options(
            selectinload(Activity.user),
            selectinload(Activity.assigned_by),
            selectinload(Activity.lead),
        )

        query = await self._apply_pending_role_filter(query, current_user)

        query = query.order_by(Activity.scheduled_at.asc())

        result = await self.db.execute(query)
        return list(result.scalars().all())
