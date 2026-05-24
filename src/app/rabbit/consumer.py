"""Консьюмер доменных событий из RabbitMQ."""

import json

from aio_pika import ExchangeType, connect_robust
from aiormq.exceptions import AMQPError
from loguru import logger
from sqlalchemy import select

from app.core.config import settings
from app.core.constants import (
    DOMAIN_EVENTS_EXCHANGE,
    DOMAIN_EVENTS_QUEUE,
    DOMAIN_EVENTS_ROUTING_KEY,
)
from app.models.processed_event import ProcessedEvent
from celery_app.tasks.booking_notifications import (
    send_email_booking_notification,
)
from celery_app.utils.celery_db import get_session


async def consume_domain_events(max_messages: int = 100) -> dict:
    """Вычитать события из очереди и маршрутизировать в Celery-задачи."""
    processed = 0
    skipped = 0
    failed = 0

    connection = await connect_robust(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        login=settings.rabbitmq_user,
        password=settings.rabbitmq_pass,
        virtualhost=settings.rabbitmq_vhost,
        heartbeat=settings.rabbitmq_heartbeat,
        connection_attempts=settings.rabbitmq_connection_attempts,
    )

    try:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            DOMAIN_EVENTS_EXCHANGE,
            ExchangeType.DIRECT,
            durable=True,
        )
        queue = await channel.declare_queue(DOMAIN_EVENTS_QUEUE, durable=True)
        await queue.bind(exchange, routing_key=DOMAIN_EVENTS_ROUTING_KEY)

        for _ in range(max_messages):
            message = await queue.get(fail=False)
            if message is None:
                break

            try:
                payload = json.loads(message.body.decode('utf-8'))
                event_id = payload.get('event_id')
                event_type = payload.get('event_type')
                event_payload = payload.get('payload', {})
                correlation_id = str(event_payload.get('correlation_id', '-'))

                if not event_id or not event_type:
                    failed += 1
                    logger.error(
                        'consumer.invalid_event req={req}',
                        req=correlation_id,
                    )
                    await message.ack()
                    continue

                with get_session() as session:
                    already_processed = session.execute(
                        select(ProcessedEvent).where(
                            ProcessedEvent.event_id == event_id,
                        ),
                    ).scalar_one_or_none()

                    if already_processed is not None:
                        skipped += 1
                        logger.info(
                            'consumer.dup eid={eid} req={req}',
                            eid=event_id,
                            req=correlation_id,
                        )
                        await message.ack()
                        continue

                    logger.info(
                        'consumer.recv eid={eid} type={type} req={req}',
                        eid=event_id,
                        type=event_type,
                        req=correlation_id,
                    )

                    if event_type == 'booking.created':
                        booking_id = event_payload.get('booking_id')
                        if booking_id is None:
                            raise ValueError('booking_id is required')
                        send_email_booking_notification.delay(
                            int(booking_id),
                            correlation_id=correlation_id,
                        )

                    elif event_type == 'booking.updated':
                        booking_id = event_payload.get('booking_id')
                        if booking_id is not None:
                            send_email_booking_notification.delay(
                                int(booking_id),
                                correlation_id=correlation_id,
                            )

                    session.add(
                        ProcessedEvent(
                            event_id=event_id,
                            event_type=event_type,
                        ),
                    )

                processed += 1
                logger.info(
                    'consumer.done eid={eid} type={type} req={req}',
                    eid=event_id,
                    type=event_type,
                    req=correlation_id,
                )
                await message.ack()

            except (ValueError, AMQPError, KeyError, TypeError):
                failed += 1
                logger.exception(
                    'Ошибка обработки события из domain.events: {error}',
                )
                await message.reject(requeue=True)

    finally:
        await connection.close()

    return {
        'status': 'completed',
        'processed': processed,
        'skipped': skipped,
        'failed': failed,
    }
