"""Схемы данных для работы с акциями."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.cafe import CafeShortInfo
from app.schemas.types import Description


class ActionBase(BaseModel):
    """Базовая схема акции."""

    description: Description = Field(
        ...,
        description='Описание акции. От 1 до 500 символов',
    )
    photo_id: Optional[UUID] = Field(None, description='ID фотографии')

    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            'example': {
                'description': 'Описание самой выгодной акции!',
                'photo_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
            },
        },
    )


class ActionCreate(ActionBase):
    """Схема для создания акции."""

    cafes_id: List[int] = Field(
        ...,
        min_length=1,
        description='ID кафе, где планируется акция',
        examples=[[1, 2, 3]],
    )

    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            'example': {
                'description': 'Описание самой выгодной акции!',
                'photo_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                'cafes_id': [1, 2, 3],
            },
        },
    )


class ActionUpdate(BaseModel):
    """Схема для обновления акции."""

    description: Optional[Description] = Field(
        None,
        description='Описание акции. От 1 до 500 символов',
    )
    photo_id: Optional[UUID] = None
    cafes_id: Optional[List[int]] = Field(None, min_length=1)
    is_active: Optional[bool] = None

    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            'example': {
                'description': 'Обновленное описание акции',
                'photo_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                'cafes_id': [1, 2],
                'is_active': True,
            },
        },
    )


class ActionInfo(ActionBase):
    """Схема для информации об акции."""

    id: int = Field(..., description='ID акции')
    cafes: List[CafeShortInfo] = Field(
        ...,
        description='Кафе, где действует акция',
    )
    is_active: bool = Field(..., description='Активна ли акция')
    created_at: datetime = Field(..., description='Дата создания')
    updated_at: datetime = Field(..., description='Дата обновления')

    model_config = ConfigDict(from_attributes=True)
