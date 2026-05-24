"""Схемы для работы с пользователями."""

from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.types import Password, PhoneNumber, TgId, Username


class UserBase(BaseModel):
    """Базовая схема пользователя."""

    username: Username = Field(
        ...,
        description='Имя пользователя. От 3 символов, начинается с буквы, '
        'только латиница, цифры и _',
    )
    email: EmailStr = Field(
        ...,
        description='Электронная почта',
    )
    phone: PhoneNumber | None = Field(
        None,
        description='Номер телефона в формате +79XXXXXXXXX',
    )
    tg_id: TgId | None = Field(
        None,
        description='Telegram ID (числовой идентификатор)',
    )


class UserRole(IntEnum):
    """Роли пользователей."""

    ADMINISTRATOR = 2
    MANAGER = 1
    USER = 0


class UserCreate(UserBase):
    """Схема для создания пользователя."""

    password: Password = Field(
        description='Пароль минимум 6 символов, '
        'должен содержать хотя бы одну строчную букву, одну заглавную и цифру',
    )

    model_config = ConfigDict(extra='forbid')


class UserCreateByAdmin(UserCreate):
    """Схема для создания пользователя с ролью.

    Только для администраторов и менеджеров.
    """

    role: UserRole = Field(
        default=UserRole.USER,
        description='Роль пользователя: 0 - USER, '
        '1 - MANAGER, 2 - ADMINISTRATOR',
    )


class UserShortInfo(UserBase):
    """Схема для краткой информации о пользователе."""

    id: int
    username: str
    email: EmailStr
    phone: str | None = None
    tg_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserInfo(UserShortInfo):
    """Схема для получения полной информации о пользователе."""

    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdateOwn(UserBase):
    """Схема для обновления своих данных пользователя."""

    username: Username | None = Field(
        None,
        description='Имя пользователя. От 3 символов, '
        'начинается с буквы, только латиница, цифры и _',
    )
    email: EmailStr | None = Field(
        None,
        description='Электронная почта',
    )
    phone: PhoneNumber | None = Field(
        None,
        description='Номер телефона в формате +79XXXXXXXXX',
    )
    tg_id: TgId | None = Field(
        None,
        description='Telegram ID (числовой идентификатор)',
    )
    password: Password | None = Field(
        None,
        description='Пароль минимум 6 символов, '
        'должен содержать хотя бы одну строчную букву, одну заглавную и цифру',
    )

    model_config = ConfigDict(extra='forbid')


class UserUpdateByAdmin(UserUpdateOwn):
    """Схема для обновления данных пользователя с ролью и активностью.

    Только для администраторов и менеджеров.
    """

    role: UserRole | None = Field(
        None,
        description='Роль пользователя: '
        '0 - USER, 1 - MANAGER, 2 - ADMINISTRATOR',
    )
    is_active: bool | None = None


class Token(BaseModel):
    """Схема для возврата пары токенов."""

    access_token: str = Field(description='JWT токен доступа')
    # refresh_token: str = Field(description='JWT токен обновления')
    token_type: str = Field(
        default='bearer',
        description='Тип токена',
    )


class TokenData(BaseModel):
    """Схема для данных из токена."""

    user_id: int | None = Field(
        None,
        description='ID пользователя из токена',
    )
    jti: str | None = Field(
        None,
        description=('Уникальный идентификатор токена'),
    )
