"""CRUD для модели Action."""

from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import log_audit_event
from app.crud.base import CRUDBase
from app.models import Action
from app.models.cafe import CafeAction
from app.schemas.action import ActionCreate, ActionUpdate


class CRUDAction(CRUDBase[Action, ActionCreate, ActionUpdate]):
    """CRUD для акций."""

    async def get_with_relations(
        self,
        db: AsyncSession,
        obj_id: int,
        only_active: bool = True,
    ) -> Optional[Action]:
        """Получить акцию со всеми связанными данными."""
        stmt = (
            select(Action)
            .where(Action.id == obj_id)
            .options(selectinload(Action.cafes))
        )
        if only_active:
            stmt = stmt.where(Action.is_active._is(True))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi_by_cafe(
        self,
        db: AsyncSession,
        cafe_id: int,
        *,
        only_active: bool = True,
    ) -> List[Action]:
        """Получить акции по ID кафе."""
        query = (
            select(Action)
            .join(CafeAction, Action.id == CafeAction.action_id)
            .where(CafeAction.cafe_id == cafe_id)
            .options(selectinload(Action.cafes))
        )

        if only_active:
            query = query.where(Action.is_active.is_(True))

        result = await db.execute(query)
        actions = result.scalars().all()

        return list(actions)

    async def create_with_cafes(
        self,
        db: AsyncSession,
        *,
        obj_in: ActionCreate,
    ) -> Action:
        """Создать акцию и привязать к кафе.

        Создаётся акция.
        Добавляются связи с кафе.
        Возвращаются данные с новыми связями в result.

        Исключения:
            IntegrityError: При нарушении целостности данных.
        """
        action_data = obj_in.model_dump(exclude={'cafes_id'})
        db_action = Action(**action_data)
        try:
            db.add(db_action)
            await db.flush()

            if obj_in.cafes_id:
                for cafe_id in obj_in.cafes_id:
                    cafe_action = CafeAction(
                        cafe_id=cafe_id,
                        action_id=db_action.id,
                    )
                    db.add(cafe_action)

            await db.commit()
            await db.refresh(db_action)

            result = await db.execute(
                select(Action)
                .where(Action.id == db_action.id)
                .options(selectinload(Action.cafes)),
            )
            created_action = result.scalar_one()

            log_audit_event(
                event='Создана запись в таблице action',
                details={
                    'id': created_action.id,
                    'parameters': action_data | {'cafes_id': obj_in.cafes_id},
                },
            )
            return created_action

        except IntegrityError as e:
            await db.rollback()
            log_audit_event(
                event='Ошибка при создании акции',
                details={
                    'error': str(e),
                    'parameters': action_data | {'cafes_id': obj_in.cafes_id},
                },
                level='ERROR',
            )
            raise

    async def update_with_cafes(
        self,
        db: AsyncSession,
        *,
        db_obj: Action,
        obj_in: ActionUpdate,
    ) -> Action:
        """Обновить акцию и ее связи с кафе.

        Обновляются поля акции.
        Обновляются связи с кафе (удаляются старые связи).
        Создаются новые связи.
        Возвращаются данные с новыми связями в result.

        Исключения:
            IntegrityError: При нарушении целостности данных.
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        cafes_id = update_data.pop('cafes_id', None)
        try:
            for field, value in update_data.items():
                setattr(db_obj, field, value)

            if cafes_id is not None:
                await db.execute(
                    delete(CafeAction).where(
                        CafeAction.action_id == db_obj.id),
                )

                for cafe_id in cafes_id:
                    cafe_action = CafeAction(
                        cafe_id=cafe_id,
                        action_id=db_obj.id,
                    )
                    db.add(cafe_action)

            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)

            result = await db.execute(
                select(Action)
                .where(Action.id == db_obj.id)
                .options(selectinload(Action.cafes)),
            )
            updated_action = result.scalar_one()
            log_audit_event(
                event='Обновлена запись в таблице action',
                details={
                    'id': updated_action.id,
                    'parameters': update_data | {'cafes_id': cafes_id},
                },
            )
            return updated_action

        except IntegrityError as e:
            await db.rollback()
            log_audit_event(
                event='Ошибка при обновлении акции',
                details={
                    'error': str(e),
                    'parameters': update_data | {'cafes_id': obj_in.cafes_id},
                },
                level='ERROR',
            )
            raise

    async def get_current(
        self,
        db: AsyncSession,
    ) -> List[Action]:
        """Получить только текущие активные акции."""
        result = await db.execute(
            select(Action)
            .where(
                Action.is_active.is_(True),
            )
            .options(selectinload(Action.cafes)),
        )
        return list(result.scalars().all())
