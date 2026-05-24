"""Валидаторы для медиафайлов."""

import io
from pathlib import Path
from typing import Optional
from uuid import UUID

from PIL import Image
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.constants import (
    MEDIA_CORRUPTED_IMAGE,
    MEDIA_INVALID_UUID,
    MEDIA_NOT_FOUND,
)


class MediaValidator:
    """Валидатор для медиафайлов."""

    @staticmethod
    def validate_mime_type(content_type: Optional[str]) -> None:
        """Проверить MIME тип файла."""
        if (
            not content_type
            or content_type not in settings.allowed_image_types
        ):
            allowed = ', '.join(settings.allowed_image_types)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Недопустимый тип файла. Разрешены: {allowed}.',
            )

    @staticmethod
    def validate_file_extension(filename: Optional[str]) -> None:
        """Проверить расширение файла."""
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Имя файла не указано',
            )

        ext = Path(filename).suffix.lower()
        if ext not in settings.allowed_extentions:
            allowed = ', '.join(settings.allowed_extentions)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Недопустимое расширение. Разрешены: {allowed}',
            )

    @staticmethod
    async def validate_image_integrity(content: bytes) -> None:
        """Проверить целостность изображения."""
        try:
            Image.open(io.BytesIO(content))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MEDIA_CORRUPTED_IMAGE,
            )

    @staticmethod
    def validate_uuid_format(uuid_str: str) -> UUID:
        """Проверить формат UUID."""
        try:
            return UUID(uuid_str)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=MEDIA_INVALID_UUID,
            ) from exc

    @staticmethod
    def validate_file_exists(file_path: Path) -> None:
        """Проверить существование файла."""
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MEDIA_NOT_FOUND,
            )
