"""Модуль аутентификации и авторизации пользователей."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt_security import TokenService
from app.crud import CRUDUser
from app.models import User
from app.schemas.user import (
    UserCreateByAdmin,
    UserRole,
    UserUpdateByAdmin,
)


class AuthService:
    """Сервис для аутентификации и валидации."""

    def __init__(
        self,
        user_crud: CRUDUser,
        token_service: TokenService,
    ) -> None:
        """Инициализация CRUD для сервисного слоя аутентификации."""
        self.user_crud = user_crud
        self.token_service = token_service

    async def get_current_user(
        self,
        token: str,
        session: AsyncSession,
    ) -> User:
        """Возвращает текущего аутентифицированного пользователя."""
        token_data = self.token_service.verify_access_token(token)
        user = await self.user_crud.get(session, token_data.user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Пользователь не найден',
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Пользователь не активен',
            )
        return user

    async def validate_user_id(
        self,
        user_id: int,
        session: AsyncSession,
    ) -> User:
        """Проверяет, что user_id существует в базе."""
        user = await self.user_crud.get(session, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Пользователь не найден',
            )
        return user

    def validate_managers_permissions(
        self,
        manager: User,
        user_to_update: User | None = None,
        user_to_create: UserCreateByAdmin | None = None,
    ) -> None:
        """Проверяет права менеджера."""
        if user_to_update:
            if user_to_update.is_administrator:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='Менеджер не может изменять администратора',
                )
        if user_to_create:
            if user_to_create.role == UserRole.ADMINISTRATOR:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='Менеджер не может создавать администратора',
                )

    def validate_admin_and_manger_self_update(
        self,
        request: UserUpdateByAdmin,
    ) -> None:
        """Не дает администратору менять собственную роль и активность."""
        if request.role is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Администратор | Менеджер не может изменить свою роль',
            )

        if request.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Администратор | Менджер не может деактивировать себя',
            )

    def allow_admin_only(
        self,
        user: User,
    ) -> User:
        """Доступ только администраторам."""
        if not user.is_administrator:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Только для администраторов',
            )
        return user

    def allow_admin_and_manager(
        self,
        user: User,
    ) -> User:
        """Доступ администраторам и менеджерам."""
        if not user.is_administrator and not user.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Только для администраторов и менеджеров',
            )
        return user
