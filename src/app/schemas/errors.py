"""Схемы данных для работы с ошибками."""

from pydantic import BaseModel


class CustomError(BaseModel):
    """Схема ошибок."""

    code: int
    message: str
