"""Сервис для управления бронированиями.

Содержит бизнес-логику создания и обновления бронирований,
а также публикации доменных событий через Outbox.
Обеспечивает атомарность операций и согласованность данных.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from kombu.exceptions import KombuError
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import OUTBOX_STATUS_PENDING
from app.crud import BookingCRUD
from app.models.booking import Booking
from app.models.outbox_event import OutboxEvent
from app.schemas.booking import BookingCreate, BookingUpdate
from app.schemas.events import EventType, OutboxEventCreate
from celery_app.tasks.outbox import publish_pending_outbox_events


def build_outbox_event(
    event_type: EventType,
    booking: Booking,
    correlation_id: str | None = None,
) -> OutboxEvent:
    """Собрать outbox-событие для бронирования."""
    payload = OutboxEventCreate(
        event_id=str(uuid4()),
        event_type=event_type,
        event_version=1,
        occurred_at=datetime.now(timezone.utc),
        aggregate_type='booking',
        aggregate_id=booking.id,
        payload={
            'booking_id': booking.id,
            'user_id': booking.user_id,
            'cafe_id': booking.cafe_id,
            'status': int(booking.status),
            'booking_date': booking.booking_date.isoformat(),
            'guest_number': booking.guest_number,
            'tables_id': [table.id for table in booking.tables],
            'slots_id': [slot.id for slot in booking.slots],
            'correlation_id': correlation_id or '-',
        },
    )
    return OutboxEvent(
        **payload.model_dump(),
        status=OUTBOX_STATUS_PENDING,
    )


class BookingService:
    """Сервисный слой для сценариев работы с бронированиями."""

    def __init__(self, booking_crud: BookingCRUD) -> None:
        """Инициализировать сервис с CRUD-слоем для бронирований."""
        self.booking_crud = booking_crud

    @staticmethod
    def _enqueue_outbox_publish(
        booking_id: int,
        correlation_id: str | None = None,
    ) -> None:
        """Попросить Celery немедленно опубликовать pending-события."""
        try:
            logger.info(
                'booking.outbox enqueue b={b} r={r}',
                b=booking_id,
                r=correlation_id or '-',
            )
            publish_pending_outbox_events.delay()
        except (KombuError, OSError):
            logger.exception(
                'booking.outbox enqueue fail b={b} r={r}',
                b=booking_id,
                r=correlation_id or '-',
            )

    async def create_booking(
        self,
        obj_in: BookingCreate,
        user_id: int,
        session: AsyncSession,
        correlation_id: str | None = None,
    ) -> Booking:
        """Создать бронирование и поставить уведомление в очередь."""
        try:
            booking = await self.booking_crud.create(
                obj_in=obj_in,
                user_id=user_id,
                session=session,
            )
            outbox_event = build_outbox_event(
                event_type=EventType.BOOKING_CREATED,
                booking=booking,
                correlation_id=correlation_id,
            )
            session.add(outbox_event)
            logger.info(
                'booking.create prepared b={b} e={e} r={r}',
                b=booking.id,
                e=outbox_event.event_id,
                r=correlation_id or '-',
            )
            await session.commit()
            logger.info(
                'booking.create ok b={b} e={e} r={r}',
                b=booking.id,
                e=outbox_event.event_id,
                r=correlation_id or '-',
            )
        except (SQLAlchemyError, ValueError):
            await session.rollback()
            raise

        self._enqueue_outbox_publish(
            booking_id=booking.id,
            correlation_id=correlation_id,
        )

        committed_booking = await self.booking_crud.get(booking.id, session)
        if committed_booking is None:
            raise ValueError('Не удалось получить созданное бронирование')
        return committed_booking

    async def update_booking(
        self,
        booking: Booking,
        obj_in: BookingUpdate,
        session: AsyncSession,
        correlation_id: str | None = None,
    ) -> Booking:
        """Обновить бронирование через CRUD-слой."""
        try:
            updated_booking = await self.booking_crud.update(
                booking=booking,
                obj_in=obj_in,
                session=session,
            )
            outbox_event = build_outbox_event(
                event_type=EventType.BOOKING_UPDATED,
                booking=updated_booking,
                correlation_id=correlation_id,
            )
            session.add(outbox_event)
            logger.info(
                'booking.update prepared b={b} e={e} r={r}',
                b=updated_booking.id,
                e=outbox_event.event_id,
                r=correlation_id or '-',
            )
            await session.commit()
            logger.info(
                'booking.update ok b={b} e={e} r={r}',
                b=updated_booking.id,
                e=outbox_event.event_id,
                r=correlation_id or '-',
            )
        except (SQLAlchemyError, ValueError):
            await session.rollback()
            raise

        self._enqueue_outbox_publish(
            booking_id=updated_booking.id,
            correlation_id=correlation_id,
        )

        committed_booking = await self.booking_crud.get(
            updated_booking.id, session,
        )
        if committed_booking is None:
            raise ValueError('Не удалось получить обновленное бронирование')
        return committed_booking
