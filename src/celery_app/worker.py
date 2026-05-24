"""Настройка и инициализация Celery для фоновых задач."""

from celery import Celery

from app.core.config import settings
from app.core.logging import configure_logging

from .config import CeleryConfig

configure_logging(
    level=settings.log_level,
    log_file=settings.log_file,
    rotation=settings.log_rotation,
    retention=settings.log_retention,
    enqueue=False,
)

celery_app = Celery('workers')
celery_app.config_from_object(CeleryConfig)

celery_app.autodiscover_tasks(['celery_app.tasks'])
