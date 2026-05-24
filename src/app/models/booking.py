"""Модель бронирования и его связь со столами и временными слотами."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import (
    NOTE_MAX_LENGTH,
)
from app.core.db import Base, CommonMixin
from app.schemas.booking import BookingStatus
from app.schemas.types import validate_description
from app.validators.orm_models_validator import create_validator_mixin

BookingValidatorMixin = create_validator_mixin({
    'note': validate_description,
})


class Booking(CommonMixin, BookingValidatorMixin, Base):
    """Бронирование пользователя."""

    # __tablename__ = 'booking', у нас в app.core.db Base
    # есть определение tablename

    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id'),
        nullable=False,
    )
    cafe_id: Mapped[int] = mapped_column(
        ForeignKey('cafe.id'),
        nullable=False,
    )
    guest_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(
        String(NOTE_MAX_LENGTH),
        nullable=True,
    )
    status: Mapped[int] = mapped_column(
        Integer,
        default=BookingStatus.BOOKING,
        nullable=False,
    )
    booking_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    user = relationship('User')
    cafe = relationship('Cafe')
    tables = relationship(
        'Table',
        secondary='booking_table',
    )
    slots = relationship(
        'TimeSlot',
        secondary='booking_slot',
    )

    def __repr__(self) -> str:
        return f'Бронирование {self.id} пользователя {self.user_id}'


class BookingTable(Base):
    """Связь бронирования и стола."""

    __tablename__ = 'booking_table'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    booking_id: Mapped[int] = mapped_column(
        ForeignKey('booking.id'),
        nullable=False,
    )
    table_id: Mapped[int] = mapped_column(
        ForeignKey('table.id'),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f'Связь бронирования {self.booking_id} и стола {self.table_id}'


class BookingSlot(Base):
    """Связь бронирования и временного слота."""

    __tablename__ = 'booking_slot'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    booking_id: Mapped[int] = mapped_column(
        ForeignKey('booking.id'),
        nullable=False,
    )
    slot_id: Mapped[int] = mapped_column(
        ForeignKey('time_slot.id'),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f'Связь бронирования {self.booking_id} и слота {self.slot_id}'
