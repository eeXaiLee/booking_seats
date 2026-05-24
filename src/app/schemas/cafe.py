"""Схемы данных для работы с кафе."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import (
    ADDRESS_MAX_LENGTH,
)
from app.schemas.types import Description, Name, PhoneNumber

from .user import UserShortInfo


class CafeCreate(BaseModel):
    """Создание кафе."""

    name: Name
    address: str = Field(..., max_length=ADDRESS_MAX_LENGTH)
    phone: PhoneNumber
    description: Description = Field(
        ...,
        description='Описание кафе. От 1 до 500 символов',
    )
    photo_id: UUID
    managers_id: list[int]

    model_config = ConfigDict(extra='forbid')


class CafeUpdate(BaseModel):
    """Обновление кафе."""

    name: Name | None = None
    address: str | None = Field(None, max_length=ADDRESS_MAX_LENGTH)
    phone: PhoneNumber | None = None
    description: Description | None = Field(
        None,
        description='Описание кафе. От 1 до 500 символов',
    )
    photo_id: UUID | None = None
    managers_id: list[int] | None = None
    is_active: bool | None = None

    model_config = ConfigDict(extra='forbid')


class CafeShortInfo(BaseModel):
    """Краткая информация о кафе."""

    id: int
    name: str
    address: str
    phone: str
    description: str
    photo_id: UUID

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class CafeInfo(CafeShortInfo):
    """Полная информация о кафе."""

    managers: list[UserShortInfo]
    is_active: bool
    created_at: datetime
    updated_at: datetime
