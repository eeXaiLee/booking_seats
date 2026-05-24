"""Задачи Celery: публикация событий из Outbox в RabbitMQ."""

import asyncio
from datetime import datetime, timezone

from aiormq.exceptions import AMQPError
from loguru import logger
from sqlalchemy import select

from app.core.constants import (
    OUTBOX_STATUS_FAILED,
    OUTBOX_STATUS_PENDING,
    OUTBOX_STATUS_PUBLISHED,
)
from app.models.outbox_event import OutboxEvent
from app.rabbit.producer import send_domain_event
from celery_app.tasks.consumer import consume_domain_events_task
from celery_app.utils.celery_db import get_session
from celery_app.worker import celery_app


@celery_app.task(
    name='publish_pending_outbox_events',
    queue='default',
    max_retries=3,
)
def publish_pending_outbox_events(batch_size: int = 100) -> dict:
    """Опубликовать накопленные pending-события из outbox в RabbitMQ."""
    with get_session() as session:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.status == OUTBOX_STATUS_PENDING)
            .order_by(OutboxEvent.id.asc())
            .limit(batch_size)
        )
        events = session.execute(stmt).scalars().all()

        if not events:
            return {
                'status': 'no_events',
                'published': 0,
                'failed': 0,
            }

        published = 0
        failed = 0

        for event in events:
            correlation_id = str(event.payload.get('correlation_id', '-'))
            logger.info(
                'outbox.publish start '
                'id={outbox_id} evt={event_id} req={request_id}',
                outbox_id=event.id,
                event_id=event.event_id,
                request_id=correlation_id,
            )
            try:
                sent = asyncio.run(
                    send_domain_event(
                        {
                            'event_id': event.event_id,
                            'event_type': event.event_type,
                            'event_version': event.event_version,
                            'occurred_at': event.occurred_at.isoformat(),
                            'aggregate_type': event.aggregate_type,
                            'aggregate_id': event.aggregate_id,
                            'payload': event.payload,
                        },
                    ),
                )
            except (AMQPError, OSError, RuntimeError, ValueError) as error:
                event.status = OUTBOX_STATUS_FAILED
                event.error_message = str(error)
                failed += 1
                logger.exception(
                    'Ошибка публикации outbox event {event_id}',
                    event_id=event.event_id,
                )
                continue

            if sent:
                event.status = OUTBOX_STATUS_PUBLISHED
                event.error_message = None
                event.published_at = datetime.now(timezone.utc)
                published += 1
                logger.info(
                    'outbox.publish ok '
                    'id={outbox_id} evt={event_id} req={request_id}',
                    outbox_id=event.id,
                    event_id=event.event_id,
                    request_id=correlation_id,
                )
            else:
                event.status = OUTBOX_STATUS_FAILED
                event.error_message = 'RabbitMQ publish returned false'
                failed += 1
                logger.error(
                    'outbox.publish fail '
                    'id={outbox_id} evt={event_id} req={request_id}',
                    outbox_id=event.id,
                    event_id=event.event_id,
                    request_id=correlation_id,
                )

        if published > 0:
            logger.info(
                'outbox.consume enqueue published={published}',
                published=published,
            )
            consume_domain_events_task.delay(
                max_messages=max(batch_size, published),
            )

        return {
            'status': 'completed',
            'published': published,
            'failed': failed,
            'processed': len(events),
        }
