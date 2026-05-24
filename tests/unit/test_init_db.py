"""Тесты инициализации пользователей."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core import init_db


@pytest.mark.asyncio
async def test_create_first_users_normalizes_email_before_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Проверка: поиск существующего пользователя идёт по lower-case email."""
    session = AsyncMock()
    get_by_attributes = AsyncMock(return_value=object())
    create_user = AsyncMock()
    info_mock = MagicMock()

    monkeypatch.setattr(
        init_db,
        'settings',
        SimpleNamespace(
            first_superuser_email='Admin@Example.com',
            first_superuser_password='Secret123',
            first_superuser_phonenumber='+79000000001',
            first_manager_email='',
            first_manager_password='Secret123',
            first_manager_phonenumber='+79000000002',
            first_user_email='',
            first_user_password='Secret123',
            first_user_phonenumber='+79000000003',
        ),
    )
    monkeypatch.setattr(
        init_db,
        'user_crud',
        SimpleNamespace(
            get_by_attributes=get_by_attributes,
            create_user=create_user,
        ),
    )
    monkeypatch.setattr(init_db.logger, 'info', info_mock)

    await init_db.create_first_users(session)

    get_by_attributes.assert_awaited_once_with(
        session,
        email='admin@example.com',
    )
    create_user.assert_not_awaited()
