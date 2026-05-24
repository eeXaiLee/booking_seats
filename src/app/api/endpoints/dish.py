"""Модуль с эндпоинтами для работы с блюдами."""
from http import HTTPStatus
from typing import List, Optional

from dependency_injector.wiring import inject
from fastapi import APIRouter, Body, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import (
    AdminAndManagerDependency,
    AdminOnlyDependency,
    CRUDDishDependency,
    SessionDependency,
    UserDependency,
)
from app.schemas.dish import DishCreate, DishInfo, DishUpdate
from app.validators.dish import (
    validate_cafes_exist_for_dish,
    validate_dish_exists,
    validate_dish_update_permissions,
    validate_requested_show_all_for_dish,
)

router = APIRouter()


@router.get(
    '/',
    response_model=List[DishInfo],
    response_model_exclude_none=True,
    summary='Получить список блюд',
    description='Получить список блюд',
)
@inject
async def get_all_dishes(
    session: SessionDependency,
    dish_crud: CRUDDishDependency,
    current_user: UserDependency,
    show_all: bool = Query(
        False,
        description='Показывать все блюда или нет. По умолчанию активные',
    ),
    cafe_id: Optional[int] = Query(
        None,
        description='ID кафе, в котором показывать блюда',
    ),
) -> List[DishInfo]:
    """Получение списка блюд.

    Для администраторов и менеджеров - все блюда (с возможностью выбора),
    для пользователей - только активные.
    """
    only_active = not validate_requested_show_all_for_dish(
        current_user.role,
        show_all,
    )

    if cafe_id:
        dishes = await dish_crud.get_multi_by_cafe(
            session,
            cafe_id=cafe_id,
            only_active=only_active,
        )
    else:
        dishes = await dish_crud.get_multi(session)
        if only_active:
            dishes = [dish for dish in dishes if dish.is_active]

    return dishes


@router.post(
    '/',
    response_model=DishInfo,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    summary='Создать блюдо',
    description='Создать блюдо',
)
@inject
async def create_dish(
    session: SessionDependency,
    dish_crud: CRUDDishDependency,
    _: AdminAndManagerDependency,
    dish_in: DishCreate = Body(
        ...,
        openapi_examples={
            'default': {
                'summary': 'Пример создания блюда',
                'value': {
                    'name': 'Эльфийский лесной суп',
                    'description': (
                        'Легкий, ароматный суп с травами и овощами, '
                        'будто приготовленный на кухне Ривенделла'
                    ),
                    'photo_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                    'price': 150,
                    'cafes_id': [1],
                },
            },
        },
    ),
) -> DishInfo:
    """Создание нового блюда.

    Только для администраторов и менеджеров.
    """
    try:
        await validate_cafes_exist_for_dish(session, dish_in.cafes_id)

        return await dish_crud.create_with_cafes(session, obj_in=dish_in)
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Ошибка при создании блюда',
        ) from e


@router.get(
    '/{dish_id}',
    response_model=DishInfo,
    response_model_exclude_none=True,
    summary='Получить блюдо по id',
    description='Получить блюдо по id',
)
@inject
async def get_dish_by_id(
    dish_id: int,
    session: SessionDependency,
    dish_crud: CRUDDishDependency,
    current_user: UserDependency,
) -> DishInfo:
    """Получение информации о блюде по его ID.

    Для администраторов и менеджеров - все блюда,
    для пользователей - только активные.
    """
    only_active = not validate_requested_show_all_for_dish(
        current_user.role,
        True,
    )

    dish = await validate_dish_exists(
        session,
        dish_crud,
        dish_id,
        only_active=only_active,
    )

    if not current_user.is_administrator and not current_user.is_manager:
        if not dish.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Доступ запрещен',
            )

    return dish


@router.patch(
    '/{dish_id}',
    response_model=DishInfo,
    response_model_exclude_none=True,
    summary='Обновить блюдо',
    description='Обновить блюдо',
)
@inject
async def update_dish(
    dish_id: int,
    dish_in: DishUpdate,
    session: SessionDependency,
    dish_crud: CRUDDishDependency,
    current_user: AdminAndManagerDependency,
) -> DishInfo:
    """Обновление информации о блюде по его ID.

    Только для администраторов и менеджеров.
    """
    try:
        dish = await validate_dish_exists(
            session,
            dish_crud,
            dish_id,
            only_active=False,
        )

        validate_dish_update_permissions(current_user.role, dish_in)

        if dish_in.cafes_id is not None:
            await validate_cafes_exist_for_dish(session, dish_in.cafes_id)

        return await dish_crud.update_with_cafes(
            db=session,
            db_obj=dish,
            obj_in=dish_in,
        )
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Ошибка при обновлении блюда',
        ) from e


@router.delete(
    '/{dish_id}',
    response_model=DishInfo,
    response_model_exclude_none=True,
    summary='Деактивировать блюдо',
    description='Деактивировать блюдо. Доступно только администраторам.',
)
@inject
async def delete_dish(
    dish_id: int,
    session: SessionDependency,
    _: AdminOnlyDependency,
    dish_crud: CRUDDishDependency,
) -> DishInfo:
    """Деактивация блюда через is_active (мягкое удаление)."""
    try:
        dish = await validate_dish_exists(
            session,
            dish_crud,
            dish_id,
            only_active=False,
        )

        return await dish_crud.update(
            db=session,
            db_obj=dish,
            obj_in=DishUpdate(is_active=False),
        )
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Ошибка при деактивации блюда',
        ) from e
