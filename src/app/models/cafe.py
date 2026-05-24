"""Модель кафе и его связь с менеджерами, блюдами и акциями."""

from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.core.constants import (
    ADDRESS_MAX_LENGTH,
    CAFE_NAME_MAX_LENGTH,
    PHONE_MAX_LENGTH,
)
from app.core.db import Base, CommonMixin
from app.schemas.types import (
    validate_description,
    validate_name,
    validate_phone,
)
from app.validators.orm_models_validator import create_validator_mixin

CafeValidatorMixin = create_validator_mixin({
    'name': validate_name,
    'phone': validate_phone,
    'description': validate_description,
})


class Cafe(CommonMixin, CafeValidatorMixin, Base):
    """Кафе."""

    name: Mapped[str] = mapped_column(
        String(CAFE_NAME_MAX_LENGTH),
        nullable=False,
    )
    address: Mapped[str] = mapped_column(
        String(ADDRESS_MAX_LENGTH),
        nullable=False,
    )
    phone: Mapped[str] = mapped_column(
        String(PHONE_MAX_LENGTH),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    photo_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )

    managers = relationship(
        'User',
        secondary='cafe_manager',
        back_populates='cafes',
    )
    dishes = relationship(
        'Dish',
        secondary='cafe_dish',
        back_populates='cafes',
    )
    actions = relationship(
        'Action',
        secondary='cafe_action',
        back_populates='cafes',
    )
    tables = relationship('Table')

    def __repr__(self) -> str:
        return f'Кафе {self.id}: {self.name}'


class CafeManager(Base):
    """Связь кафе и менеджера."""

    __tablename__ = 'cafe_manager'

    cafe_id: Mapped[int] = mapped_column(
        ForeignKey('cafe.id'),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id'),
        primary_key=True,
    )

    def __repr__(self) -> str:
        return f'Связь кафе {self.cafe_id} и менеджера {self.user_id}'


class CafeDish(Base):
    """Связь кафе и блюда."""

    __tablename__ = 'cafe_dish'

    cafe_id: Mapped[int] = mapped_column(
        ForeignKey('cafe.id'),
        primary_key=True,
    )
    dish_id: Mapped[int] = mapped_column(
        ForeignKey('dish.id'),
        primary_key=True,
    )

    def __repr__(self) -> str:
        return f'Связь кафе {self.cafe_id} и блюда {self.dish_id}'


class CafeAction(Base):
    """Связь кафе и акции."""

    __tablename__ = 'cafe_action'

    cafe_id: Mapped[int] = mapped_column(
        ForeignKey('cafe.id'),
        primary_key=True,
    )
    action_id: Mapped[int] = mapped_column(
        ForeignKey('action.id'),
        primary_key=True,
    )

    def __repr__(self) -> str:
        return f'Связь кафе {self.cafe_id} и акции {self.action_id}'
