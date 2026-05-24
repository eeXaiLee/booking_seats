"""Модуль с задачами Celery.

Обеспечивает фоновую обработку:
- email-напоминаний о бронировании,
- публикации событий из Outbox,
- потребления доменных событий,
- проверки здоровья конвейера.
"""

from celery_app.tasks.booking_notifications import (
    booking_reminder,
    send_email_booking_notification,
    send_email_smtp,
)
from celery_app.tasks.consumer import consume_domain_events_task
from celery_app.tasks.health import check_pipeline_health
from celery_app.tasks.outbox import publish_pending_outbox_events

__all__ = [
    'booking_reminder',
    'check_pipeline_health',
    'consume_domain_events_task',
    'publish_pending_outbox_events',
    'send_email_booking_notification',
    'send_email_smtp',
]
