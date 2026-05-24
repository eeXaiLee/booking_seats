"""Модель акции и её связь с кафе."""

from __future__ import annotations

from typing import List

from sqlalchemy import UUID, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonMixin
from app.schemas.types import validate_description
from app.validators.orm_models_validator import create_validator_mixin

from .cafe import Cafe

ActionValidatorMixin = create_validator_mixin({
    'description': validate_description,
})


class Action(CommonMixin, ActionValidatorMixin, Base):
    """Модель акции."""

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    photo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    cafes: Mapped[List[Cafe]] = relationship(
        Cafe,
        secondary='cafe_action',
        back_populates='actions',
        lazy='selectin',
    )
