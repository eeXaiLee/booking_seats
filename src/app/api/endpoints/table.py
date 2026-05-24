"""Модуль с эндпоинтами для работы со столами в кафе."""

from http import HTTPStatus

from dependency_injector.wiring import inject
from fastapi import APIRouter

from app.api.dependencies import (
    AdminAndManagerDependency,
    CRUDCafeDependency,
    CRUDTableDependency,
    SessionDependency,
    TableServiceDependency,
    UserDependency,
)
from app.models import Table
from app.schemas import TableCreate, TableInfo, TableUpdate
from app.validators.cafe import (
    validate_cafe_id_with_relations,
    validate_cafe_is_active,
)
from app.validators.table import (
    validate_table_belongs_to_cafe,
    validate_table_cafe_id_match,
    validate_table_id,
    validate_table_management_access,
)

router = APIRouter()


@router.get(
    '/',
    response_model=list[TableInfo],
    response_model_exclude_none=True,
    summary='Получить список столов в кафе',
    description=(
        'Получить список столов. Доступно авторизованным пользователям.'
    ),
)
@inject
async def get_tables(
    cafe_id: int,
    session: SessionDependency,
    table_service: TableServiceDependency,
    current_user: UserDependency,
    show_all: bool = False,
) -> list[Table]:
    """Получение списка столов в кафе."""
    return await table_service.get_tables(
        session=session,
        cafe_id=cafe_id,
        user=current_user,
        show_all=show_all,
    )


@router.post(
    '/',
    response_model=TableInfo,
    response_model_exclude_none=True,
    status_code=HTTPStatus.CREATED,
    summary='Создать стол в кафе',
    description='Создать стол. Доступно администраторам и менеджерам.',
)
@inject
async def create_table(
    cafe_id: int,
    table_in: TableCreate,
    session: SessionDependency,
    table_crud: CRUDTableDependency,
    cafe_crud: CRUDCafeDependency,
    current_user: AdminAndManagerDependency,
) -> Table:
    """Создание стола в кафе."""
    validate_table_cafe_id_match(
        path_cafe_id=cafe_id,
        body_cafe_id=table_in.cafe_id,
    )

    cafe = await validate_cafe_id_with_relations(
        cafe_id=cafe_id,
        session=session,
        cafe_crud=cafe_crud,
        show_all=True,
    )

    validate_cafe_is_active(cafe)

    validate_table_management_access(
        user=current_user,
        cafe=cafe,
    )

    return await table_crud.create(
        db=session,
        obj_in=table_in,
    )


@router.get(
    '/{table_id}',
    response_model=TableInfo,
    response_model_exclude_none=True,
    summary='Получить стол в кафе по id',
    description='Получить стол по id. Доступно авторизованным пользователям.',
)
@inject
async def get_table(
    cafe_id: int,
    table_id: int,
    session: SessionDependency,
    table_service: TableServiceDependency,
    current_user: UserDependency,
    show_all: bool = False,
) -> Table:
    """Получение одного стола кафе."""
    return await table_service.get_table(
        session=session,
        cafe_id=cafe_id,
        table_id=table_id,
        user=current_user,
        show_all=show_all,
    )


@router.patch(
    '/{table_id}',
    response_model=TableInfo,
    response_model_exclude_none=True,
    summary='Обновить стол в кафе',
    description='Обновить стол. Доступно администраторам и менеджерам.',
)
@inject
async def update_table(
    cafe_id: int,
    table_id: int,
    table_in: TableUpdate,
    session: SessionDependency,
    table_crud: CRUDTableDependency,
    cafe_crud: CRUDCafeDependency,
    current_user: AdminAndManagerDependency,
) -> Table:
    """Обновление стола кафе."""
    table = await validate_table_id(
        table_id=table_id,
        session=session,
        show_all=True,
    )
    validate_table_belongs_to_cafe(
        table=table,
        cafe_id=cafe_id,
    )

    if table_in.cafe_id is not None:
        validate_table_cafe_id_match(
            path_cafe_id=cafe_id,
            body_cafe_id=table_in.cafe_id,
        )

    cafe = await validate_cafe_id_with_relations(
        cafe_id=cafe_id,
        session=session,
        cafe_crud=cafe_crud,
        show_all=True,
    )

    validate_table_management_access(
        user=current_user,
        cafe=cafe,
    )

    return await table_crud.update(
        db=session,
        db_obj=table,
        obj_in=table_in,
    )


@router.delete(
    '/{table_id}',
    response_model=TableInfo,
    response_model_exclude_none=True,
    summary='Деактивировать стол в кафе',
    description='Деактивировать стол. Доступно администраторам и менеджерам.',
)
@inject
async def delete_table(
    cafe_id: int,
    table_id: int,
    session: SessionDependency,
    table_crud: CRUDTableDependency,
    cafe_crud: CRUDCafeDependency,
    current_user: AdminAndManagerDependency,
) -> Table:
    """Мягкое удаление стола через is_active=False."""
    table = await validate_table_id(
        table_id=table_id,
        session=session,
        show_all=True,
    )
    validate_table_belongs_to_cafe(
        table=table,
        cafe_id=cafe_id,
    )

    cafe = await validate_cafe_id_with_relations(
        cafe_id=cafe_id,
        session=session,
        cafe_crud=cafe_crud,
        show_all=True,
    )

    validate_table_management_access(
        user=current_user,
        cafe=cafe,
    )

    return await table_crud.update(
        db=session,
        db_obj=table,
        obj_in=TableUpdate(is_active=False),
    )
