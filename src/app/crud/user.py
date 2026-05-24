"""CRUD операции для пользователей."""

from typing import Any

import bcrypt
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ENCODING
from app.core.logging import log_audit_event
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserCreateByAdmin,
    UserUpdateByAdmin,
    UserUpdateOwn,
)


class CRUDUser(CRUDBase[User, UserCreate, UserUpdateOwn]):
    """CRUD операции для работы с пользователями."""

    async def verify_password(
        self,
        plain_password: str,
        hashed_password: str,
    ) -> bool:
        """Проверяет соответствие пароля хешу."""
        return bcrypt.checkpw(
            plain_password.encode(ENCODING),
            hashed_password.encode(ENCODING),
        )

    async def get_password_hash(self, password: str) -> str:
        """Хеширует пароль."""
        return bcrypt.hashpw(
            password.encode(ENCODING),
            bcrypt.gensalt(),
        ).decode(ENCODING)

    async def get_by_attributes(
        self,
        session: AsyncSession,
        **kwargs: Any,
    ) -> User | None:
        """Получает пользователя по атрибутам."""
        conditions = [
            getattr(self.model, key) == value
            for key, value in kwargs.items()
            if hasattr(self.model, key)
        ]
        if not conditions:
            return None
        query = select(self.model).where(or_(*conditions))
        user = await session.execute(query)
        return user.scalar_one_or_none()

    async def create_user(
        self,
        request: UserCreate | UserCreateByAdmin,
        session: AsyncSession,
    ) -> User:
        """Создаёт нового пользователя."""
        try:
            request_data = request.model_dump()

            if request_data.get('password'):
                request_data['password'] = await self.get_password_hash(
                    request_data['password'],
                )

            return await super().create(session, obj_in=request_data)
        except IntegrityError as e:
            await session.rollback()
            self._handle_integrity_error(e, 'create')

    async def update_user(
        self,
        db_obj: User,
        request: UserUpdateOwn | UserUpdateByAdmin,
        session: AsyncSession,
    ) -> User:
        """Обновляет данные пользователя."""
        try:
            update_data = request.model_dump(exclude_unset=True)

            if update_data.get('password'):
                update_data['password'] = await self.get_password_hash(
                    update_data['password'],
                )

            return await super().update(
                session,
                db_obj=db_obj,
                obj_in=update_data,
            )
        except IntegrityError as e:
            await session.rollback()
            self._handle_integrity_error(e, 'update')

    @staticmethod
    def _handle_integrity_error(
        e: IntegrityError,
        operation: str,  # ← добавляем параметр
    ) -> None:
        """Преобразует исключение IntegrityError в HTTPException."""
        error_msg = str(e.orig).lower()

        operation = 'создании' if operation == 'create' else 'обновлении'

        fields_map = {
            'username': 'Имя пользователя',
            'email': 'Email',
            'phone': 'Телефон',
            'tg_id': 'ID телеграм',
        }

        for field, field_name in fields_map.items():
            if field in error_msg:
                log_audit_event(
                    event='Нарушение уникальности '
                    f'при {operation} пользователя',
                    details={
                        'operation': operation,
                        'field': field,
                        'field_name': field_name,
                        'table': User.__tablename__,
                        'error_detail': error_msg,
                    },
                    level='WARNING',
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f'Поле {field_name} уже занято',
                )

        log_audit_event(
            event='Неизвестная ошибка целостности '
            f'при {operation} пользователя',
            details={
                'operation': operation,
                'error_msg': error_msg,
                'table': User.__tablename__,
            },
            level='ERROR',
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Конфликт данных при сохранении',
        )


user_crud = CRUDUser(User)
