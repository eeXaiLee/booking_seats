"""Схемы данных для работы с временными слотами."""

from datetime import datetime, time, timedelta

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)
from typing_extensions import Self

from app.core.constants import (
    DESCRIPTION_MAX_LENGTH,
    TIME_SLOT_ERROR,
)
from app.schemas import CafeShortInfo
from app.schemas.types import Description

START_TIME = (datetime.now() + timedelta(minutes=10)).strftime('%H:%M')
END_TIME = (datetime.now() + timedelta(hours=1)).strftime('%H:%M')


class TimeSlotBase(BaseModel):
    """Базовая модель временных слотов."""

    start_time: time = Field(..., examples=[START_TIME])
    end_time: time = Field(..., examples=[END_TIME])
    description: str = Field(..., max_length=DESCRIPTION_MAX_LENGTH)

    model_config = ConfigDict(extra='forbid')


class TimeSlotCreate(TimeSlotBase):
    """Создание временных слотов."""

    cafe_id: int

    @model_validator(mode='after')
    def check_start_time_before_end_time(self) -> Self:
        """Валидация полей времени в слотах.

        Конец времени слота не должен быть позже его начала.
        """
        if self.start_time is None or self.end_time is None:
            return self
        if self.start_time >= self.end_time:
            error = TIME_SLOT_ERROR
            raise ValueError(error)
        return self


class TimeSlotShortInfo(TimeSlotBase):
    """Короткая информация временных слотов."""

    id: int


class TimeSlotInfo(TimeSlotShortInfo):
    """Полная информация временных слотов."""

    cafe: CafeShortInfo
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra='forbid', from_attributes=True)


class TimeSlotUpdate(TimeSlotCreate):
    """Обновление временных слотов."""

    cafe_id: int | None = None
    start_time: time | None = None
    end_time: time | None = None
    description: Description | None = Field(
        None,
        description='Описание для временного слота. '
        'Максимальная длина 500 символов',
    )
    is_active: bool | None = None
