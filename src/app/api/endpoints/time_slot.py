"""Модуль с эндпоинтами для работы с временными слотами в кафе."""

from http import HTTPStatus

from dependency_injector.wiring import inject
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import (
    AdminAndManagerDependency,
    CRUDTimeSlotDependency,
    SessionDependency,
    UserDependency,
)
from app.models import TimeSlot
from app.schemas import TimeSlotCreate, TimeSlotInfo, TimeSlotUpdate
from app.validators.cafe import validate_cafe_id
from app.validators.time_slot import (
    validate_time_slot_cafe_id_match,
    validate_time_slot_exists,
    validate_time_slot_intersections,
)

router = APIRouter()


@router.get(
    '/',
    response_model=list[TimeSlotInfo],
    summary='Список временных слотов в кафе',
    description=(
        'Получение списка доступных для бронирования временных слотов в кафе.'
        'Для администраторов и менеджеров — все слоты (с возможностью выбора),'
        'для пользователей — только активные.'
    ),
)
@inject
async def get_all_time_slots(
    session: SessionDependency,
    time_slot_crud: CRUDTimeSlotDependency,
    cafe_id: int,
    _: UserDependency,
    show_all: bool = Query(
        default=False,
        description='Показывать все временные слоты, включая неактивные.',
    ),
) -> list[TimeSlot]:
    """Получение всех временных слотов в кафе."""
    return await time_slot_crud.get_multi_by_cafe_id(
        cafe_id=cafe_id,
        show_all=show_all,
        session=session,
    )


@router.post(
    '/',
    response_model=TimeSlotInfo,
    summary='Новый временной слот в кафе',
    description=(
        'Создание нового временного слота в кафе. '
        'Только для администраторов и менеджеров.'
    ),
)
@inject
async def create_time_slot(
    session: SessionDependency,
    time_slot: TimeSlotCreate,
    time_slot_crud: CRUDTimeSlotDependency,
    cafe_id: int,
    _: AdminAndManagerDependency,
) -> TimeSlot:
    """Создание временного слота."""
    try:
        validate_time_slot_cafe_id_match(
            path_cafe_id=cafe_id,
            body_cafe_id=time_slot.cafe_id,
        )
        await validate_cafe_id(
            cafe_id=cafe_id,
            session=session,
        )
        await validate_time_slot_intersections(
            **time_slot.model_dump(),
            db=session,
        )
        return await time_slot_crud.create(
            db=session,
            obj_in=time_slot,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    '/{slot_id}',
    response_model=TimeSlotInfo,
    summary='Информация о временном слоте в кафе по его ID',
    description=(
        'Получение информации о временном слоте в кафе по его ID. '
        'Для администраторов и менеджеров — любой слот, '
        'для пользователей — только активный.'
    ),
)
@inject
async def get_time_slot(
    session: SessionDependency,
    time_slot_crud: CRUDTimeSlotDependency,
    cafe_id: int,
    slot_id: int,
    _: UserDependency,
) -> TimeSlot:
    """Получение временного слота."""
    await validate_cafe_id(
        cafe_id=cafe_id,
        session=session,
    )
    await validate_time_slot_exists(
        cafe_id=cafe_id,
        slot_id=slot_id,
        session=session,
    )
    return await time_slot_crud.get_by_cafe_id(
        cafe_id=cafe_id,
        slot_id=slot_id,
        session=session,
    )


@router.patch(
    '/{slot_id}',
    response_model=TimeSlotInfo,
    summary='Обновление информации о временном слоте в кафе по его ID',
    description=(
        'Обновление информации о временном слоте в кафе по его ID. '
        'Только для администраторов и менеджеров.'
    ),
)
@inject
async def update_time_slot(
    session: SessionDependency,
    time_slot: TimeSlotUpdate,
    time_slot_crud: CRUDTimeSlotDependency,
    cafe_id: int,
    slot_id: int,
    _: AdminAndManagerDependency,
) -> TimeSlot:
    """Обновление временного слота."""
    try:
        validate_time_slot_cafe_id_match(
            path_cafe_id=cafe_id,
            body_cafe_id=time_slot.cafe_id,
        )
        await validate_cafe_id(
            cafe_id=cafe_id,
            session=session,
        )
        slot_being_updated = await validate_time_slot_exists(
            cafe_id=cafe_id,
            slot_id=slot_id,
            session=session,
        )
        await validate_time_slot_intersections(
            cafe_id=time_slot.cafe_id or slot_being_updated.cafe_id,
            start_time=time_slot.start_time or slot_being_updated.start_time,
            end_time=time_slot.end_time or slot_being_updated.end_time,
            slot_id=slot_id,
            db=session,
        )
        return await time_slot_crud.update(
            db=session,
            db_obj=slot_being_updated,
            obj_in=time_slot,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.delete(
    '/{slot_id}',
    status_code=204,
    summary='Удалить временной слот',
    description='Удаляет временной слот кафе.',
)
@inject
async def delete_time_slot(
    session: SessionDependency,
    time_slot_crud: CRUDTimeSlotDependency,
    cafe_id: int,
    slot_id: int,
    _: AdminAndManagerDependency,
) -> None:
    """Удаление временного слота."""
    try:
        await validate_cafe_id(
            cafe_id=cafe_id,
            session=session,
        )
        slot_to_delete = await validate_time_slot_exists(
            cafe_id=cafe_id,
            slot_id=slot_id,
            session=session,
        )
        await time_slot_crud.remove(
            db=session,
            db_obj=slot_to_delete,
        )
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=(
                'Нельзя удалить временной слот, '
                'он используется в бронированиях.'
            ),
        ) from exc
