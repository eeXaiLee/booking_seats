"""Сервис для работы с медиафайлами.

Обрабатывает загрузку, конвертацию и сохранение изображений.
"""

import io
import uuid
from pathlib import Path

import aiofiles
from PIL import Image
from fastapi import UploadFile

from app.core.config import settings


class MediaService:
    """Сервис для работы с изображениями.

    Предоставляет методы для обработки, сохранения и получения изображений.
    Все изображения конвертируются в формат JPG и сохраняются с UUID именем.
    """

    # Константы класса
    MEDIA_DIR = Path(settings.media_dir)
    MAX_FILE_SIZE = settings.max_image_size
    ALLOWED_MIME_TYPES = set(settings.allowed_image_types)
    ALLOWED_EXTENSIONS = set(settings.allowed_extentions)
    JPEG_QUALITY = settings.jpeg_quality

    @classmethod
    def ensure_dir(cls) -> None:
        """Создать директорию для изображений, если её нет.

        Создает все необходимые родительские директории.
        """
        cls.MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    async def process_image(cls, file: UploadFile, content: bytes) -> bytes:
        """Обработка изображения.

        Выполняет:
        - Проверку расширения файла
        - Конвертацию в RGB (для JPG формата)
        - Оптимизацию и сохранение в JPG

        Args:
            file: Загруженный файл
            content: Содержимое файла в байтах

        Returns:
            bytes: Обработанное изображение в формате JPG

        Raises:
            ValueError:Если формат файла не поддерживается или ошибка обработки

        """
        # Проверка расширения файла
        file_extension = Path(file.filename or '').suffix.lower()
        if file_extension not in cls.ALLOWED_EXTENSIONS:
            raise ValueError(
                f'Неподдерживаемый формат файла. Разрешены: JPG, PNG.'
                f'Получен: {file_extension}',
            )

        try:
            # Открытие изображения
            image = Image.open(io.BytesIO(content))

            # Конвертация в RGB (необходимо для JPG)
            if image.mode != 'RGB':
                if image.mode in ('RGBA', 'LA', 'P'):
                    # Для изображений с прозрачностью создаем белый фон
                    rgb_image = Image.new('RGB', image.size, (255, 255, 255))

                    if image.mode == 'RGBA':
                        rgb_image.paste(image, mask=image.split()[-1])
                    elif image.mode == 'LA':
                        rgb_image.paste(
                            image.convert('RGBA'),
                            mask=image.split()[-1],
                        )
                    else:
                        rgb_image.paste(image.convert('RGBA'))

                    image = rgb_image
                else:
                    image = image.convert('RGB')

            # Сохранение в JPG с оптимизацией
            output_buffer = io.BytesIO()
            image.save(
                output_buffer,
                format='JPEG',
                quality=cls.JPEG_QUALITY,
                optimize=True,
                progressive=True,
            )

            return output_buffer.getvalue()

        except Exception as error:
            raise ValueError(
                f'Не удалось обработать изображение: {str(error)}',
            )

    @classmethod
    async def save_image(
        cls,
        image_data: bytes,
    ) -> uuid.UUID:
        """Сохранить изображение на диск с UUID именем.

        Args:
            image_data: Изображение в байтах

        Returns:
            uuid.UUID: UUID сохраненного файла

        """
        # Создание директории при необходимости
        cls.ensure_dir()

        # Генерация UUID для файла
        image_id = uuid.uuid4()
        file_path = cls.MEDIA_DIR / f'{image_id}.jpg'

        # Асинхронное сохранение файла с помощью aiofiles
        async with aiofiles.open(file_path, 'wb') as file:
            await file.write(image_data)

        return image_id

    @classmethod
    def get_path(cls, image_id: uuid.UUID) -> Path:
        """Получить путь к изображению по ID.

        Args:
            image_id: UUID изображения

        Returns:
            Path: Путь к файлу изображения

        """
        return cls.MEDIA_DIR / f'{image_id}.jpg'
