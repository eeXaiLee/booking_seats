"""Схемы данных для работы с блюдами."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.cafe import CafeShortInfo
from app.schemas.types import Description, DishName, Price


class DishBase(BaseModel):
    """Базовая схема блюда."""

    name: DishName = Field(
        ...,
        description='Название блюда. От 3 до 255 символов. '
        'Допустимы буквы, цифры, пробелы и знаки: -.,!?()',
    )
    description: Description = Field(
        ...,
        description='Описание блюда. От 1 до 500 символов',
    )
    photo_id: UUID = Field(..., description='ID фотографии')
    price: Price = Field(
        ...,
        description='Цена блюда. От 0.01 до 999999.99',
    )

    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            'example': {
                'name': 'Цезарь с курицей',
                'description': 'Классический салат Цезарь с курицей и соусом',
                'photo_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                'price': 450.00,
            },
        },
    )


class DishCreate(DishBase):
    """Схема для создания блюда."""

    cafes_id: List[int] = Field(
        ...,
        min_length=1,
        description='ID кафе, где будет доступно блюдо',
        examples=[[1, 2, 3]],
    )

    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            'example': {
                'name': 'Цезарь с курицей',
                'description': 'Классический салат Цезарь с курицей и соусом',
                'photo_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                'price': 450.00,
                'cafes_id': [1, 2, 3],
            },
        },
    )


class DishUpdate(BaseModel):
    """Схема для обновления блюда."""

    name: Optional[DishName] = Field(
        None,
        description='Название блюда. От 3 до 255 символов',
    )
    description: Optional[Description] = Field(
        None,
        description='Описание блюда. От 1 до 500 символов',
    )
    photo_id: Optional[UUID] = None
    price: Optional[Price] = Field(
        None,
        description='Цена блюда. От 0.01 до 999999.99',
    )
    cafes_id: Optional[List[int]] = Field(None, min_length=1)
    is_active: Optional[bool] = None

    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            'example': {
                'name': 'Цезарь с креветками',
                'price': 550.00,
                'is_active': True,
            },
        },
    )


class DishInfo(DishBase):
    """Схема для информации о блюде."""

    id: int = Field(..., description='ID блюда')
    cafes: List[CafeShortInfo] = Field(
        ...,
        description='Кафе, где доступно блюдо',
    )
    is_active: bool = Field(..., description='Активно ли блюдо')
    created_at: datetime = Field(..., description='Дата создания')
    updated_at: datetime = Field(..., description='Дата обновления')

    model_config = ConfigDict(from_attributes=True)
