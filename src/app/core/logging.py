"""Модуль настройки логирования с интеграцией Loguru и поддержкой аудита."""

import json
import logging
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from loguru import logger

from app.core.constants import SYSTEM_USERNAME, SYSTEM_USER_ID

LOG_FORMAT = (
    '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | '
    '<level>{level: <8}</level> | '
    'user=<cyan>{extra[username]}</cyan>:'
    '<cyan>{extra[user_id]}</cyan> | '
    'corr=<magenta>{extra[correlation_id]}</magenta> | '
    '<cyan>{name}</cyan>:<cyan>{function}</cyan>:'
    '<cyan>{line}</cyan> - <level>{message}</level>'
)


class InterceptHandler(logging.Handler):
    """Перенаправляет стандартные логи Python в Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Обработать запись стандартного логгера."""
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def configure_logging(
    level: str,
    log_file: str,
    rotation: str,
    retention: str | int,
    enqueue: bool = True,
) -> None:
    """Настроить Loguru для приложения и стандартных логгеров."""
    logger.remove()
    logger.configure(
        extra={
            'user_id': SYSTEM_USER_ID,
            'username': SYSTEM_USERNAME,
            'correlation_id': '-',
        },
    )
    logger.add(
        sys.stdout,
        level=level.upper(),
        enqueue=enqueue,
        backtrace=True,
        diagnose=False,
        format=LOG_FORMAT,
    )

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_path,
        level=level.upper(),
        rotation=rotation,
        retention=_normalize_retention(retention),
        enqueue=enqueue,
        backtrace=True,
        diagnose=False,
        encoding='utf-8',
        format=LOG_FORMAT,
    )

    intercept_handler = InterceptHandler()
    logging.basicConfig(handlers=[intercept_handler], level=0, force=True)

    for logger_name in (
        'celery',
        'celery.app.trace',
        'uvicorn',
        'uvicorn.error',
        'uvicorn.access',
        'fastapi',
        'kombu',
    ):
        current_logger = logging.getLogger(logger_name)
        current_logger.handlers = [intercept_handler]
        current_logger.propagate = False


def _normalize_retention(retention: str | int) -> str | int:
    """Преобразовать retention к формату, который понимает Loguru."""
    if isinstance(retention, int):
        return retention

    normalized_retention = retention.strip()
    if normalized_retention.isdigit():
        return int(normalized_retention)

    parts = normalized_retention.lower().split()
    if (
        len(parts) == 2
        and parts[0].isdigit()
        and parts[1]
        in {
            'file',
            'files',
        }
    ):
        return int(parts[0])

    return normalized_retention


def contextualize_user(
    user_id: int | str | None = None,
    username: str | None = None,
    correlation_id: str | None = None,
) -> Any:
    """Подготовить пользовательский контекст для логов."""
    resolved_user_id = str(user_id) if user_id is not None else SYSTEM_USER_ID
    resolved_username = username or SYSTEM_USERNAME
    resolved_correlation_id = correlation_id or '-'
    return logger.contextualize(
        user_id=resolved_user_id,
        username=resolved_username,
        correlation_id=resolved_correlation_id,
    )


def log_audit_event(
    event: str,
    details: Mapping[str, Any] | None = None,
    level: str = 'INFO',
) -> None:
    """Записать аудит-событие в централизованный лог."""
    serialized_details = json.dumps(
        details or {},
        ensure_ascii=False,
        default=str,
        sort_keys=True,
    )
    logger.log(
        level.upper(),
        '{event} | details={details}',
        event=event,
        details=serialized_details,
    )
