"""Валидаторы для акций."""

from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import CRUDAction
from app.models import Action, Cafe
from app.schemas.action import ActionUpdate
from app.schemas.user import UserRole


class ActionValidator:
    """Валидаторы для акций."""

    @staticmethod
    async def validate_action_exists(
        session: AsyncSession,
        action_crud: CRUDAction,
        action_id: int,
        only_active: bool = False,
    ) -> Action:
        """Проверяет существование акции и возвращает её."""
        action = await action_crud.get_with_relations(
            session,
            obj_id=action_id,
            only_active=only_active,
        )
        if not action:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Акция не найдена.',
            )
        return action

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
    def validate_action_update_permissions(
        user_role: int,
        action_in: ActionUpdate,
    ) -> None:
        """Проверяет права на обновление акции.

        Менеджеры могут обновлять акции, но не могут деактивировать.
        """
        if user_role == UserRole.MANAGER and action_in.is_active is False:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='Менеджер не может деактивировать акцию.',
            )

    @staticmethod
    def get_show_all_for_actions(user_role: int) -> bool:
        """Определяет, можно ли показывать неактивные акции."""
        return user_role in (UserRole.ADMINISTRATOR, UserRole.MANAGER)

    @staticmethod
    def validate_requested_show_all(
        user_role: int,
        show_all: bool | None,
    ) -> bool:
        """Возвращает допустимое значение show_all для пользователя."""
        resolved_show_all = bool(show_all)
        if ActionValidator.get_show_all_for_actions(user_role):
            return resolved_show_all
        return False


async def validate_action_exists(
    session: AsyncSession,
    action_crud: CRUDAction,
    action_id: int,
    only_active: bool = False,
) -> Action:
    """Проверяет существование акции."""
    return await ActionValidator.validate_action_exists(
        session, action_crud, action_id, only_active,
    )


async def validate_cafes_exist(
    session: AsyncSession,
    cafes_id: list[int],
) -> None:
    """Проверяет существование кафе (с проверкой на дубли)."""
    await ActionValidator.validate_cafes_exist(session, cafes_id)


def validate_action_update_permissions(
    user_role: int,
    action_in: ActionUpdate,
) -> None:
    """Проверяет права на обновление акции."""
    ActionValidator.validate_action_update_permissions(user_role, action_in)


def validate_requested_show_all(
    user_role: int,
    show_all: bool | None,
) -> bool:
    """Возвращает допустимое значение show_all."""
    return ActionValidator.validate_requested_show_all(user_role, show_all)
