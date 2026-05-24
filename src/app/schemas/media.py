"""Схемы данных для работы с медиафайлами."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MediaData(BaseModel):
    """Схема медиаданных.

    Attributes:
        file: Загружаемый файл в бинарном формате

    """

    file: Any = Field(..., description='Загружаемый файл')

    model_config = ConfigDict(
        json_schema_extra={
            'example': {
                'file': '(binary data)',
            },
        },
    )


class MediaInfo(BaseModel):
    """Информация о загруженном медиафайле.

    Attributes:
        media_id: UUID идентификатор загруженного изображения

    """

    media_id: UUID = Field(..., description='ID медиафайла')

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            'example': {
                'media_id': '123e4567-e89b-12d3-a456-426614174000',
            },
        },
    )
