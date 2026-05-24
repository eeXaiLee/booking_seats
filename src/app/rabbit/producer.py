"""Модуль отправки сообщений в RabbitMQ."""

import json
from typing import Dict

from aio_pika import ExchangeType, Message
from aiormq.exceptions import AMQPError
from loguru import logger

from app.core.config import settings
from app.core.constants import (
    DOMAIN_EVENTS_EXCHANGE,
    DOMAIN_EVENTS_QUEUE,
    DOMAIN_EVENTS_ROUTING_KEY,
    ENCODING,
)

from .connection import RabbitMQConnection


async def send_message(
    queue_name: str,
    message: Dict[str, object],
    exchange_name: str | None = None,
    routing_key: str | None = None,
) -> bool:
    """Функция отправляет сообщение в указанную очередь RabbitMQ."""
    rabbit_connection = RabbitMQConnection()

    try:
        await rabbit_connection.connect()
        channel = rabbit_connection.channel
        if not channel:
            logger.error('Канал RabbitMQ не найден. Сообщение не отправлено.')
            return False

        exchange = channel.default_exchange
        resolved_routing_key = routing_key or queue_name

        if exchange_name:
            exchange = await channel.declare_exchange(
                exchange_name,
                ExchangeType.DIRECT,
                durable=True,
            )
            queue = await channel.declare_queue(queue_name, durable=True)
            await queue.bind(exchange, routing_key=resolved_routing_key)
        else:
            await channel.declare_queue(queue_name, durable=True)

        body = json.dumps(
            message,
            ensure_ascii=False,
            default=str,
        ).encode(ENCODING)

        await exchange.publish(
            Message(
                body=body,
                content_type='application/json',
                delivery_mode=settings.rabbitmq_delivery_mode,
            ),
            routing_key=resolved_routing_key,
        )

        logger.info(
            f"Сообщение отправлено в очередь '{queue_name}': {message}",
        )
        return True

    except AMQPError as e:
        logger.error(
            f"Сетевая ошибка RabbitMQ при отправке в '{queue_name}': {e}",
        )
        return False

    except TypeError as e:
        logger.error(f'Ошибка сериализации сообщения: {e}')
        return False

    except (UnicodeEncodeError, ValueError) as e:
        logger.error(f'Ошибка кодировки сообщения: {e}')
        return False

    finally:
        await rabbit_connection.close()


async def send_domain_event(message: Dict[str, object]) -> bool:
    """Отправить доменное событие в отдельный exchange/queue."""
    return await send_message(
        queue_name=DOMAIN_EVENTS_QUEUE,
        message=message,
        exchange_name=DOMAIN_EVENTS_EXCHANGE,
        routing_key=DOMAIN_EVENTS_ROUTING_KEY,
    )
