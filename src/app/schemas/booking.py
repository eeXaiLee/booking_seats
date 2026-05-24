"""Схемы данных для работы с бронированиями."""

from __future__ import annotations

from datetime import date, datetime, time
from enum import IntEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from app.schemas.types import Description

try:
    from app.schemas.cafe import CafeShortInfo
    from app.schemas.table import TableShortInfo
    from app.schemas.time_slot import TimeSlotShortInfo
    from app.schemas.user import UserShortInfo
except ImportError:

    class UserShortInfo(BaseModel):
        """Локальный fallback краткой схемы пользователя."""

        id: int
        username: str
        email: str | None = None
        phone: str | None = None
        tg_id: str | None = None

        model_config = ConfigDict(from_attributes=True, extra='forbid')

    class CafeShortInfo(BaseModel):
        """Локальный fallback краткой схемы кафе."""

        id: int
        name: str
        address: str
        phone: str
        description: str
        photo_id: UUID | None = None

        model_config = ConfigDict(from_attributes=True, extra='forbid')

    class TableShortInfo(BaseModel):
        """Локальный fallback краткой схемы стола."""

        id: int
        description: str
        seat_number: int

        model_config = ConfigDict(from_attributes=True, extra='forbid')

    class TimeSlotShortInfo(BaseModel):
        """Локальный fallback краткой схемы временного слота."""

        id: int
        start_time: time
        end_time: time
        description: str

        model_config = ConfigDict(from_attributes=True, extra='forbid')


from app.core.constants import (
    BOOKING_MIN_SLOTS_COUNT,
    BOOKING_MIN_TABLES_COUNT,
    GUEST_NUBMBER_MAX,
    GUEST_NUBMBER_MIN,
    STATUS_ACTIVE,
    STATUS_BOOK,
    STATUS_CANCEL,
)


# Может это в constants перенести?
class BookingStatus(IntEnum):
    """Статусы бронирования."""

    BOOKING = STATUS_BOOK
    CANCELED = STATUS_CANCEL
    ACTIVE = STATUS_ACTIVE


class BookingCreate(BaseModel):
    """Создание бронирования."""

    cafe_id: int
    tables_id: list[int] = Field(..., min_length=BOOKING_MIN_TABLES_COUNT)
    slots_id: list[int] = Field(..., min_length=BOOKING_MIN_SLOTS_COUNT)
    guest_number: PositiveInt = Field(
        ...,
        gt=GUEST_NUBMBER_MIN,
        lt=GUEST_NUBMBER_MAX,
    )
    note: Description | None
    status: BookingStatus
    booking_date: date

    model_config = ConfigDict(extra='forbid')


class BookingUpdate(BaseModel):
    """Обновление бронирования."""

    cafe_id: int | None = None
    tables_id: list[int] | None = Field(
        None,
        min_length=BOOKING_MIN_TABLES_COUNT,
    )
    slots_id: list[int] | None = Field(
        None,
        min_length=BOOKING_MIN_SLOTS_COUNT,
    )
    guest_number: PositiveInt | None = Field(
        None,
        gt=GUEST_NUBMBER_MIN,
        lt=GUEST_NUBMBER_MAX,
    )
    note: Description | None = None
    status: BookingStatus | None = None
    booking_date: date | None = None
    is_active: bool | None = None

    model_config = ConfigDict(extra='forbid')


class BookingInfo(BaseModel):
    """Полная информация о бронировании."""

    id: int
    user: UserShortInfo
    cafe: CafeShortInfo
    tables: list[TableShortInfo]
    slots: list[TimeSlotShortInfo]
    guest_number: int
    note: str | None = None
    status: BookingStatus
    booking_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra='forbid')
