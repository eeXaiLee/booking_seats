"""Валидаторы для столов."""
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import TableCRUD
from app.models import Cafe, Table, User


class TableValidator:
    """Валидаторы для столов."""

    @staticmethod
    async def validate_table_id(
        session: AsyncSession,
        table_id: int,
        show_all: bool = False,
    ) -> Table | None:
        """Возвращает стол по id."""
        query = select(Table).where(Table.id == table_id)

        if not show_all:
            query = query.where(Table.is_active.is_(True))

        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    def validate_table_belongs_to_cafe(
        table: Table,
        cafe_id: int,
    ) -> None:
        """Исключает стол из другого кафе."""
        if table.cafe_id != cafe_id:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Стол в указанном кафе не найден.',
            )

    @staticmethod
    def validate_table_cafe_id_match(
        path_cafe_id: int,
        body_cafe_id: int,
    ) -> None:
        """Исключает расхождение cafe_id в path и body."""
        if body_cafe_id != path_cafe_id:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='cafe_id в пути и теле запроса должны совпадать.',
            )

    @staticmethod
    def get_show_all_for_tables(user: User) -> bool:
        """Определяет, можно ли показывать неактивные столы."""
        return user.is_administrator or user.is_manager

    @staticmethod
    def validate_requested_show_all(
        user: User,
        show_all: bool | None,
    ) -> bool:
        """Возвращает допустимое значение show_all для пользователя."""
        resolved_show_all = bool(show_all)

        if TableValidator.get_show_all_for_tables(user):
            return resolved_show_all
        return False

    @staticmethod
    def validate_table_management_access(
        user: User,
        cafe: Cafe,
    ) -> None:
        """Исключает изменение столов чужого кафе для менеджера."""
        if user.is_administrator:
            return

        if not user.is_manager:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='Недостаточно прав для изменения столов.',
            )

        if not any(manager.id == user.id for manager in cafe.managers):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='Менеджер может изменять столы только своего кафе.',
            )


async def validate_table_id(
    session: AsyncSession,
    table_id: int,
    show_all: bool = False,
) -> Table:
    """Возвращает стол по id или выбрасывает 404."""
    table = await TableValidator.validate_table_id(
        session=session,
        table_id=table_id,
        show_all=show_all,
    )

    if table is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Стол не найден.',
        )

    return table


async def validate_table_id_with_relations(
    session: AsyncSession,
    table_id: int,
    table_crud: TableCRUD,
    show_all: bool = False,
) -> Table:
    """Возвращает стол с подгруженными связями или выбрасывает 404."""
    table = await table_crud.get(
        db=session,
        obj_id=table_id,
        show_all=show_all,
    )

    if table is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Стол не найден.',
        )

    return table


def validate_table_belongs_to_cafe(
    table: Table,
    cafe_id: int,
) -> None:
    """Исключает стол из другого кафе."""
    TableValidator.validate_table_belongs_to_cafe(
        table=table,
        cafe_id=cafe_id,
    )


def validate_table_cafe_id_match(
    path_cafe_id: int,
    body_cafe_id: int,
) -> None:
    """Исключает расхождение cafe_id в path и body."""
    TableValidator.validate_table_cafe_id_match(
        path_cafe_id=path_cafe_id,
        body_cafe_id=body_cafe_id,
    )


def get_show_all_for_tables(user: User) -> bool:
    """Определяет, можно ли показывать неактивные столы."""
    return TableValidator.get_show_all_for_tables(user)


def validate_requested_show_all(
    user: User,
    show_all: bool | None,
) -> bool:
    """Возвращает допустимое значение show_all для пользователя."""
    return TableValidator.validate_requested_show_all(
        user=user,
        show_all=show_all,
    )


def validate_table_management_access(
    user: User,
    cafe: Cafe,
) -> None:
    """Исключает изменение столов чужого кафе для менеджера."""
    TableValidator.validate_table_management_access(
        user=user,
        cafe=cafe,
    )
