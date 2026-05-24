"""Модуль с базой данных и асинхронными сессиями SQLAlchemy."""

from datetime import datetime
from typing import Annotated, AsyncGenerator

from sqlalchemy import Boolean, DateTime, Integer, MetaData, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
)

import app.core.constants as const
from app.core.config import settings

timestamp = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP'),
    ),
]


class Base(DeclarativeBase):
    """Базовый класс моделей."""

    metadata = MetaData(naming_convention=const.convention)

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        """Имя таблицы."""
        return cls.__name__.lower()


class CommonMixin:
    """Общие поля для всех моделей."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[timestamp]
    updated_at: Mapped[timestamp] = mapped_column(
        onupdate=text('CURRENT_TIMESTAMP'),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


engine = create_async_engine(settings.database_url)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронный генератор сессий SQLAlchemy."""
    async with AsyncSessionLocal() as async_session:
        try:
            yield async_session
        except SQLAlchemyError:
            await async_session.rollback()
            raise
