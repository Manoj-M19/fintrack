from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "fintrack",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    # Run check_all_budgets every hour
    beat_schedule={
        "check-budgets-every-hour": {
            "task": "tasks.check_all_budgets",
            "schedule": 3600.0,
        },
    },
)