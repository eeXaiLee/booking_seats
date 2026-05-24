"""Модель стола в кафе."""

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, CommonMixin
from app.schemas.types import validate_description
from app.validators.orm_models_validator import create_validator_mixin

TableValidatorMixin = create_validator_mixin({
    'description': validate_description,
})


class Table(CommonMixin, TableValidatorMixin, Base):
    """Стол."""

    cafe_id: Mapped[int] = mapped_column(
        ForeignKey('cafe.id'),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    seat_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f'Стол {self.id} в кафе {self.cafe_id}'
