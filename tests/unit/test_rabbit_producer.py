"""Unit-тесты RabbitMQ publisher."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.rabbit import producer


@pytest.mark.asyncio
async def test_send_message_creates_and_closes_connection_per_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Отправка не должна переиспользовать канал между вызовами."""
    first_connection = MagicMock()
    first_connection.connect = AsyncMock()
    first_connection.close = AsyncMock()
    first_connection.channel = MagicMock()
    first_connection.channel.default_exchange = MagicMock(
        publish=AsyncMock(),
    )
    first_connection.channel.declare_queue = AsyncMock()

    second_connection = MagicMock()
    second_connection.connect = AsyncMock()
    second_connection.close = AsyncMock()
    second_connection.channel = MagicMock()
    second_connection.channel.default_exchange = MagicMock(
        publish=AsyncMock(),
    )
    second_connection.channel.declare_queue = AsyncMock()

    connections = [first_connection, second_connection]
    monkeypatch.setattr(
        producer,
        'RabbitMQConnection',
        MagicMock(side_effect=connections),
    )

    first_result = await producer.send_message(
        queue_name='domain.events',
        message={'event_id': '1'},
    )
    second_result = await producer.send_message(
        queue_name='domain.events',
        message={'event_id': '2'},
    )

    assert first_result is True
    assert second_result is True
    first_connection.connect.assert_awaited_once()
    second_connection.connect.assert_awaited_once()
    first_connection.close.assert_awaited_once()
    second_connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_message_closes_connection_on_publish_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Соединение должно закрываться даже при ошибке публикации."""
    connection = MagicMock()
    connection.connect = AsyncMock()
    connection.close = AsyncMock()
    connection.channel = MagicMock()
    connection.channel.default_exchange = MagicMock(
        publish=AsyncMock(side_effect=ValueError('broken payload')),
    )
    connection.channel.declare_queue = AsyncMock()

    monkeypatch.setattr(
        producer,
        'RabbitMQConnection',
        MagicMock(return_value=connection),
    )

    result = await producer.send_message(
        queue_name='domain.events',
        message={'event_id': '1'},
    )

    assert result is False
    connection.connect.assert_awaited_once()
    connection.close.assert_awaited_once()
