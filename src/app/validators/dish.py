"""Валидаторы для блюд."""

from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import CRUDDish
from app.models import Cafe, Dish
from app.schemas.dish import DishUpdate
from app.schemas.user import UserRole


class DishValidator:
    """Валидаторы для блюд."""

    @staticmethod
    async def validate_dish_exists(
        session: AsyncSession,
        dish_crud: CRUDDish,
        dish_id: int,
        only_active: bool = False,
    ) -> Dish:
        """Проверяет существование блюда и возвращает его."""
        dish = await dish_crud.get_with_relations(
            session,
            obj_id=dish_id,
            only_active=only_active,
        )
        if not dish:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Блюдо не найдено.',
            )
        return dish

    @staticmethod
    async def validate_cafes_exist(
        session: AsyncSession,
        cafes_id: list[int],
    ) -> None:
        """Проверяет существование всех указанных кафе."""
        if not cafes_id:
            return

        if len(cafes_id) != len(set(cafes_id)):
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='ID кафе не должны повторяться.',
            )

        result = await session.execute(
            select(Cafe.id).where(Cafe.id.in_(cafes_id)),
        )
        existing_ids = {row[0] for row in result.all()}
        missing_ids = set(cafes_id) - existing_ids

        if missing_ids:
            if len(missing_ids) == 1:
                tail_message = 'не существует.'
            else:
                tail_message = 'не существуют.'
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f'Кафе с ID {sorted(missing_ids)} {tail_message}',
            )

    @staticmethod
    def validate_dish_update_permissions(
        user_role: int,
        dish_in: DishUpdate,
    ) -> None:
        """Проверяет права на обновление блюда."""
        if user_role == UserRole.MANAGER and dish_in.is_active is False:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='Менеджер не может деактивировать блюдо.',
            )

    @staticmethod
    def get_show_all_for_dishes(user_role: int) -> bool:
        """Определяет, можно ли показывать неактивные блюда."""
        return user_role in (UserRole.ADMINISTRATOR, UserRole.MANAGER)

    @staticmethod
    def validate_requested_show_all(
        user_role: int,
        show_all: bool | None,
    ) -> bool:
        """Возвращает допустимое значение show_all для пользователя."""
        resolved_show_all = bool(show_all)
        if DishValidator.get_show_all_for_dishes(user_role):
            return resolved_show_all
        return False


async def validate_dish_exists(
    session: AsyncSession,
    dish_crud: CRUDDish,
    dish_id: int,
    only_active: bool = False,
) -> Dish:
    """Проверяет существование блюда."""
    return await DishValidator.validate_dish_exists(
        session, dish_crud, dish_id, only_active,
    )


async def validate_cafes_exist_for_dish(
    session: AsyncSession,
    cafes_id: list[int],
) -> None:
    """Проверяет существование кафе (с проверкой на дубли)."""
    await DishValidator.validate_cafes_exist(session, cafes_id)


def validate_dish_update_permissions(
    user_role: int,
    dish_in: DishUpdate,
) -> None:
    """Проверяет права на обновление блюда."""
    DishValidator.validate_dish_update_permissions(user_role, dish_in)


def validate_requested_show_all_for_dish(
    user_role: int,
    show_all: bool | None,
) -> bool:
    """Возвращает допустимое значение show_all."""
    return DishValidator.validate_requested_show_all(user_role, show_all)
