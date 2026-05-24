"""Сервисный слой для чтения столов с учётом прав доступа."""

from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Table, User
from app.validators.table import (
    validate_requested_show_all,
    validate_table_belongs_to_cafe,
)


class TableService:
    """Сервис для работы со столами."""

    async def get_tables(
        self,
        session: AsyncSession,
        cafe_id: int,
        user: User,
        show_all: bool | None = False,
    ) -> list[Table]:
        """Получить список столов кафе с учётом прав пользователя."""
        resolved_show_all = validate_requested_show_all(
            user=user,
            show_all=bool(show_all),
        )

        query = select(Table).where(Table.cafe_id == cafe_id)
        if not resolved_show_all:
            query = query.where(Table.is_active.is_(True))

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_table(
        self,
        session: AsyncSession,
        cafe_id: int,
        table_id: int,
        user: User,
        show_all: bool | None = False,
    ) -> Table:
        """Получить стол по id с учётом прав пользователя."""
        resolved_show_all = validate_requested_show_all(
            user=user,
            show_all=bool(show_all),
        )

        query = select(Table).where(Table.id == table_id)
        if not resolved_show_all:
            query = query.where(Table.is_active.is_(True))

        result = await session.execute(query)
        table = result.scalar_one_or_none()

        if table is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Стол не найден.',
            )

        validate_table_belongs_to_cafe(
            table=table,
            cafe_id=cafe_id,
        )
        return table
