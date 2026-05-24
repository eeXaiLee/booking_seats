"""Модель временного слота для бронирования в кафе."""

from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonMixin
from app.schemas.types import validate_description
from app.validators.orm_models_validator import create_validator_mixin

if TYPE_CHECKING:
    from app.models.cafe import Cafe

TimeSlotValidatorMixin = create_validator_mixin({
    'description': validate_description,
})


class TimeSlot(CommonMixin, TimeSlotValidatorMixin, Base):
    """Модель временных слотов."""

    __tablename__ = 'time_slot'

    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cafe.id'),
        nullable=False,
    )
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)

    cafe: Mapped['Cafe'] = relationship('Cafe')

    def __repr__(self) -> str:
        return f'Временной слот с {self.start_time} по {self.end_time}'
