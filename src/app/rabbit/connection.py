"""Модуль подключения к RabbitMQ."""

from aio_pika import connect_robust
from aio_pika.abc import AbstractChannel, AbstractRobustConnection
from loguru import logger

from app.core.config import settings


class RabbitMQConnection:
    """Класс для подключения к RabbitMQ."""

    def __init__(self) -> None:
        """Инициализирует соединение (пока не установлено)."""
        self.connection: AbstractRobustConnection | None = None
        self.channel: AbstractChannel | None = None

    async def connect(self) -> None:
        """Подключиться к RabbitMQ."""
        try:
            self.connection = await connect_robust(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
                login=settings.rabbitmq_user,
                password=settings.rabbitmq_pass,
                virtualhost=settings.rabbitmq_vhost,
                heartbeat=settings.rabbitmq_heartbeat,
                connection_attempts=settings.rabbitmq_connection_attempts,
            )
            self.channel = await self.connection.channel()
            logger.info(
                f'Подключено к RabbitMQ: {settings.rabbitmq_host}:{
                    settings.rabbitmq_port
                }',
            )
        except Exception as e:
            logger.error(f'Ошибка подключения к RabbitMQ: {e}')
            raise

    async def close(self) -> None:
        """Закрыть соединение."""
        if self.connection:
            try:
                await self.connection.close()
                logger.info('Соединение с RabbitMQ закрыто')
            finally:
                self.connection = None
                self.channel = None


rabbit_connection = RabbitMQConnection()
