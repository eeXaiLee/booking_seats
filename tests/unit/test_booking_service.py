"""Unit-тесты для BookingService."""

import re
from datetime import date, datetime, timezone
from importlib import import_module
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.core.constants import OUTBOX_STATUS_PENDING
from app.schemas.events import EventType
from app.services.booking import BookingService, build_outbox_event


def _make_booking(
    booking_id: int = 1,
    user_id: int = 10,
    cafe_id: int = 2,
) -> MagicMock:
    """Создаёт mock бронирования."""
    booking = MagicMock()
    booking.id = booking_id
    booking.user_id = user_id
    booking.cafe_id = cafe_id
    booking.status = 0
    booking.booking_date = date(2026, 4, 1)
    booking.guest_number = 2
    booking.tables = []
    booking.slots = []
    return booking


class TestBuildOutboxEvent:
    """Тесты build_outbox_event."""

    def test_creates_outbox_event_with_correct_fields(self) -> None:
        """Проверка полей события."""
        booking = _make_booking()
        event = build_outbox_event(
            event_type=EventType.BOOKING_CREATED,
            booking=booking,
        )

        assert event.event_type == EventType.BOOKING_CREATED
        assert event.aggregate_type == 'booking'
        assert event.aggregate_id == booking.id
        assert event.event_version == 1
        assert event.status == OUTBOX_STATUS_PENDING
        assert event.payload['booking_id'] == booking.id
        assert event.payload['user_id'] == booking.user_id

    def test_event_id_is_uuid_string(self) -> None:
        """Проверка формата event_id."""
        booking = _make_booking()
        event = build_outbox_event(
            event_type=EventType.BOOKING_CREATED,
            booking=booking,
        )
        uuid_re = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        )
        assert uuid_re.match(event.event_id)

    def test_occurred_at_is_utc(self) -> None:
        """Проверка времени события."""
        before = datetime.now(timezone.utc)
        event = build_outbox_event(
            event_type=EventType.BOOKING_UPDATED,
            booking=_make_booking(),
        )
        after = datetime.now(timezone.utc)

        assert before <= event.occurred_at <= after

    def test_correlation_id_stored_in_payload(self) -> None:
        """Проверка correlation_id в payload."""
        event = build_outbox_event(
            event_type=EventType.BOOKING_CREATED,
            booking=_make_booking(),
            correlation_id='test-corr-id',
        )
        assert event.payload['correlation_id'] == 'test-corr-id'

    def test_correlation_id_default_dash(self) -> None:
        """Проверка default correlation_id."""
        event = build_outbox_event(
            event_type=EventType.BOOKING_CREATED,
            booking=_make_booking(),
        )
        assert event.payload['correlation_id'] == '-'

    def test_each_call_produces_unique_event_id(self) -> None:
        """Проверка уникальности event_id."""
        booking = _make_booking()
        e1 = build_outbox_event(
            EventType.BOOKING_CREATED, booking,
        )
        e2 = build_outbox_event(
            EventType.BOOKING_CREATED, booking,
        )
        assert e1.event_id != e2.event_id


class TestBookingServiceCreateBooking:
    """Тесты create_booking."""

    @pytest.fixture
    def booking_crud(self) -> AsyncMock:
        """Фикстура CRUD-слоя."""
        crud = AsyncMock()
        booking = _make_booking()
        crud.create.return_value = booking
        crud.get.return_value = booking
        return crud

    @pytest.fixture
    def session(self) -> AsyncMock:
        """Фикстура сессии БД."""
        s = AsyncMock()
        s.add = MagicMock()
        s.commit = AsyncMock()
        s.rollback = AsyncMock()
        return s

    @pytest.mark.asyncio
    async def test_creates_booking_and_outbox_event(
        self,
        booking_crud: AsyncMock,
        session: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Проверка создания брони и события."""
        delay_mock = MagicMock()
        outbox_module = import_module('celery_app.tasks.outbox')
        monkeypatch.setattr(
            outbox_module.publish_pending_outbox_events,
            'delay',
            delay_mock,
        )

        svc = BookingService(booking_crud=booking_crud)
        booking_in = MagicMock()

        await svc.create_booking(obj_in=booking_in, user_id=1, session=session)

        booking_crud.create.assert_awaited_once()
        session.add.assert_called_once()
        session.commit.assert_awaited_once()
        delay_mock.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_rollback_on_crud_failure(
        self,
        booking_crud: AsyncMock,
        session: AsyncMock,
    ) -> None:
        """Проверка отката при ошибке."""
        booking_crud.create.side_effect = SQLAlchemyError('db error')
        svc = BookingService(booking_crud=booking_crud)

        with pytest.raises(SQLAlchemyError):
            await svc.create_booking(
                obj_in=MagicMock(),
                user_id=1,
                session=session,
            )

        session.rollback.assert_awaited_once()
        session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_committed_booking(
        self,
        booking_crud: AsyncMock,
        session: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Проверка возврата брони."""
        outbox_module = import_module('celery_app.tasks.outbox')
        monkeypatch.setattr(
            outbox_module.publish_pending_outbox_events,
            'delay',
            MagicMock(),
        )

        expected = _make_booking(booking_id=99)
        booking_crud.create.return_value = _make_booking(booking_id=99)
        booking_crud.get.return_value = expected

        svc = BookingService(booking_crud=booking_crud)
        result = await svc.create_booking(
            obj_in=MagicMock(),
            user_id=1,
            session=session,
        )

        assert result is expected

    @pytest.mark.asyncio
    async def test_create_booking_does_not_fail_if_enqueue_fails(
        self,
        booking_crud: AsyncMock,
        session: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Сбой enqueue не должен ломать создание брони."""
        outbox_module = import_module('celery_app.tasks.outbox')
        delay_mock = MagicMock(side_effect=OSError('broker unavailable'))
        monkeypatch.setattr(
            outbox_module.publish_pending_outbox_events,
            'delay',
            delay_mock,
        )

        svc = BookingService(booking_crud=booking_crud)

        result = await svc.create_booking(
            obj_in=MagicMock(),
            user_id=1,
            session=session,
        )

        assert result is booking_crud.get.return_value
        session.commit.assert_awaited_once()
        session.rollback.assert_not_awaited()
