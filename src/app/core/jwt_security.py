"""Модуль для работы с JWT-токенами: создание, верификация, отзыв."""

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import (  # Тут добавил импортов
    ACCESS_TOKEN_TYPE,
    ENCODING,
    INVALID_TOKEN,
    INVALID_TOKEN_JTI_OR_USER_ID,
    INVALID_TOKEN_SIGNATURE,
    INVALID_TOKEN_TYPE,
    INVALID_TOKEN_USER_ID,
    JWT_EXP,
    JWT_JTI,
    JWT_TYPE,
    JWT_USER_ID,
    REFRESH_TOKEN_TYPE,
    TOKEN_EXPIRED,
    TOKEN_NOT_FOUND,
    TOKEN_REVOKED,
)
from app.models.refresh_token import RefreshToken
from app.schemas.user import TokenData


class InvalidTokenError(HTTPException):
    """Ошибка невалидного токена."""


class ExpiredTokenError(HTTPException):
    """Ошибка истекшего токена."""


class RevokedTokenError(HTTPException):
    """Ошибка отозванного токена."""


class TokenService:
    """Сервис для работы с токенами."""

    def __init__(
        self,
        secret_key: str,
        refresh_secret_key: str,
        algorithm: str,
        access_exp_minutes: int,
        refresh_exp_days: int,
    ) -> None:
        """Инициализация настроек для JWT-токенов."""
        self.secret_key = secret_key
        self.refresh_secret_key = refresh_secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_exp_minutes
        self.refresh_token_expire_days = refresh_exp_days

    async def create_tokens(
        self,
        data: dict,
        session: AsyncSession,
    ) -> tuple[str, str]:
        """Создаёт пару токенов."""
        access_token_data = data.copy()
        refresh_token_data = data.copy()
        now = datetime.now(timezone.utc)
        access_expire = now + timedelta(
            minutes=self.access_token_expire_minutes,
        )
        refresh_expire = now + timedelta(
            days=self.refresh_token_expire_days,
        )
        access_token_data.update({
            JWT_EXP: access_expire,
            JWT_TYPE: ACCESS_TOKEN_TYPE,
        })
        access_token = jwt.encode(
            access_token_data,
            self.secret_key,
            self.algorithm,
        )
        db_token = RefreshToken(
            user_id=data[JWT_USER_ID],
            expires_at=refresh_expire,
        )
        session.add(db_token)
        await session.flush()

        jti = str(db_token.jti)
        refresh_token_data.update({
            JWT_EXP: refresh_expire,
            JWT_TYPE: REFRESH_TOKEN_TYPE,
            JWT_JTI: jti,
        })
        refresh_token = jwt.encode(
            refresh_token_data,
            self.refresh_secret_key,
            self.algorithm,
        )

        db_token.token_hash = self._hash_token(refresh_token)
        await session.commit()
        return access_token, refresh_token

    def _hash_token(self, refresh_token: str) -> str:
        """Хеширует токен для хранения в БД."""
        return bcrypt.hashpw(
            refresh_token.encode(ENCODING)[:72],
            bcrypt.gensalt(),
        ).decode(
            ENCODING,
        )

    def _verify_token_hash(self, refresh_token: str, hashed: str) -> bool:
        """Проверяет соответствие токена хешу."""
        return bcrypt.checkpw(
            refresh_token.encode(ENCODING)[:72],
            hashed.encode(ENCODING),
        )

    def _decode_token(self, token: str, secret: str) -> dict:
        """Декодирует токен."""
        return jwt.decode(
            token,
            secret,
            algorithms=[self.algorithm],
        )

    def _validate_payload(self, payload: dict) -> TokenData:
        """Валидирует токен."""
        token_data = TokenData(**payload)

        if token_data.user_id is None:
            raise InvalidTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_TOKEN_USER_ID,
            )
        return token_data

    async def _verify_in_db(
        self,
        jti: str,
        refresh_token: str,
        session: AsyncSession,
    ) -> None:
        """Проверяет токен в БД."""
        result = await session.execute(
            select(RefreshToken).where(
                RefreshToken.jti == jti,
            ),
        )
        db_token = result.scalar_one_or_none()

        if db_token is None:
            raise InvalidTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=TOKEN_NOT_FOUND,
            )

        if db_token.revoked:
            raise InvalidTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=TOKEN_REVOKED,
            )

        if db_token.expires_at < datetime.now(timezone.utc):
            raise ExpiredTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=TOKEN_EXPIRED,
            )

        if not self._verify_token_hash(refresh_token, db_token.token_hash):
            raise InvalidTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_TOKEN_SIGNATURE,
            )

    def verify_access_token(
        self,
        access_token: str,
    ) -> TokenData:
        """Верифицирует access токен."""
        try:
            payload = self._decode_token(access_token, self.secret_key)

            if payload.get('type') != ACCESS_TOKEN_TYPE:
                raise InvalidTokenError(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=INVALID_TOKEN_TYPE,
                )

            return self._validate_payload(payload)
        except JWTError as exc:
            raise InvalidTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_TOKEN,
            ) from exc

    async def verify_refresh_token(
        self,
        refresh_token: str,
        session: AsyncSession,
    ) -> TokenData:
        """Верифицирует refresh токен."""
        try:
            payload = self._decode_token(
                refresh_token,
                self.refresh_secret_key,
            )

            if payload.get('type') != REFRESH_TOKEN_TYPE:
                raise InvalidTokenError(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=INVALID_TOKEN_TYPE,
                )

            token_data = self._validate_payload(payload)

            if token_data.user_id is None or token_data.jti is None:
                raise InvalidTokenError(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=INVALID_TOKEN_JTI_OR_USER_ID,
                )

            await self._verify_in_db(
                payload[JWT_JTI],
                refresh_token,
                session,
            )
            return token_data
        except JWTError as exc:
            raise InvalidTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_TOKEN,
            ) from exc

    async def revoke_all_user_tokens(
        self,
        user_id: int,
        session: AsyncSession,
    ) -> None:
        """Отзывает все refresh токены пользователя."""
        result = await session.execute(
            select(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked.is_(False),
            ),
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.revoked = True
        await session.commit()

    async def revoke_token(
        self,
        refresh_token: str,
        session: AsyncSession,
    ) -> None:
        """Отзывает конкретный refresh токен."""
        try:
            payload = self._decode_token(
                refresh_token,
                self.refresh_secret_key,
            )
            jti = payload.get(JWT_JTI)

            result = await session.execute(
                select(RefreshToken).where(RefreshToken.jti == jti),
            )
            db_token = result.scalar_one_or_none()

            if db_token:
                db_token.revoked = True
                await session.commit()

        except JWTError as exc:
            raise InvalidTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_TOKEN,
            ) from exc

    async def refresh_tokens(
        self,
        refresh_token: str,
        session: AsyncSession,
    ) -> tuple[str, str]:
        """Обновляет пару токенов. Отзывает старый refresh и создаёт новый."""
        token_data = await self.verify_refresh_token(refresh_token, session)
        await self.revoke_token(refresh_token, session)
        new_access_token, new_refresh_token = await self.create_tokens(
            {JWT_USER_ID: token_data.user_id},
            session,
        )
        return new_access_token, new_refresh_token


token_service = TokenService(
    secret_key=settings.secret_key,
    refresh_secret_key=settings.refresh_secret_key,
    algorithm=settings.algorithm,
    access_exp_minutes=settings.access_token_expire_minutes,
    refresh_exp_days=settings.refresh_token_expire_days,
)
