"""CRUD для модели TimeSlot."""

from collections.abc import Sequence
from datetime import time
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models import TimeSlot
from app.schemas import TimeSlotCreate, TimeSlotUpdate


class TimeSlotCRUD(CRUDBase[TimeSlot, TimeSlotCreate, TimeSlotUpdate]):
    """CRUD временных слотов."""

    async def get_multi_by_cafe_id(
        self,
        cafe_id: int,
        show_all: bool,
        session: AsyncSession,
    ) -> Sequence[TimeSlot]:
        """Получение всех временных слотов кафе."""
        stmt = (
            select(self.model)
            .where(self.model.cafe_id == cafe_id)
            .options(selectinload(self.model.cafe))
        )
        if not show_all:
            stmt = stmt.where(self.model.is_active.is_(True))
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_cafe_id(
        self,
        cafe_id: int,
        slot_id: int,
        session: AsyncSession,
    ) -> TimeSlot | None:
        """Получение одного временного слота в кафе по ID."""
        stmt = (
            select(self.model)
            .where(
                self.model.cafe_id == cafe_id,
                self.model.id == slot_id,
            )
            .options(selectinload(self.model.cafe))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: TimeSlotCreate | dict[str, Any],
    ) -> TimeSlot:
        """Создание временного слота."""
        db_obj = await super().create(db, obj_in=obj_in)
        # Загружаем relationship для сериализации
        stmt = (
            select(self.model)
            .where(self.model.id == db_obj.id)
            .options(selectinload(self.model.cafe))
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: TimeSlot,
        obj_in: TimeSlotUpdate | dict[str, Any],
    ) -> TimeSlot:
        """Обновление временного слота."""
        db_obj = await super().update(db, db_obj=db_obj, obj_in=obj_in)
        # Загружаем relationship для сериализации
        stmt = (
            select(self.model)
            .where(self.model.id == db_obj.id)
            .options(selectinload(self.model.cafe))
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    async def remove(
        self,
        db: AsyncSession,
        db_obj: TimeSlot,
    ) -> None:
        """Удаление временного слота."""
        try:
            await db.delete(db_obj)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise

    async def get_time_slots_at_the_same_time(
        self,
        cafe_id: int,
        start_time: time,
        end_time: time,
        db: AsyncSession,
        slot_id: int | None = None,
    ) -> Sequence[TimeSlot]:
        """Получение временных слотов, пересекающихся с заданными значениями.

        Используется при валидации создания/обновления.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.cafe_id == cafe_id,
                self.model.is_active.is_(True),
                and_(
                    self.model.start_time < end_time,
                    self.model.end_time > start_time,
                ),
            )
            .options(selectinload(self.model.cafe))
        )
        if slot_id is not None:
            stmt = stmt.where(self.model.id != slot_id)
        result = await db.execute(stmt)
        return result.scalars().all()


time_slot_crud = TimeSlotCRUD(TimeSlot)
