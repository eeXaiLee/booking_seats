"""Регрессионные тесты временных слотов."""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.api.endpoints.time_slot import delete_time_slot
from app.crud.time_slot import TimeSlotCRUD
from app.schemas.time_slot import TimeSlotUpdate


def test_time_slot_update_allows_partial_is_active_patch() -> None:
    """PATCH только с is_active не должен валиться на validator времени."""
    result = TimeSlotUpdate.model_validate({'is_active': False})

    assert result.is_active is False
    assert result.start_time is None
    assert result.end_time is None


@pytest.mark.asyncio
async def test_time_slot_remove_rolls_back_on_integrity_error() -> None:
    """При FK-конфликте удаление должно делать rollback."""
    db = AsyncMock()
    db.delete = AsyncMock()
    db.commit = AsyncMock(
        side_effect=IntegrityError('stmt', 'params', Exception()),
    )
    db.rollback = AsyncMock()

    with pytest.raises(IntegrityError):
        await TimeSlotCRUD.remove(TimeSlotCRUD, db=db, db_obj=object())

    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_time_slot_returns_conflict_for_booked_slot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """API должен отдавать 409 вместо 500 при удалении занятого слота."""
    session = AsyncMock()
    session.rollback = AsyncMock()
    crud = AsyncMock()
    crud.remove.side_effect = IntegrityError('stmt', 'params', Exception())

    monkeypatch.setattr(
        'app.api.endpoints.time_slot.validate_cafe_id',
        AsyncMock(),
    )
    monkeypatch.setattr(
        'app.api.endpoints.time_slot.validate_time_slot_exists',
        AsyncMock(return_value=object()),
    )

    with pytest.raises(HTTPException) as exc_info:
        await delete_time_slot(
            session=session,
            time_slot_crud=crud,
            cafe_id=1,
            slot_id=4,
            _=object(),
        )

    assert exc_info.value.status_code == 409
    assert 'используется в бронированиях' in exc_info.value.detail
    session.rollback.assert_awaited_once()
