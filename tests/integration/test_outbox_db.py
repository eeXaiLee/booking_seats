"""Интеграционные тесты: create booking -> outbox запись в БД.

Запускаются только при наличии переменной окружения TEST_DATABASE_URL,
чтобы не ломать CI без отдельной тестовой базы.
"""

import os
from datetime import date
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from app.crud.booking import BookingCRUD
from app.models.cafe import Cafe
from app.models.outbox_event import OutboxEvent
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingStatus
from app.services.booking import BookingService

pytestmark = pytest.mark.skipif(
    not os.getenv('TEST_DATABASE_URL'),
    reason='TEST_DATABASE_URL не задан, интеграционные тесты пропущены',
)

booking_crud = BookingCRUD()

DATABASE_URL = os.getenv('TEST_DATABASE_URL', '')


@pytest.fixture(name='db_engine', scope='function')
def db_engine_fixture() -> AsyncEngine:
    """Фикстура движка БД."""
    return create_async_engine(DATABASE_URL, echo=False)


@pytest_asyncio.fixture(name='session')
async def session_fixture(
    db_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Фикстура асинхронной сессии БД."""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with async_session() as sess:
        # Начинаем транзакцию
        tx = await sess.begin()
        try:
            yield sess
        finally:
            # Откатываем только если транзакция ещё открыта
            if tx.is_active:
                await tx.rollback()
            await sess.close()


@pytest.mark.asyncio
async def test_outbox_event_persisted_on_create(session: AsyncSession) -> None:
    """После create_booking в outbox_event должна появиться pending запись."""
    # Создаём кафе
    cafe = Cafe(
        name="Test Cafe",
        address="Test Address",
        phone="+79991234567",
        description="Test description",
        photo_id="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        is_active=True,
    )
    session.add(cafe)
    await session.flush()

    user = User(
        username="testuser",
        password="fakehashedpassword",
        email="testuser@example.com",
        phone="+79991234567",
        is_active=True,
    )
    session.add(user)
    await session.flush()

    with patch.object(
        BookingCRUD,
        '_validate_booking_constraints',
        new_callable=AsyncMock,
    ) as mock_validate:
        mock_validate.return_value = ([], [])

        svc = BookingService(booking_crud=booking_crud)

        obj_in = BookingCreate(
            cafe_id=cafe.id,
            tables_id=[101, 102],
            slots_id=[201, 202],
            guest_number=2,
            note="Тестовое бронирование",
            status=BookingStatus.BOOKING,
            booking_date=date(2026, 4, 1),
        )

        await svc.create_booking(obj_in=obj_in, user_id=1, session=session)

        result = await session.execute(
            select(OutboxEvent).where(OutboxEvent.aggregate_type == 'booking'),
        )
        events = result.scalars().all()
        assert len(events) >= 1
        assert events[0].status == 'pending'


@pytest.mark.asyncio
async def test_outbox_event_schema_matches_db(session: AsyncSession) -> None:
    """Поля модели OutboxEvent совпадают с колонками таблицы в БД."""
    result = await session.execute(
        text(
            'select column_name from information_schema.columns '
            "where table_name = 'outbox_event' order by ordinal_position",
        ),
    )
    columns = {row[0] for row in result.fetchall()}
    expected = {
        'id',
        'event_id',
        'event_type',
        'event_version',
        'occurred_at',
        'aggregate_type',
        'aggregate_id',
        'payload',
        'status',
        'error_message',
        'published_at',
        'created_at',
    }
    assert expected == columns


@pytest.mark.asyncio
async def test_processed_event_schema_matches_db(
    session: AsyncSession,
) -> None:
    """Поля модели ProcessedEvent совпадают с колонками таблицы в БД."""
    result = await session.execute(
        text(
            'select column_name from information_schema.columns '
            "where table_name = 'processed_event' order by ordinal_position",
        ),
    )
    columns = {row[0] for row in result.fetchall()}
    expected = {'id', 'event_id', 'event_type', 'processed_at'}
    assert expected == columns
