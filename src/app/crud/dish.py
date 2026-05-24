"""CRUD для модели Action."""

from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import log_audit_event
from app.crud.base import CRUDBase
from app.models import Dish
from app.models.cafe import CafeDish
from app.schemas.dish import DishCreate, DishUpdate


class CRUDDish(CRUDBase[Dish, DishCreate, DishUpdate]):
    """CRUD для блюд."""

    async def get_with_relations(
        self,
        db: AsyncSession,
        obj_id: int,
        only_active: bool = True,
    ) -> Optional[Dish]:
        """Получить блюдо со всеми связанными данными."""
        stmt = select(Dish).where(Dish.id == obj_id)
        if only_active:
            stmt = stmt.where(Dish.is_active._is(True))
        result = await db.execute(
            select(Dish)
            .where(Dish.id == obj_id)
            .options(selectinload(Dish.cafes)),
        )
        return result.scalar_one_or_none()

    async def get_multi_by_cafe(
        self,
        db: AsyncSession,
        cafe_id: int,
        *,
        only_active: bool = True,
    ) -> List[Dish]:
        """Получить блюда по ID кафе."""
        query = (
            select(Dish)
            .join(CafeDish, Dish.id == CafeDish.dish_id)
            .where(CafeDish.cafe_id == cafe_id)
            .options(selectinload(Dish.cafes))
        )

        if only_active:
            query = query.where(Dish.is_active.is_(True))

        result = await db.execute(query)
        return list(result.scalars().all())

    async def create_with_cafes(
        self,
        db: AsyncSession,
        *,
        obj_in: DishCreate,
    ) -> Dish:
        """Создать блюдо и привязать к кафе.

        Создаётся блюдо.
        Добавляются связи с кафе.
        Возвращаются данные с новыми связями в result.
        """
        dish_data = obj_in.model_dump(exclude={'cafes_id'})
        db_dish = Dish(**dish_data)
        try:
            db.add(db_dish)
            await db.flush()

            if obj_in.cafes_id:
                for cafe_id in obj_in.cafes_id:
                    cafe_dish = CafeDish(
                        cafe_id=cafe_id,
                        dish_id=db_dish.id,
                    )
                    db.add(cafe_dish)

            await db.commit()
            await db.refresh(db_dish)

            result = await db.execute(
                select(Dish)
                .where(Dish.id == db_dish.id)
                .options(selectinload(Dish.cafes)),
            )
            created_dish = result.scalar_one()
            log_audit_event(
                event='Создана запись в таблице dish',
                details={
                    'id': created_dish.id,
                    'parameters': dish_data | {'cafes_id': obj_in.cafes_id},
                },
            )
            return created_dish

        except IntegrityError as e:
            await db.rollback()
            log_audit_event(
                event='Ошибка при создании блюда',
                details={
                    'error': str(e),
                    'parameters': dish_data | {'cafes_id': obj_in.cafes_id},
                },
                level='ERROR',
            )
            raise

    async def update_with_cafes(
        self,
        db: AsyncSession,
        *,
        db_obj: Dish,
        obj_in: DishUpdate,
    ) -> Dish:
        """Обновить блюдо и его связи с кафе.

        Обновляются поля блюда.
        Обновляются связи с кафе (удаляются старые связи).
        Создаются новые связи.
        Возвращаются данные с новыми связями в result.
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        cafes_id = update_data.pop('cafes_id', None)

        try:
            for field, value in update_data.items():
                setattr(db_obj, field, value)

            if cafes_id is not None:
                await db.execute(
                    delete(CafeDish).where(CafeDish.dish_id == db_obj.id),
                )
                for cafe_id in cafes_id:
                    cafe_dish = CafeDish(
                        cafe_id=cafe_id,
                        dish_id=db_obj.id,
                    )
                    db.add(cafe_dish)

            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)

            result = await db.execute(
                select(Dish)
                .where(Dish.id == db_obj.id)
                .options(selectinload(Dish.cafes)),
            )
            updated_dish = result.scalar_one()
            log_audit_event(
                event='Обновлена запись в таблице dish',
                details={
                    'id': updated_dish.id,
                    'parameters': update_data | {'cafes_id': cafes_id},
                },
            )
            return updated_dish

        except IntegrityError as e:
            await db.rollback()
            log_audit_event(
                event='Ошибка при обновлении блюда',
                details={
                    'error': str(e),
                    'parameters': update_data | {'cafes_id': obj_in.cafes_id},
                },
                level='ERROR',
            )
            raise

# dish_crud = CRUDDish(Dish)
