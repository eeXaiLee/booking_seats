from http import HTTPStatus
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import time_slot_crud
from app.models import TimeSlot


async def validate_time_slot_exists(
    cafe_id: int,
    slot_id: int,
    session: AsyncSession,
) -> TimeSlot:
    """Валидация существования временного слота."""
    time_slot = await time_slot_crud.get_by_cafe_id(
        cafe_id=cafe_id,
        slot_id=slot_id,
        session=session,
    )
    if not time_slot:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Временной слот не найден',
        )
    return time_slot


def validate_time_slot_cafe_id_match(
    path_cafe_id: int,
    body_cafe_id: int | None,
) -> None:
    """Валидация path и body по cafe_id."""
    if body_cafe_id is None:
        return
    if body_cafe_id != path_cafe_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='cafe_id в пути и теле запроса должны совпадать.',
        )


async def validate_time_slot_intersections(**kwargs: Any) -> None:
    """Валидация пересечения полей времени."""
    slots = await time_slot_crud.get_time_slots_at_the_same_time(
        cafe_id=kwargs['cafe_id'],
        start_time=kwargs['start_time'],
        end_time=kwargs['end_time'],
        db=kwargs['db'],
        slot_id=kwargs.get('slot_id'),
    )
    if slots:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=(
                f'Время слота пересекается с другими слотами: {str(slots)}'
            ),
        )
