from celery import Celery

from src.infrastructure.config.app_config import get_app_config

config = get_app_config()

celery_app = Celery(
    "clean_arch_worker",
    broker=config.CELERY_BROKER_URL,
    include=["src.presentation.workers.user_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
)
