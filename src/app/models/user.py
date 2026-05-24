"""Модель пользователя."""

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import (
    USER_EMAIL_MAX_LENGTH,
    USER_NAME_MAX_LENGTH,
    USER_PASSWORD_MAX_LENGTH,
    USER_PHONE_MAX_LENGTH,
)
from app.core.db import Base, CommonMixin
from app.schemas import UserRole
from app.schemas.types import (
    validate_email,
    validate_password,
    validate_phone,
    validate_tg_id,
    validate_username,
)
from app.validators.orm_models_validator import create_validator_mixin

UserValidatorMixin = create_validator_mixin({
    'username': validate_username,
    'email': validate_email,
    'password': validate_password,
    'phone': validate_phone,
    'tg_id': validate_tg_id,
})


class User(UserValidatorMixin, CommonMixin, Base):
    """Модель пользователя."""

    username: Mapped[str] = mapped_column(
        String(USER_NAME_MAX_LENGTH),
        unique=True,
        nullable=False,
    )
    password: Mapped[str] = mapped_column(
        String(USER_PASSWORD_MAX_LENGTH),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(USER_EMAIL_MAX_LENGTH),
        unique=True,
        nullable=False,
        index=True,
    )
    phone: Mapped[str] = mapped_column(
        String(USER_PHONE_MAX_LENGTH),
        nullable=True,
        unique=True,
        index=True,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.USER.value,
        nullable=False,
    )
    tg_id: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    cafes = relationship(
        'Cafe',
        secondary='cafe_manager',
        back_populates='managers',
    )

    @property
    def is_administrator(self) -> bool:
        """Проверка является ли пользователь администратором."""
        return self.role == UserRole.ADMINISTRATOR.value

    @property
    def is_manager(self) -> bool:
        """Проверка является ли пользователь менеджером."""
        return self.role == UserRole.MANAGER.value
