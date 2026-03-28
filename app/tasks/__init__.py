from celery import Celery

from app.config import settings

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
}
