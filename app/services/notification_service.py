import logging
from uuid import UUID
from datetime import datetime, timezone
from typing import List, Tuple

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.user import User
from app.models.activity import Activity
from app.core.exceptions import NotFoundException


NOTIFICATION_TYPE_ACTIVITY_REMINDER_5M = "activity_reminder_5m"
NOTIFICATION_TYPE_MANAGER_TASK_ASSIGNED = "manager_task_assigned"
REFERENCE_TYPE_ACTIVITY = "activity"

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_user(
        self,
        user: User,
        *,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Notification], int]:
        conds = [Notification.user_id == user.id]
        if unread_only:
            conds.append(Notification.read_at.is_(None))

        count_q = select(func.count()).select_from(Notification).where(*conds)
        total = int(await self.db.scalar(count_q) or 0)

        q = select(Notification).where(*conds).order_by(Notification.created_at.desc())
        q = q.offset(offset).limit(limit)
        result = await self.db.execute(q)
        items = list(result.scalars().all())
        return items, total

    async def unread_count(self, user: User) -> int:
        q = select(func.count()).where(
            Notification.user_id == user.id,
            Notification.read_at.is_(None),
        )
        return int(await self.db.scalar(q) or 0)

    async def mark_read(self, notification_id: UUID, user: User) -> Notification:
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user.id,
            )
        )
        n = result.scalar_one_or_none()
        if not n:
            raise NotFoundException("Notification")
        n.read_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(n)
        return n

    async def mark_all_read(self, user: User) -> int:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            update(Notification)
            .where(
                Notification.user_id == user.id,
                Notification.read_at.is_(None),
            )
            .values(read_at=now)
        )
        await self.db.commit()
        return result.rowcount or 0

    async def notify_manager_task_assigned(
        self,
        *,
        assignee: User,
        activity: Activity,
        assigner_name: str,
        lead_name: str | None,
    ) -> Notification:
        """In-app notification when a manager/admin assigns a task to an agent."""
        title = "New task from your manager"
        if lead_name:
            body = f"{assigner_name} assigned you a {activity.type.value} regarding {lead_name}."
        else:
            body = f"{assigner_name} assigned you a {activity.type.value}."
        if activity.description:
            body = f"{body} {activity.description[:200]}"

        n = Notification(
            user_id=assignee.id,
            type=NOTIFICATION_TYPE_MANAGER_TASK_ASSIGNED,
            title=title,
            body=body,
            lead_id=activity.lead_id,
            reference_type=REFERENCE_TYPE_ACTIVITY,
            reference_id=activity.id,
        )
        self.db.add(n)
        await self.db.commit()
        await self.db.refresh(n)

        # Re-read email from DB (canonical value for this user — login / profile updates).
        row = await self.db.execute(select(User.email).where(User.id == assignee.id))
        to_email = (row.scalar_one_or_none() or "").strip()

        if to_email:
            try:
                from app.tasks.notification_tasks import send_transactional_email

                async_result = send_transactional_email.delay(to_email, title, body)
                logger.info(
                    "Queued transactional email for manager task: celery_task_id=%s to=%s",
                    async_result.id,
                    to_email,
                )
            except Exception:
                logger.exception("Queue transactional email for manager task failed")
        else:
            logger.warning(
                "No transactional email for manager task: user has no email in DB (user_id=%s)",
                assignee.id,
            )

        return n
