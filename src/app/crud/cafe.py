"""CRUD для модели Cafe."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import log_audit_event
from app.crud.base import CRUDBase
from app.models import Cafe, User
from app.schemas import CafeCreate, CafeUpdate


class CafeCRUD(CRUDBase[Cafe, CafeCreate, CafeUpdate]):
    """CRUD для кафе."""

    def __init__(self) -> None:
        """Инициализирует CRUD для кафе."""
        super().__init__(Cafe)

    async def _get_managers(
        self,
        managers_id: list[int],
        session: AsyncSession,
    ) -> list[User]:
        """Получение менеджеров по списку id."""
        managers = await session.execute(
            select(User).where(User.id.in_(managers_id)),
        )
        return list(managers.scalars().all())

    async def get(
        self,
        db: AsyncSession,
        obj_id: int,
        show_all: bool | None = False,
    ) -> Cafe | None:
        """Получение кафе по id."""
        resolved_show_all = bool(show_all)

        stmt = (
            select(self.model)
            .options(selectinload(self.model.managers))
            .where(self.model.id == obj_id)
        )
        if not resolved_show_all:
            stmt = stmt.where(self.model.is_active.is_(True))

        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        show_all: bool | None = False,
    ) -> list[Cafe]:
        """Получение списка кафе."""
        resolved_show_all = bool(show_all)

        stmt = select(self.model).options(
            selectinload(self.model.managers),
        )
        if not resolved_show_all:
            stmt = stmt.where(self.model.is_active.is_(True))

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CafeCreate,
    ) -> Cafe:
        """Создание кафе."""
        cafe_data = obj_in.model_dump()
        managers_id = cafe_data.pop('managers_id')

        cafe = self.model(**cafe_data)
        cafe.managers = await self._get_managers(
            managers_id,
            db,
        )

        db.add(cafe)
        await db.commit()
        await db.refresh(
            cafe,
            attribute_names=['created_at', 'updated_at', 'managers'],
        )

        log_audit_event(
            event='Создана запись в таблице cafe',
            details={
                'id': cafe.id,
                'parameters': cafe_data | {'managers_id': managers_id},
            },
        )
        return cafe

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Cafe,
        obj_in: CafeUpdate,
    ) -> Cafe:
        """Обновление кафе."""
        update_fields = obj_in.model_dump(exclude_unset=True)

        managers_id = update_fields.pop('managers_id', None)
        if managers_id is not None:
            db_obj.managers = await self._get_managers(
                managers_id,
                db,
            )

        for field, value in update_fields.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(
            db_obj,
            attribute_names=['updated_at', 'managers'],
        )

        log_audit_event(
            event='Обновлена запись в таблице cafe',
            details={
                'id': db_obj.id,
                'parameters': (
                    update_fields
                    | (
                        {'managers_id': managers_id}
                        if managers_id is not None
                        else {}
                    )
                ),
            },
        )
        return db_obj
