from uuid import UUID
from typing import List, Optional, Tuple
from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, nulls_last
from sqlalchemy.orm import selectinload

from app.models.activity import Activity, ActivityType
from app.models.lead import Lead
from app.models.user import User
from app.models.manager_task_schedule import ManagerTaskSchedule
from app.core.exceptions import NotFoundException, BadRequestException, PermissionDeniedException
from app.core.permissions import UserRole
from app.schemas.activity import (
    ActivityCreate,
    ActivityUpdate,
    ManagerTaskAssign,
    ManagerTaskAssignResult,
    ManagerTaskScheduleResponse,
    ActivityResponse,
)
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

    async def _lead_display_name(self, lead_id: Optional[UUID]) -> Optional[str]:
        if lead_id is None:
            return None
        row = await self.db.execute(select(Lead.full_name).where(Lead.id == lead_id))
        return row.scalar_one_or_none()

    async def _finalize_manager_task_delivery(
        self,
        activity: Activity,
        assignee: User,
        assigner: User,
        lead_name: Optional[str],
    ) -> None:
        if activity.task_bonus_points and activity.task_bonus_points > 0:
            await self._gamification.award_adjustment_points(
                assignee.id,
                activity.task_bonus_points,
                reference_id=activity.id,
                reference_type="activity",
                note="Task assignment bonus",
            )
            await self.db.commit()
            await self.db.refresh(activity)
        ns = NotificationService(self.db)
        await ns.notify_manager_task_assigned(
            assignee=assignee,
            activity=activity,
            assigner_name=assigner.full_name,
            lead_name=lead_name,
        )

    async def _spawn_from_schedule(
        self, schedule: ManagerTaskSchedule, fire_date: date
    ) -> Optional[Activity]:
        if schedule.last_fired_on == fire_date:
            return None
        r = await self.db.execute(
            select(User).where(User.id == schedule.assignee_id, User.is_deleted.is_(False))
        )
        assignee = r.scalar_one_or_none()
        r2 = await self.db.execute(
            select(User).where(User.id == schedule.assigned_by_id, User.is_deleted.is_(False))
        )
        assigner = r2.scalar_one_or_none()
        if not assignee or not assigner or not assignee.is_active:
            return None

        atype = ActivityType(schedule.activity_type)
        act = Activity(
            lead_id=schedule.lead_id,
            user_id=schedule.assignee_id,
            assigned_by_id=schedule.assigned_by_id,
            type=atype,
            description=schedule.description,
            scheduled_at=schedule.due_at_utc(fire_date),
            call_recording_url=None,
            is_completed=False,
            manager_schedule_id=schedule.id,
            task_bonus_points=schedule.task_points,
        )
        self.db.add(act)
        schedule.last_fired_on = fire_date
        await self.db.commit()
        await self.db.refresh(act)
        await self.db.refresh(schedule)
        lead_name = await self._lead_display_name(schedule.lead_id)
        await self._finalize_manager_task_delivery(act, assignee, assigner, lead_name)
        return act

    @staticmethod
    def _schedule_clock_utc(data: ManagerTaskAssign) -> Tuple[int, int]:
        if data.scheduled_at:
            return data.scheduled_at.hour, data.scheduled_at.minute
        return 9, 0

    async def assign_task_from_manager(
        self,
        data: ManagerTaskAssign,
        current_user: User,
    ) -> ManagerTaskAssignResult:
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

        hour_utc, minute_utc = self._schedule_clock_utc(data)

        if data.recurrence == "weekly":
            ws = sorted(set(data.weekdays or []))
            sched = ManagerTaskSchedule(
                assignee_id=data.assignee_id,
                assigned_by_id=current_user.id,
                lead_id=lead_id,
                activity_type=data.type.value,
                description=data.description,
                task_points=data.task_points,
                weekdays=ws,
                schedule_hour_utc=hour_utc,
                schedule_minute_utc=minute_utc,
                is_active=True,
                last_fired_on=None,
            )
            self.db.add(sched)
            await self.db.commit()
            await self.db.refresh(sched)

            today = datetime.now(timezone.utc).date()
            if today.weekday() in ws:
                act = await self._spawn_from_schedule(sched, today)
                if act:
                    full = await self.get_activity_by_id(act.id, current_user)
                    return ManagerTaskAssignResult(
                        activity=ActivityResponse.model_validate(full),
                        schedule_id=sched.id,
                    )
            return ManagerTaskAssignResult(
                schedule_id=sched.id,
                detail="weekly_schedule_active",
            )

        new_activity = Activity(
            lead_id=lead_id,
            user_id=data.assignee_id,
            assigned_by_id=current_user.id,
            type=data.type,
            description=data.description,
            scheduled_at=data.scheduled_at,
            call_recording_url=None,
            is_completed=False,
            task_bonus_points=data.task_points,
        )

        self.db.add(new_activity)
        await self.db.commit()
        await self.db.refresh(new_activity)

        lead_name = await self._lead_display_name(lead_id)
        await self._finalize_manager_task_delivery(
            new_activity, assignee, current_user, lead_name
        )

        full = await self.get_activity_by_id(new_activity.id, current_user)
        return ManagerTaskAssignResult(activity=ActivityResponse.model_validate(full))

    async def list_manager_task_schedules(
        self, current_user: User
    ) -> List[ManagerTaskScheduleResponse]:
        if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
            raise PermissionDeniedException("Not allowed")

        q = (
            select(ManagerTaskSchedule)
            .where(ManagerTaskSchedule.is_active.is_(True))
            .options(selectinload(ManagerTaskSchedule.assignee))
            .order_by(ManagerTaskSchedule.created_at.desc())
        )
        if current_user.role == UserRole.MANAGER:
            q = q.where(ManagerTaskSchedule.assigned_by_id == current_user.id)

        res = await self.db.execute(q)
        rows = res.scalars().all()
        out: List[ManagerTaskScheduleResponse] = []
        for s in rows:
            an = s.assignee.full_name if s.assignee else ""
            out.append(
                ManagerTaskScheduleResponse(
                    id=s.id,
                    assignee_id=s.assignee_id,
                    assignee_name=an,
                    assigned_by_id=s.assigned_by_id,
                    lead_id=s.lead_id,
                    activity_type=ActivityType(s.activity_type),
                    description=s.description,
                    task_points=s.task_points,
                    weekdays=list(s.weekdays or []),
                    schedule_hour_utc=s.schedule_hour_utc,
                    schedule_minute_utc=s.schedule_minute_utc,
                    is_active=s.is_active,
                    last_fired_on=s.last_fired_on,
                )
            )
        return out

    async def cancel_manager_task_schedule(
        self, schedule_id: UUID, current_user: User
    ) -> None:
        if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
            raise PermissionDeniedException("Not allowed")
        s = await self.db.get(ManagerTaskSchedule, schedule_id)
        if not s:
            raise NotFoundException("Schedule")
        if (
            current_user.role == UserRole.MANAGER
            and s.assigned_by_id != current_user.id
        ):
            raise PermissionDeniedException("You can only cancel your own schedules")
        s.is_active = False
        await self.db.commit()

    async def run_daily_manager_schedules(self) -> int:
        """Create one activity per active schedule when weekday matches (UTC)."""
        today = datetime.now(timezone.utc).date()
        wd = today.weekday()
        res = await self.db.execute(
            select(ManagerTaskSchedule)
            .where(ManagerTaskSchedule.is_active.is_(True))
            .options(
                selectinload(ManagerTaskSchedule.assignee),
                selectinload(ManagerTaskSchedule.assigned_by),
            )
        )
        created = 0
        for s in res.scalars().all():
            if wd not in (s.weekdays or []):
                continue
            act = await self._spawn_from_schedule(s, today)
            if act:
                created += 1
        return created

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
