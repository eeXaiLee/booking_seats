"""Сервисный слой для работы с кафе."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import CafeCRUD
from app.models import Cafe, Table
from app.schemas import CafeUpdate


class CafeService:
    """Сервис для работы с кафе."""

    async def deactivate_cafe(
        self,
        session: AsyncSession,
        cafe: Cafe,
        cafe_crud: CafeCRUD,
    ) -> Cafe:
        """Каскадно деактивировать кафе и связанные с ним столы."""
        result = await session.execute(
            select(Table).where(
                Table.cafe_id == cafe.id,
                Table.is_active.is_(True),
            ),
        )
        tables = list(result.scalars().all())

        for table in tables:
            table.is_active = False

        if tables:
            session.add_all(tables)

        return await cafe_crud.update(
            db=session,
            db_obj=cafe,
            obj_in=CafeUpdate(is_active=False),
        )
