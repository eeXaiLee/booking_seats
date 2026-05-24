"""Модуль с эндпоинтами для аутентификации и управления токенами."""

from dependency_injector.wiring import inject
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
)

from app.api.dependencies import (
    CRUDUserDependency,
    SessionDependency,
    TokenServiceDependency,
)
from app.core.constants import JWT_USER_ID
from app.core.logging import contextualize_user, log_audit_event
from app.schemas import Token

router = APIRouter()


@router.post(
    '/login',
    response_model=Token,
    summary='Вход в систему',
)
@inject
async def login(
    session: SessionDependency,
    crud: CRUDUserDependency,
    token_service: TokenServiceDependency,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """Аутентифицирует пользователя и возвращает пару токенов."""
    user = await crud.get_by_attributes(
        session,
        email=form_data.username,
    )

    if user is None or not await crud.verify_password(
        form_data.password,
        user.password,
    ):
        with contextualize_user():
            log_audit_event(
                event='Неуспешная аутентификация пользователя',
                details={'email': form_data.username},
                level='WARNING',
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Некорректный email или пароль',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token, refresh_token = await token_service.create_tokens(
        data={
            JWT_USER_ID: user.id,
        },
        session=session,
    )
    with contextualize_user(user_id=user.id, username=user.username):
        log_audit_event(
            event='Успешная аутентификация пользователя',
            details={'email': user.email},
        )
    response.set_cookie(
        'refresh_token',
        refresh_token,
        httponly=True,
    )
    return Token(access_token=access_token)


@router.post(
    '/refresh',
    response_model=Token,
    summary='Обновление токенов',
)
@inject
async def refresh(
    request: Request,
    response: Response,
    token_service: TokenServiceDependency,
    session: SessionDependency,
    crud: CRUDUserDependency,
) -> Token:
    """Обновляет пару токенов по refresh токену."""
    refresh_token = request.cookies.get('refresh_token')

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Нет refresh токена',
        )

    token_data = await token_service.verify_refresh_token(
        refresh_token,
        session,
    )
    user = await crud.get(session, token_data.user_id)
    new_access_token, new_refresh_token = await token_service.refresh_tokens(
        refresh_token,
        session,
    )
    response.set_cookie(
        'refresh_token',
        new_refresh_token,
        httponly=True,
    )
    with contextualize_user(
        user_id=token_data.user_id,
        username=user.username if user else None,
    ):
        log_audit_event(event='Обновлена пара токенов пользователя')
    return Token(access_token=new_access_token)
