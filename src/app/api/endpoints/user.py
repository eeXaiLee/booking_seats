"""Модуль с эндпоинтами для работы с пользователями."""

from dependency_injector.wiring import inject
from fastapi import APIRouter

from app.api.dependencies import (
    AdminAndManagerDependency,
    AuthServiceDependency,
    CRUDUserDependency,
    SessionDependency,
    UserDependency,
)
from app.models import User
from app.schemas import (
    UserCreate,
    UserInfo,
    UserUpdateOwn,
)
from app.schemas.user import UserCreateByAdmin, UserUpdateByAdmin

router = APIRouter()


@router.get(
    '/',
    response_model=list[UserInfo],
    summary='Получить список пользователей',
)
@inject
async def get_users(
    _: AdminAndManagerDependency,
    session: SessionDependency,
    crud: CRUDUserDependency,
) -> list[User]:
    """Получает список всех пользователей.

    Доступно администраторам и менеджерам.
    """
    return await crud.get_multi(session)


@router.get(
    '/me',
    response_model=UserInfo,
    summary='Получить текущего пользователя',
)
@inject
async def get_me(
    user: UserDependency,
) -> User:
    """Получает информацию о текущем аутентифицированном пользователе."""
    return user


@router.patch(
    '/me',
    response_model=UserInfo,
    summary='Обновить свой профиль',
)
@inject
async def update_me(
    request: UserUpdateOwn,
    user: UserDependency,
    crud: CRUDUserDependency,
    session: SessionDependency,
) -> User:
    """Обновляет данные текущего пользователя."""
    return await crud.update_user(user, request, session)


@router.get(
    '/{user_id}',
    response_model=UserInfo,
    summary='Получить пользователя по ID',
)
@inject
async def get_user(
    user_id: int,
    _: AdminAndManagerDependency,
    session: SessionDependency,
    auth_service: AuthServiceDependency,
) -> User:
    """Получает пользователя по ID. Доступно администраторам и менеджерам."""
    return await auth_service.validate_user_id(user_id, session)


@router.post(
    '/',
    response_model=UserInfo,
    summary='Зарегистрировать пользователя',
)
@inject
async def register_user(
    user: UserCreate,
    session: SessionDependency,
    crud: CRUDUserDependency,
) -> User:
    """Создаёт нового пользователя."""
    return await crud.create_user(user, session)


@router.post(
    '/create',
    response_model=UserInfo,
    summary='Создать пользователя с ролью',
)
@inject
async def create_user(
    user_to_create: UserCreateByAdmin,
    current_user: AdminAndManagerDependency,
    session: SessionDependency,
    auth_service: AuthServiceDependency,
    crud: CRUDUserDependency,
) -> User:
    """Создаёт нового пользователя.

    Только для администраторов и менеджеров.
    """
    if current_user.is_manager:
        auth_service.validate_managers_permissions(
            current_user,
            user_to_create=user_to_create,
        )
    return await crud.create_user(user_to_create, session)


@router.patch(
    '/{user_id}',
    response_model=UserInfo,
    summary='Обновить пользователя по ID',
)
@inject
async def update_user(
    user_id: int,
    request: UserUpdateByAdmin,
    session: SessionDependency,
    current_user: UserDependency,
    auth_service: AuthServiceDependency,
    crud: CRUDUserDependency,
) -> User:
    """Обновляет данные пользователя по ID.

    Доступно администраторам и менеджерам.
    """
    user_to_update = await auth_service.validate_user_id(user_id, session)

    is_self_update = current_user.id == user_to_update.id

    if current_user.is_manager:
        auth_service.validate_managers_permissions(
            current_user,
            user_to_update=user_to_update,
        )

    if is_self_update and (
        current_user.is_administrator or current_user.is_manager
    ):
        auth_service.validate_admin_and_manger_self_update(request)

    return await crud.update_user(user_to_update, request, session)
