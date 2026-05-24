"""Базовый класс CRUD для операций с моделью."""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import Base
from app.core.logging import log_audit_event

Model = TypeVar('Model', bound=Base)
CreateSchema = TypeVar('CreateSchema', bound=BaseModel)
UpdateSchema = TypeVar('UpdateSchema', bound=BaseModel)


class CRUDBase(Generic[Model, CreateSchema, UpdateSchema]):
    """Базовый класс CRUD для операций с моделью.

    Предоставляет стандартные методы: get, create, update и др.
    """

    def __init__(self, model: Type[Model]) -> None:
        """Инициализация CRUD-класса с моделью SQLAlchemy."""
        self.model = model

    async def get(self, db: AsyncSession, obj_id: Any) -> Optional[Model]:
        """Получить объект по ID."""
        stmt = select(self.model).where(self.model.id == obj_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = settings.default_page_limit,
    ) -> List[Model]:
        """Получить список объектов с пагинацией."""
        limit = min(limit, settings.max_page_limit)
        stmt = select(self.model).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: Union[CreateSchema, Dict[str, Any]],
    ) -> Model:
        """Создать новый объект."""
        if isinstance(obj_in, dict):
            obj_in_data = obj_in.copy()
        else:
            obj_in_data = obj_in.model_dump(mode='python')
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        log_audit_event(
            event=f'Создана запись в таблице {self.model.__tablename__}',
            details={
                'id': getattr(db_obj, 'id', None),
                'parameters': jsonable_encoder(obj_in_data),
            },
        )
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Model,
        obj_in: Union[UpdateSchema, Dict[str, Any]],
    ) -> Model:
        """Обновить объект."""
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        log_audit_event(
            event=f'Обновлена запись в таблице {self.model.__tablename__}',
            details={
                'id': getattr(db_obj, 'id', None),
                'parameters': update_data,
            },
        )
        return db_obj
