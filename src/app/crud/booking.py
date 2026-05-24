"""CRUD для модели Booking."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import (
    BOOKING_CAFE_MISMATCH_ERROR,
    BOOKING_CANNOT_UPDATE_ACTIVE_ERROR,
    BOOKING_CANNOT_UPDATE_PAST_ERROR,
    BOOKING_CREATION_ERROR,
    BOOKING_PAST_DATE_ERROR,
    BOOKING_SLOTS_NOT_FOUND_ERROR,
    BOOKING_TABLES_BUSY_ERROR,
    BOOKING_TABLES_NOT_FOUND_ERROR,
    BOOKING_UPDATE_ERROR,
    BOOKING_USER_CONFLICT_ERROR,
)
from app.core.logging import log_audit_event
from app.schemas.booking import BookingStatus

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.schemas.booking import BookingCreate, BookingUpdate


class BookingCRUD:
    """CRUD для бронирований."""

    async def _get_tables(
        self,
        tables_id: list[int],
        session: AsyncSession,
    ) -> list[Any]:
        """Получение столов по списку идентификаторов."""
        from app.models.table import Table

        tables = await session.execute(
            select(Table).where(Table.id.in_(tables_id)),
        )
        return list(tables.scalars().all())

    async def _get_slots(
        self,
        slots_id: list[int],
        session: AsyncSession,
    ) -> list[Any]:
        """Получение временных слотов по списку идентификаторов."""
        from app.models.time_slot import TimeSlot

        slots = await session.execute(
            select(TimeSlot).where(TimeSlot.id.in_(slots_id)),
        )
        return list(slots.scalars().all())

    async def _validate_booking_date(
        self,
        booking_date: date,
    ) -> None:
        """Проверка, что бронирование создается не на прошедшую дату."""
        if booking_date < date.today():
            raise ValueError(BOOKING_PAST_DATE_ERROR)

    async def _validate_tables_and_slots(
        self,
        cafe_id: int,
        tables_id: list[int],
        slots_id: list[int],
        session: AsyncSession,
    ) -> tuple[list[Any], list[Any]]:
        """Проверка, что столы и слоты существуют и принадлежат кафе."""
        tables = await self._get_tables(tables_id, session)
        slots = await self._get_slots(slots_id, session)

        if len(tables) != len(set(tables_id)):
            raise ValueError(BOOKING_TABLES_NOT_FOUND_ERROR)
        if len(slots) != len(set(slots_id)):
            raise ValueError(BOOKING_SLOTS_NOT_FOUND_ERROR)

        if any(table.cafe_id != cafe_id for table in tables):
            raise ValueError(BOOKING_CAFE_MISMATCH_ERROR)
        if any(slot.cafe_id != cafe_id for slot in slots):
            raise ValueError(BOOKING_CAFE_MISMATCH_ERROR)

        return tables, slots

    async def _check_tables_available(
        self,
        booking_date: date,
        tables_id: list[int],
        slots_id: list[int],
        session: AsyncSession,
        exclude_booking_id: int | None = None,
    ) -> None:
        """Проверка, что столы свободны в выбранные слоты."""
        from app.models.booking import Booking
        from app.models.table import Table
        from app.models.time_slot import TimeSlot

        stmt = (
            select(Booking)
            .join(Booking.tables)
            .join(Booking.slots)
            .where(Booking.booking_date == booking_date)
            .where(Booking.is_active.is_(True))
            .where(Booking.status != BookingStatus.CANCELED)
            .where(Table.id.in_(tables_id))
            .where(TimeSlot.id.in_(slots_id))
        )

        if exclude_booking_id is not None:
            stmt = stmt.where(Booking.id != exclude_booking_id)

        conflicts = await session.execute(stmt.distinct())
        if conflicts.scalars().first() is not None:
            raise ValueError(
                BOOKING_TABLES_BUSY_ERROR,
            )

    async def _check_user_booking_conflicts(
        self,
        user_id: int,
        booking_date: date,
        slots_id: list[int],
        session: AsyncSession,
        exclude_booking_id: int | None = None,
    ) -> None:
        """Проверка, что бронирования пользователя не пересекаются."""
        from app.models.booking import Booking
        from app.models.time_slot import TimeSlot

        stmt = (
            select(Booking)
            .join(Booking.slots)
            .where(Booking.user_id == user_id)
            .where(Booking.booking_date == booking_date)
            .where(Booking.is_active.is_(True))
            .where(Booking.status != BookingStatus.CANCELED)
            .where(TimeSlot.id.in_(slots_id))
        )

        if exclude_booking_id is not None:
            stmt = stmt.where(Booking.id != exclude_booking_id)

        conflicts = await session.execute(stmt.distinct())
        if conflicts.scalars().first() is not None:
            raise ValueError(
                BOOKING_USER_CONFLICT_ERROR,
            )

    async def _validate_booking_constraints(
        self,
        user_id: int,
        cafe_id: int,
        tables_id: list[int],
        slots_id: list[int],
        booking_date: date,
        session: AsyncSession,
        exclude_booking_id: int | None = None,
    ) -> tuple[list[Any], list[Any]]:
        """Комплексная валидация данных бронирования."""
        await self._validate_booking_date(booking_date)
        tables, slots = await self._validate_tables_and_slots(
            cafe_id,
            tables_id,
            slots_id,
            session,
        )
        await self._check_tables_available(
            booking_date,
            tables_id,
            slots_id,
            session,
            exclude_booking_id=exclude_booking_id,
        )
        await self._check_user_booking_conflicts(
            user_id,
            booking_date,
            slots_id,
            session,
            exclude_booking_id=exclude_booking_id,
        )
        return tables, slots

    async def _validate_booking_for_update(
        self,
        booking: Booking,
    ) -> None:
        """Проверка, что бронирование можно изменять."""
        if booking.booking_date < date.today():
            raise ValueError(BOOKING_CANNOT_UPDATE_PAST_ERROR)
        if booking.status == BookingStatus.ACTIVE:
            raise ValueError(
                BOOKING_CANNOT_UPDATE_ACTIVE_ERROR,
            )

    async def get(
        self,
        obj_id: int,
        session: AsyncSession,
    ) -> Booking | None:
        """Получение бронирования по идентификатору."""
        from app.models.booking import Booking

        stmt = (
            select(Booking)
            .options(
                selectinload(Booking.user),
                selectinload(Booking.cafe),
                selectinload(Booking.tables),
                selectinload(Booking.slots),
            )
            .where(Booking.id == obj_id)
        )
        booking = await session.execute(stmt)
        return booking.scalars().first()

    async def get_multi(
        self,
        session: AsyncSession,
        show_all: bool = False,
        cafe_id: int | None = None,
        user_id: int | None = None,
    ) -> list[Booking]:
        """Получение списка бронирований с фильтрами."""
        from app.models.booking import Booking

        stmt = select(Booking).options(
            selectinload(Booking.user),
            selectinload(Booking.cafe),
            selectinload(Booking.tables),
            selectinload(Booking.slots),
        )

        if not show_all:
            stmt = stmt.where(Booking.is_active.is_(True))
        if cafe_id is not None:
            stmt = stmt.where(Booking.cafe_id == cafe_id)
        if user_id is not None:
            stmt = stmt.where(Booking.user_id == user_id)

        bookings = await session.execute(stmt)
        return list(bookings.scalars().all())

    async def create(
        self,
        obj_in: BookingCreate,
        user_id: int,
        session: AsyncSession,
    ) -> Booking:
        """Создание бронирования."""
        from app.models.booking import Booking

        booking_data = obj_in.model_dump()
        tables_id = booking_data.pop('tables_id')
        slots_id = booking_data.pop('slots_id')

        tables, slots = await self._validate_booking_constraints(
            user_id=user_id,
            cafe_id=booking_data['cafe_id'],
            tables_id=tables_id,
            slots_id=slots_id,
            booking_date=booking_data['booking_date'],
            session=session,
        )

        booking = Booking(
            **booking_data,
            user_id=user_id,
        )
        booking.tables = tables
        booking.slots = slots

        session.add(booking)
        await session.flush()

        created_booking = await self.get(booking.id, session)
        if created_booking is None:
            raise ValueError(BOOKING_CREATION_ERROR)
        log_audit_event(
            event='Создана запись в таблице booking',
            details={
                'id': created_booking.id,
                'parameters': booking_data
                | {
                    'user_id': user_id,
                    'tables_id': tables_id,
                    'slots_id': slots_id,
                },
            },
        )
        return created_booking

    async def update(
        self,
        booking: Booking,
        obj_in: BookingUpdate,
        session: AsyncSession,
    ) -> Booking:
        """Обновление бронирования."""
        update_fields = obj_in.model_dump(exclude_unset=True)
        await self._validate_booking_for_update(booking)

        target_cafe_id = update_fields.get('cafe_id', booking.cafe_id)
        target_tables_id = update_fields.get(
            'tables_id',
            [table.id for table in booking.tables],
        )
        target_slots_id = update_fields.get(
            'slots_id',
            [slot.id for slot in booking.slots],
        )
        target_booking_date = update_fields.get(
            'booking_date',
            booking.booking_date,
        )

        tables, slots = await self._validate_booking_constraints(
            user_id=booking.user_id,
            cafe_id=target_cafe_id,
            tables_id=target_tables_id,
            slots_id=target_slots_id,
            booking_date=target_booking_date,
            session=session,
            exclude_booking_id=booking.id,
        )

        for field, value in update_fields.items():
            if field not in {'tables_id', 'slots_id'}:
                setattr(booking, field, value)

        booking.tables = tables
        booking.slots = slots

        session.add(booking)
        await session.flush()

        updated_booking = await self.get(booking.id, session)
        if updated_booking is None:
            raise ValueError(BOOKING_UPDATE_ERROR)
        log_audit_event(
            event='Обновлена запись в таблице booking',
            details={
                'id': updated_booking.id,
                'parameters': update_fields,
            },
        )
        return updated_booking
