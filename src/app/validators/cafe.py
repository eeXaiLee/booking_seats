"""Валидаторы для кафе."""

from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import CafeCRUD
from app.models import Cafe, User
from app.schemas import CafeUpdate, UserRole


class CafeValidator:
    """Валидаторы для кафе."""

    @staticmethod
    async def validate_cafe_id(
        session: AsyncSession,
        cafe_id: int,
        show_all: bool = False,
    ) -> Cafe | None:
        """Возвращает кафе по id."""
        query = select(Cafe).where(Cafe.id == cafe_id)

        if not show_all:
            query = query.where(Cafe.is_active.is_(True))

        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def validate_managers_exist(
        session: AsyncSession,
        managers_id: list[int],
    ) -> list[User]:
        """Возвращает всех существующих менеджеров."""
        if not managers_id:
            return []

        query = select(User).where(User.id.in_(managers_id))
        result = await session.execute(query)
        managers = list(result.scalars().all())

        if len(managers) != len(set(managers_id)):
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Один или несколько менеджеров не найдены.',
            )

        return managers

    @staticmethod
    async def validate_managers_are_allowed(
        session: AsyncSession,
        managers_id: list[int],
    ) -> None:
        """Исключает недопустимые роли в managers_id."""
        managers = await CafeValidator.validate_managers_exist(
            session=session,
            managers_id=managers_id,
        )

        invalid_users = [
            user.id
            for user in managers
            if user.role not in (UserRole.MANAGER, UserRole.ADMINISTRATOR)
        ]

        if invalid_users:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=(
                    'В managers_id можно передавать только '
                    'менеджеров или администраторов.'
                ),
            )

    @staticmethod
    def get_show_all_for_cafes(user: User) -> bool:
        """Определяет, можно ли показывать неактивные кафе."""
        return user.is_administrator or user.is_manager

    @staticmethod
    def validate_requested_show_all(
        user: User,
        show_all: bool | None,
    ) -> bool:
        """Возвращает допустимое значение show_all для пользователя."""
        resolved_show_all = bool(show_all)

        if CafeValidator.get_show_all_for_cafes(user):
            return resolved_show_all
        return False

    @staticmethod
    def validate_cafe_management_access(
        user: User,
        cafe: Cafe,
    ) -> None:
        """Исключает изменение чужого кафе для менеджера."""
        if user.is_administrator:
            return

        if not user.is_manager:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='Недостаточно прав для изменения кафе.',
            )

        if not any(manager.id == user.id for manager in cafe.managers):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='Менеджер может изменять только своё кафе.',
            )

    @staticmethod
    def validate_cafe_update_permissions(
        user: User,
        cafe: Cafe,
        cafe_in: CafeUpdate,
    ) -> None:
        """Исключает недопустимое обновление кафе."""
        CafeValidator.validate_cafe_management_access(
            user=user,
            cafe=cafe,
        )

        if user.is_manager and cafe_in.is_active is False:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='Менеджер не может деактивировать кафе.',
            )

    @staticmethod
    async def validate_cafe_phone_is_available(
        session: AsyncSession,
        phone: str,
        exclude_cafe_id: int | None = None,
    ) -> None:
        """Исключает использование занятого номера телефона другим кафе."""
        query = select(Cafe).where(Cafe.phone == phone)

        if exclude_cafe_id is not None:
            query = query.where(Cafe.id != exclude_cafe_id)

        result = await session.execute(query)
        cafe = result.scalars().first()

        if cafe is not None:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Кафе с таким номером телефона уже существует.',
            )

    @staticmethod
    def validate_last_manager_not_removed(
        cafe_in: CafeUpdate,
    ) -> None:
        """Исключает удаление последнего менеджера из кафе."""
        if cafe_in.managers_id == []:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Нельзя убрать последнего менеджера из кафе.',
            )

    @staticmethod
    def validate_cafe_is_active(
        cafe: Cafe,
    ) -> None:
        """Исключает работу с неактивным кафе."""
        if not cafe.is_active:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Нельзя создавать столы для неактивного кафе.',
            )


async def validate_cafe_id(
    session: AsyncSession,
    cafe_id: int,
    show_all: bool = False,
) -> Cafe:
    """Возвращает кафе по id или выбрасывает 404."""
    cafe = await CafeValidator.validate_cafe_id(
        session=session,
        cafe_id=cafe_id,
        show_all=show_all,
    )

    if cafe is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Кафе не найдено.',
        )

    return cafe


async def validate_cafe_id_with_relations(
    session: AsyncSession,
    cafe_id: int,
    cafe_crud: CafeCRUD,
    show_all: bool = False,
) -> Cafe:
    """Возвращает кафе с подгруженными связями или выбрасывает 404."""
    cafe = await cafe_crud.get(
        db=session,
        obj_id=cafe_id,
        show_all=show_all,
    )

    if cafe is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Кафе не найдено.',
        )

    return cafe


async def validate_managers_exist(
    session: AsyncSession,
    managers_id: list[int],
) -> list[User]:
    """Возвращает всех существующих менеджеров."""
    return await CafeValidator.validate_managers_exist(
        session=session,
        managers_id=managers_id,
    )


async def validate_managers_are_allowed(
    session: AsyncSession,
    managers_id: list[int],
) -> None:
    """Исключает недопустимые роли в managers_id."""
    await CafeValidator.validate_managers_are_allowed(
        session=session,
        managers_id=managers_id,
    )


def get_show_all_for_cafes(user: User) -> bool:
    """Определяет, можно ли показывать неактивные кафе."""
    return CafeValidator.get_show_all_for_cafes(user)


def validate_requested_show_all(
    user: User,
    show_all: bool | None,
) -> bool:
    """Возвращает допустимое значение show_all для пользователя."""
    return CafeValidator.validate_requested_show_all(
        user=user,
        show_all=show_all,
    )


def validate_cafe_management_access(
    user: User,
    cafe: Cafe,
) -> None:
    """Исключает изменение чужого кафе для менеджера."""
    CafeValidator.validate_cafe_management_access(
        user=user,
        cafe=cafe,
    )


def validate_cafe_update_permissions(
    user: User,
    cafe: Cafe,
    cafe_in: CafeUpdate,
) -> None:
    """Исключает недопустимое обновление кафе."""
    CafeValidator.validate_cafe_update_permissions(
        user=user,
        cafe=cafe,
        cafe_in=cafe_in,
    )


async def validate_cafe_phone_is_available(
    session: AsyncSession,
    phone: str,
    exclude_cafe_id: int | None = None,
) -> None:
    """Исключает использование занятого номера телефона другим кафе."""
    await CafeValidator.validate_cafe_phone_is_available(
        session=session,
        phone=phone,
        exclude_cafe_id=exclude_cafe_id,
    )


def validate_last_manager_not_removed(
    cafe_in: CafeUpdate,
) -> None:
    """Исключает удаление последнего менеджера из кафе."""
    CafeValidator.validate_last_manager_not_removed(cafe_in=cafe_in)


def validate_cafe_is_active(
    cafe: Cafe,
) -> None:
    """Исключает работу с неактивным кафе."""
    CafeValidator.validate_cafe_is_active(cafe=cafe)
