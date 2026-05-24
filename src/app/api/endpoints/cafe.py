"""Модуль с эндпоинтами для работы с кафе."""

from http import HTTPStatus

from dependency_injector.wiring import inject
from fastapi import APIRouter

from app.api.dependencies import (
    AdminAndManagerDependency,
    AdminOnlyDependency,
    CRUDCafeDependency,
    CafeServiceDependency,
    SessionDependency,
    UserDependency,
)
from app.models import Cafe
from app.schemas import CafeCreate, CafeInfo, CafeUpdate
from app.validators.cafe import (
    validate_cafe_id_with_relations,
    validate_cafe_phone_is_available,
    validate_cafe_update_permissions,
    validate_last_manager_not_removed,
    validate_managers_are_allowed,
    validate_requested_show_all,
)

router = APIRouter()


@router.get(
    '/',
    response_model=list[CafeInfo],
    response_model_exclude_none=True,
    summary='Получить список кафе',
    description='Получить список кафе. Доступно авторизованным пользователям.',
)
@inject
async def get_cafes(
    session: SessionDependency,
    cafe_crud: CRUDCafeDependency,
    current_user: UserDependency,
    show_all: bool = False,
) -> list[Cafe]:
    """Получение списка кафе."""
    return await cafe_crud.get_multi(
        db=session,
        show_all=validate_requested_show_all(
            user=current_user,
            show_all=show_all,
        ),
    )


@router.post(
    '/',
    response_model=CafeInfo,
    response_model_exclude_none=True,
    status_code=HTTPStatus.CREATED,
    summary='Создать кафе',
    description='Создать кафе. Доступно только администраторам.',
)
@inject
async def create_cafe(
    cafe_in: CafeCreate,
    session: SessionDependency,
    cafe_crud: CRUDCafeDependency,
    _: AdminOnlyDependency,
) -> Cafe:
    """Создание кафе."""
    await validate_cafe_phone_is_available(
        session=session,
        phone=cafe_in.phone,
    )
    await validate_managers_are_allowed(
        session=session,
        managers_id=cafe_in.managers_id,
    )

    return await cafe_crud.create(
        db=session,
        obj_in=cafe_in,
    )


@router.get(
    '/{cafe_id}',
    response_model=CafeInfo,
    response_model_exclude_none=True,
    summary='Получить кафе по id',
    description='Получить кафе по id. Доступно авторизованным пользователям.',
)
@inject
async def get_cafe(
    cafe_id: int,
    session: SessionDependency,
    cafe_crud: CRUDCafeDependency,
    current_user: UserDependency,
    show_all: bool = False,
) -> Cafe:
    """Получение одного кафе."""
    return await validate_cafe_id_with_relations(
        cafe_id=cafe_id,
        session=session,
        cafe_crud=cafe_crud,
        show_all=validate_requested_show_all(
            user=current_user,
            show_all=show_all,
        ),
    )


@router.patch(
    '/{cafe_id}',
    response_model=CafeInfo,
    response_model_exclude_none=True,
    summary='Обновить кафе',
    description='Обновить кафе. Доступно администраторам и менеджерам.',
)
@inject
async def update_cafe(
    cafe_id: int,
    cafe_in: CafeUpdate,
    session: SessionDependency,
    cafe_crud: CRUDCafeDependency,
    current_user: AdminAndManagerDependency,
) -> Cafe:
    """Обновление кафе."""
    cafe = await validate_cafe_id_with_relations(
        cafe_id=cafe_id,
        session=session,
        cafe_crud=cafe_crud,
        show_all=True,
    )

    validate_cafe_update_permissions(
        user=current_user,
        cafe=cafe,
        cafe_in=cafe_in,
    )

    if cafe_in.phone is not None:
        await validate_cafe_phone_is_available(
            session=session,
            phone=cafe_in.phone,
            exclude_cafe_id=cafe_id,
        )
    if cafe_in.managers_id is not None:
        validate_last_manager_not_removed(cafe_in=cafe_in)
        await validate_managers_are_allowed(
            session=session,
            managers_id=cafe_in.managers_id,
        )

    return await cafe_crud.update(
        db=session,
        db_obj=cafe,
        obj_in=cafe_in,
    )


@router.delete(
    '/{cafe_id}',
    response_model=CafeInfo,
    response_model_exclude_none=True,
    summary='Деактивировать кафе',
    description='Деактивировать кафе. Доступно только администраторам.',
)
@inject
async def delete_cafe(
    cafe_id: int,
    session: SessionDependency,
    cafe_crud: CRUDCafeDependency,
    cafe_service: CafeServiceDependency,
    _: AdminOnlyDependency,
) -> Cafe:
    """Деактивация кафе через is_active."""
    cafe = await validate_cafe_id_with_relations(
        cafe_id=cafe_id,
        session=session,
        cafe_crud=cafe_crud,
        show_all=True,
    )

    return await cafe_service.deactivate_cafe(
        session=session,
        cafe=cafe,
        cafe_crud=cafe_crud,
    )
