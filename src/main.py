"""Главный модуль приложения FastAPI.

Настраивает:
- маршруты,
- middleware,
- жизненный цикл,
- логирование,
- DI-контейнер.
"""

from contextlib import asynccontextmanager
from time import perf_counter
from typing import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from loguru import logger
from starlette.middleware.base import RequestResponseEndpoint

from app.api.routers import main_router
from app.core.config import settings
from app.core.constants import SYSTEM_USERNAME, SYSTEM_USER_ID
from app.core.db import AsyncSessionLocal
from app.core.init_db import create_first_users
from app.core.jwt_security import token_service
from app.core.logging import configure_logging, contextualize_user
from app.crud.user import user_crud
from containers import Container

configure_logging(
    level=settings.log_level,
    log_file=settings.log_file,
    rotation=settings.log_rotation,
    retention=settings.log_retention,
)


def build_docs_description() -> str:
    """Собрать описание Swagger с полезными ссылками."""
    description = settings.app_description

    if settings.server_ip:
        description += (
            '\n\n## Полезные ссылки\n\n'
            f'- [Flower](http://{settings.server_ip}:5555)\n'
            f'- [RabbitMQ](http://{settings.server_ip}:15672)\n'
        )

    return description


async def _resolve_request_user(request: Request) -> tuple[str, str]:
    """Определить пользователя из Bearer-токена для контекста логов."""
    authorization = request.headers.get('Authorization', '')
    if not authorization.startswith('Bearer '):
        return SYSTEM_USER_ID, SYSTEM_USERNAME

    token = authorization.removeprefix('Bearer ').strip()
    if not token:
        return SYSTEM_USER_ID, SYSTEM_USERNAME

    try:
        token_data = token_service.verify_access_token(token)
    except HTTPException:
        return SYSTEM_USER_ID, SYSTEM_USERNAME

    async with AsyncSessionLocal() as session:
        user = await user_crud.get(session, token_data.user_id)

    if user is None:
        return SYSTEM_USER_ID, SYSTEM_USERNAME

    return str(user.id), user.username


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Логировать жизненный цикл приложения."""
    try:
        async with AsyncSessionLocal() as session:
            await create_first_users(session)
        with contextualize_user():
            logger.info('Инициализация данных завершена')
    except Exception:
        with contextualize_user():
            logger.exception(
                'Критическая ошибка при инициализации.Приложение не запущено.',
            )
        raise

    with contextualize_user():
        logger.info('Приложение запущено')
    yield
    with contextualize_user():
        logger.info('Приложение завершило работу')


app = FastAPI(
    title=settings.app_title,
    description=build_docs_description(),
    lifespan=lifespan,
)

container = Container()
container.config.from_dict(
    {
        'database_url': settings.database_url,
        'app_title': settings.app_title,
        'app_description': settings.app_description,
        'secret': settings.secret,
    },
)

container.wire(
    modules=[
        'app.api.endpoints.action',
        'app.api.endpoints.cafe',
        'app.api.endpoints.table',
        'app.api.endpoints.time_slot',
        'app.api.endpoints.booking',
        'app.api.endpoints.user',
        'app.api.endpoints.auth',
        'app.api.endpoints.media',
        'app.api.endpoints.dish',
        'app.api.dependencies',
        'app.services.auth',
        'app.services.cafe',
    ],
)

app.container = container


@app.middleware('http')
async def log_requests(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """Логировать каждый HTTP-запрос и его результат."""
    correlation_id = request.headers.get('X-Request-ID') or str(uuid4())
    request.state.correlation_id = correlation_id
    user_id, username = await _resolve_request_user(request)

    with contextualize_user(
        user_id=user_id,
        username=username,
        correlation_id=correlation_id,
    ):
        started_at = perf_counter()
        logger.info(
            'HTTP {method} {path} started request_id={request_id}',
            method=request.method,
            path=request.url.path,
            request_id=correlation_id,
        )
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (perf_counter() - started_at) * 1000
            logger.exception(
                'HTTP {method} {path} failed in {elapsed_ms:.2f} ms '
                'request_id={request_id}',
                method=request.method,
                path=request.url.path,
                elapsed_ms=elapsed_ms,
                request_id=correlation_id,
            )
            raise

        elapsed_ms = (perf_counter() - started_at) * 1000
        response.headers['X-Request-ID'] = correlation_id
        logger.info(
            '{method} {path} -> {status_code} in {elapsed_ms:.2f} ms '
            'request_id={request_id}',
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
            request_id=correlation_id,
        )
        return response


app.include_router(main_router)
