"""Схемы данных для работы с доменными событиями."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class EventType(StrEnum):
    """Типы доменных событий приложения."""

    BOOKING_CREATED = 'booking.created'
    BOOKING_UPDATED = 'booking.updated'
    BOOKING_CANCELED = 'booking.canceled'


class OutboxEventCreate(BaseModel):
    """Контракт outbox-события для записи и последующей публикации."""

    event_id: str
    event_type: EventType
    event_version: int
    occurred_at: datetime
    aggregate_type: str
    aggregate_id: int
    payload: dict[str, Any]

    model_config = ConfigDict(extra='forbid', use_enum_values=True)
