"""Модуль с эндпоинтами для работы с акциями."""
from http import HTTPStatus
from typing import List, Optional

from dependency_injector.wiring import inject
from fastapi import APIRouter, Body, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import (
    AdminAndManagerDependency,
    AdminOnlyDependency,
    CRUDActionDependency,
    SessionDependency,
    UserDependency,
)
from app.schemas.action import ActionCreate, ActionInfo, ActionUpdate
from app.validators.action import (
    validate_action_exists,
    validate_action_update_permissions,
    validate_cafes_exist,
    validate_requested_show_all,
)

router = APIRouter()


@router.get(
    '/',
    response_model=List[ActionInfo],
    response_model_exclude_none=True,
    summary='Получить список акций',
    description='Получить список акций',
)
@inject
async def get_all_actions(
    session: SessionDependency,
    action_crud: CRUDActionDependency,
    current_user: UserDependency,
    show_all: bool = Query(
        False,
        description='Показывать все акции или нет. По умолчанию активные',
    ),
    cafe_id: Optional[int] = Query(
        None,
        description='ID кафе, в котором показывать акции',
    ),
) -> List[ActionInfo]:
    """Получение списка акций."""
    only_active = not validate_requested_show_all(
        current_user.role,
        show_all,
    )

    if cafe_id:
        actions = await action_crud.get_multi_by_cafe(
            session,
            cafe_id=cafe_id,
            only_active=only_active,
        )
    else:
        if only_active:
            actions = await action_crud.get_current(session)
        else:
            actions = await action_crud.get_multi(session)

    return actions


@router.post(
    '/',
    response_model=ActionInfo,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    summary='Создать акцию',
    description='Создать акцию',
)
@inject
async def create_action(
    session: SessionDependency,
    action_crud: CRUDActionDependency,
    _: AdminAndManagerDependency,
    action_in: ActionCreate = Body(...),
) -> ActionInfo:
    """Создание новой акции. Только для администраторов и менеджеров."""
    try:
        await validate_cafes_exist(session, action_in.cafes_id)
        return await action_crud.create_with_cafes(session, obj_in=action_in)
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Ошибка при создании акции',
        ) from e


@router.get(
    '/{action_id}',
    response_model=ActionInfo,
    response_model_exclude_none=True,
    summary='Получить акцию по id',
    description='Получить акцию по id',
)
@inject
async def get_action_by_id(
    action_id: int,
    session: SessionDependency,
    action_crud: CRUDActionDependency,
    current_user: UserDependency,
) -> ActionInfo:
    """Получение информации об акции по ее ID."""
    only_active = not validate_requested_show_all(
        current_user.role,
        True,
    )

    action = await validate_action_exists(
        session,
        action_crud,
        action_id,
        only_active=only_active,
    )

    if not current_user.is_administrator and not current_user.is_manager:
        if not action.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Доступ запрещен',
            )

    return action


@router.patch(
    '/{action_id}',
    response_model=ActionInfo,
    response_model_exclude_none=True,
    summary='Обновить акцию',
    description='Обновить акцию',
)
@inject
async def update_action(
    action_id: int,
    action_in: ActionUpdate,
    session: SessionDependency,
    action_crud: CRUDActionDependency,
    current_user: AdminAndManagerDependency,
) -> ActionInfo:
    """Обновление информации об акции по ее ID."""
    try:
        action = await validate_action_exists(
            session,
            action_crud,
            action_id,
            only_active=False,
        )

        validate_action_update_permissions(current_user.role, action_in)

        if action_in.cafes_id is not None:
            await validate_cafes_exist(session, action_in.cafes_id)

        return await action_crud.update_with_cafes(
            db=session,
            db_obj=action,
            obj_in=action_in,
        )
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Ошибка при обновлении акции',
        ) from e


@router.delete(
    '/{action_id}',
    response_model=ActionInfo,
    response_model_exclude_none=True,
    summary='Деактивировать акцию',
    description='Деактивировать акцию. Доступно только администраторам.',
)
@inject
async def delete_action(
    action_id: int,
    session: SessionDependency,
    _: AdminOnlyDependency,
    action_crud: CRUDActionDependency,
) -> ActionInfo:
    """Деактивация акции через is_active (мягкое удаление)."""
    try:
        action = await validate_action_exists(
            session,
            action_crud,
            action_id,
            only_active=False,
        )

        return await action_crud.update(
            db=session,
            db_obj=action,
            obj_in=ActionUpdate(is_active=False),
        )
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Ошибка при деактивации акции',
        ) from e
