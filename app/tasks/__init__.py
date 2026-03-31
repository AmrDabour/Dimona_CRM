import asyncio
from celery import Celery
from celery.schedules import crontab
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

from app.config import settings

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=1.0,
        integrations=[CeleryIntegration()],
    )

_loop = None

def run_async(coro):
    global _loop
    if _loop is None:
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop.run_until_complete(coro)

celery_app = Celery(
    "dimora_crm",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.webhook_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.report_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

celery_app.conf.beat_schedule = {
    "dispatch-activity-reminders": {
        "task": "app.tasks.notification_tasks.dispatch_activity_reminders",
        "schedule": 60.0,
    },
    "check-overdue-activities": {
        "task": "app.tasks.notification_tasks.check_overdue_activities",
        "schedule": 3600.0,
    },
    "daily-report": {
        "task": "app.tasks.report_tasks.generate_daily_report",
        "schedule": 86400.0,
    },
    "run-daily-manager-task-schedules": {
        "task": "app.tasks.notification_tasks.run_daily_manager_task_schedules",
        "schedule": crontab(hour=0, minute=5),
    },
}
