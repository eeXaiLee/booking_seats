"""Тесты схем событий."""

from typing import Any, Dict

import pytest
from pydantic import ValidationError

from app.schemas.events import EventType, OutboxEventCreate


class TestEventType:
    """Тесты EventType."""

    def test_booking_created_value(self) -> None:
        """Проверка BOOKING_CREATED."""
        assert EventType.BOOKING_CREATED == 'booking.created'

    def test_booking_updated_value(self) -> None:
        """Проверка BOOKING_UPDATED."""
        assert EventType.BOOKING_UPDATED == 'booking.updated'

    def test_booking_canceled_value(self) -> None:
        """Проверка BOOKING_CANCELED."""
        assert EventType.BOOKING_CANCELED == 'booking.canceled'

    def test_invalid_event_type_raises(self) -> None:
        """Проверка ошибки на невалидный тип события."""
        with pytest.raises(ValidationError):
            OutboxEventCreate(
                event_id='00000000-0000-0000-0000-000000000001',
                event_type='booking.unknown',
                event_version=1,
                occurred_at='2026-01-01T00:00:00+00:00',
                aggregate_type='booking',
                aggregate_id=1,
                payload={'booking_id': 1},
            )


class TestOutboxEventCreate:
    """Тесты OutboxEventCreate."""

    def _valid_payload(self, **overrides: Dict[str, Any]) -> dict:
        """Возвращает валидные данные события.

        Args:
            overrides: Переопределения полей.

        Returns:
            Словарь с данными события.

        """
        base = {
            'event_id': '00000000-0000-0000-0000-000000000001',
            'event_type': EventType.BOOKING_CREATED,
            'event_version': 1,
            'occurred_at': '2026-01-01T00:00:00+00:00',
            'aggregate_type': 'booking',
            'aggregate_id': 1,
            'payload': {'booking_id': 1},
        }
        base.update(overrides)
        return base

    def test_valid_creates_instance(self) -> None:
        """Проверка создания валидного экземпляра."""
        event = OutboxEventCreate(**self._valid_payload())
        assert event.event_type == 'booking.created'
        assert event.aggregate_type == 'booking'
        assert event.event_version == 1

    def test_extra_fields_forbidden(self) -> None:
        """Проверка запрета лишних полей."""
        with pytest.raises(ValidationError):
            OutboxEventCreate(**self._valid_payload(unexpected_field='x'))

    def test_use_enum_values_stores_string(self) -> None:
        """Проверка: enum сохраняется как строка."""
        event = OutboxEventCreate(**self._valid_payload())
        dumped = event.model_dump()
        assert isinstance(dumped['event_type'], str)
        assert dumped['event_type'] == 'booking.created'

    def test_missing_required_field_raises(self) -> None:
        """Проверка ошибки при отсутствии обязательного поля."""
        payload = self._valid_payload()
        del payload['aggregate_id']
        with pytest.raises(ValidationError):
            OutboxEventCreate(**payload)

    def test_payload_accepts_arbitrary_keys(self) -> None:
        """Проверка: payload принимает любые ключи."""
        event = OutboxEventCreate(
            **self._valid_payload(
                payload={
                    'booking_id': 42,
                    'cafe_id': 5,
                    'correlation_id': 'abc',
                },
            ),
        )
        assert event.payload['correlation_id'] == 'abc'
