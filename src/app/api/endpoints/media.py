"""Эндпоинты для работы с медиафайлами."""

from typing import AsyncGenerator

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse

from app.api.dependencies import AdminAndManagerDependency
from app.core.config import settings
from app.core.constants import MEDIA_SAVE_ERROR
from app.schemas.media import MediaInfo
from app.utils.media import MediaService
from app.validators.media import MediaValidator

router = APIRouter()


async def read_in_chunks(
    file: UploadFile,
    chunk_size: int = 1024 * 1024,
) -> AsyncGenerator[bytes, None]:
    """Чтение файла порциями.

    Args:
        file: Загружаемый файл
        chunk_size: Размер порции в байтах (по умолчанию 1MB)

    Yields:
        bytes: Очередная порция данных

    """
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        yield chunk


@router.get(
    '/{media_id}',
    summary='Возвращает изображение в бинарном формате',
    description='Получение изображения по его ID.',
)
async def get_media(
    media_id: str,
) -> FileResponse:
    """Получение изображения по ID.

    - **media_id**: UUID изображения
    - **Возвращает**: изображение в формате JPG (бинарные данные)
    - **Доступно**: всем пользователям (без авторизации)
    """
    # Валидация UUID
    media_uuid = MediaValidator.validate_uuid_format(media_id)

    # Получение пути к файлу
    file_path = MediaService.get_path(media_uuid)

    # Валидация существования файла
    MediaValidator.validate_file_exists(file_path)

    return FileResponse(
        path=file_path,
        media_type='image/jpeg',
        filename=f'{media_id}.jpg',
        headers={
            'Content-Disposition': 'inline',
            'Cache-Control': 'public, max-age=86400',  # кэш на 24 часа
        },
    )


@router.post(
    '/',
    response_model=MediaInfo,
    status_code=status.HTTP_200_OK,
    summary='Загрузка изображения',
    description=(
        'Загрузка изображения на сервер. '
        'Поддерживаются форматы jpg, png. '
        'Размер файла не более 5Мб. '
        'Только для администраторов и менеджеров'
    ),
)
async def upload_media(
    current_user: AdminAndManagerDependency,
    file: UploadFile = File(
        ...,
        description='Загружаемый файл (JPG или PNG, макс. 5MB)',
        media_type='multipart/form-data',
    ),
) -> MediaInfo:
    """Загрузка изображения на сервер с проверкой без полной загрузки в память.

    Доступно только администраторам и менеджерам.
    """
    # 1. Проверяем метаданные
    MediaValidator.validate_mime_type(file.content_type)
    MediaValidator.validate_file_extension(file.filename)

    max_size_mb = settings.max_image_size // (1024 * 1024)

    file_size = 0
    content = bytearray()

    # 2. Читаем порциями
    async for chunk in read_in_chunks(file):
        file_size += len(chunk)

        if file_size > settings.max_image_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f'Размер файла превышает {max_size_mb} MB',
            )

        content.extend(chunk)

    # 3. Проверяем целостность
    await MediaValidator.validate_image_integrity(content)

    try:
        # 4. Обрабатываем изображение (конвертация в JPG)
        image_data = await MediaService.process_image(file, content)

        # 5. Сохраняем на диск
        media_id = await MediaService.save_image(image_data)
        return MediaInfo(media_id=media_id)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=MEDIA_SAVE_ERROR,
        )
