"""Модель блюда для меню кафе и его связь с заведениями."""

from __future__ import annotations

from typing import List

from sqlalchemy import UUID, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DISH_MAX_LENGTH
from app.core.db import Base, CommonMixin
from app.schemas.types import (
    validate_description,
    validate_dish_name,
    validate_price,
)
from app.validators.orm_models_validator import create_validator_mixin

from .cafe import Cafe

DishValidatorMixin = create_validator_mixin({
    'name': validate_dish_name,
    'description': validate_description,
    'price': validate_price,
})


class Dish(CommonMixin, DishValidatorMixin, Base):
    """Модель блюда."""

    name: Mapped[str] = mapped_column(
        String(DISH_MAX_LENGTH),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    photo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    cafes: Mapped[List[Cafe]] = relationship(
        Cafe,
        secondary='cafe_dish',
        back_populates='dishes',
        lazy='selectin',
    )
