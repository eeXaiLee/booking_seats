"""Инициализация базы данных при старте приложения."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import INIT_DB, SYSTEM_USER_ID
from app.core.logging import contextualize_user, log_audit_event, logger
from app.crud.user import user_crud
from app.schemas.user import UserCreateByAdmin, UserRole


async def create_first_users(session: AsyncSession) -> None:
    """Создаёт первых пользователей при старте."""
    with contextualize_user(user_id=SYSTEM_USER_ID, username=INIT_DB):
        user_configs = [
            {
                "email": settings.first_superuser_email,
                "password": settings.first_superuser_password,
                "phone": settings.first_superuser_phonenumber,
                "role": UserRole.ADMINISTRATOR,
                "event_msg": "Создан суперпользователь при инициализации",
            },
            {
                "email": settings.first_manager_email,
                "password": settings.first_manager_password,
                "phone": settings.first_manager_phonenumber,
                "role": UserRole.MANAGER,
                "event_msg": "Создан менеджер при инициализации",
            },
            {
                "email": settings.first_user_email,
                "password": settings.first_user_password,
                "phone": settings.first_user_phonenumber,
                "role": UserRole.USER,
                "event_msg": "Создан обычный пользователь при инициализации",
            },
        ]

        for config in user_configs:
            email = config["email"].strip().lower()
            if not email:
                continue

            existing = await user_crud.get_by_attributes(session, email=email)
            if existing:
                logger.info(
                    "Пропущено создание пользователя — уже существует",
                    email=email,
                )
                continue

            user_in = UserCreateByAdmin(
                email=email,
                password=config["password"],
                role=config["role"],
                username=email.split("@")[0],
                phone=config["phone"],
                tg_id=None,
            )
            db_user = await user_crud.create_user(user_in, session)

            log_audit_event(
                event=config["event_msg"],
                details={
                    "email": db_user.email,
                    "username": db_user.username,
                    "role": str(db_user.role),
                },
            )
