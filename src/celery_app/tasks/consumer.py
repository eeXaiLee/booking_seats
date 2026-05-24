"""Задачи Celery: потребление доменных событий из RabbitMQ."""

import asyncio

from app.rabbit.consumer import consume_domain_events
from celery_app.worker import celery_app


@celery_app.task(
    name='consume_domain_events',
    queue='default',
    max_retries=3,
)
def consume_domain_events_task(max_messages: int = 100) -> dict:
    """Запустить пакетную обработку доменных событий из RabbitMQ."""
    return asyncio.run(consume_domain_events(max_messages=max_messages))
