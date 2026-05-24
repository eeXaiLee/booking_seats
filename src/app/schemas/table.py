"""Схемы данных для работы со столами."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.types import Description, SeatNumber


class TableCreate(BaseModel):
    """Создание стола."""

    cafe_id: int
    description: Description = Field(
        ...,
        description='Описание стола. От 1 до 500 символов',
    )
    seat_number: SeatNumber

    model_config = ConfigDict(extra='forbid')


class TableUpdate(BaseModel):
    """Обновление стола."""

    cafe_id: int | None = None
    description: Description | None = Field(
        None,
        description='Описание стола. От 1 до 500 символов',
    )
    seat_number: SeatNumber | None = None
    is_active: bool | None = None

    model_config = ConfigDict(extra='forbid')


class TableShortInfo(BaseModel):
    """Краткая информация о столе."""

    id: int
    description: str
    seat_number: int

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class TableInfo(TableShortInfo):
    """Полная информация о столе."""

    is_active: bool
    created_at: datetime
    updated_at: datetime
