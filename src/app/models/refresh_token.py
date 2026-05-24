"""Модель refresh токена."""

import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import TOKEN_HASH_MAX_LENGTH
from app.core.db import Base


class RefreshToken(Base):
    """Модель refresh токена для хранения в БД."""

    __tablename__ = 'refresh_tokens'

    id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[uuid.UUID] = mapped_column(
        UUID,
        unique=True,
        index=True,
        default=uuid.uuid4,
    )
    token_hash: Mapped[str] = mapped_column(
        String(TOKEN_HASH_MAX_LENGTH),
        unique=True,
        index=True,
        nullable=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('user.id'),
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default='false',
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text('CURRENT_TIMESTAMP'),
    )
