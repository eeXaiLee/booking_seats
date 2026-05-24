"""Настройка DI-контейнера для приложения."""

from dependency_injector import containers, providers

from app.core.config import settings
from app.core.db import AsyncSessionLocal, get_async_session
from app.core.jwt_security import TokenService
from app.crud import (
    BookingCRUD,
    CRUDAction,
    CRUDDish,
    CRUDUser,
    CafeCRUD,
    TableCRUD,
    TimeSlotCRUD,
)
from app.models import Action, Dish, TimeSlot, User
from app.services.auth import AuthService
from app.services.booking import BookingService
from app.services.cafe import CafeService
from app.services.table import TableService


class Container(containers.DeclarativeContainer):
    """DI-контейнер."""

    config = providers.Configuration()

    db_session_factory = providers.Factory(
        AsyncSessionLocal,
    )

    db_session = providers.Resource(
        get_async_session,
    )

    cafe_crud = providers.Singleton(
        CafeCRUD,
    )

    cafe_service = providers.Singleton(
        CafeService,
    )

    table_crud = providers.Singleton(
        TableCRUD,
    )

    table_service = providers.Singleton(
        TableService,
    )

    booking_crud = providers.Singleton(
        BookingCRUD,
    )

    booking_service = providers.Singleton(
        BookingService,
        booking_crud=booking_crud,
    )

    user_crud = providers.Singleton(
        CRUDUser,
        model=User,
    )

    action_crud = providers.Singleton(
        CRUDAction,
        model=Action,
    )

    dish_crud = providers.Singleton(
        CRUDDish,
        model=Dish,
    )

    time_slot_crud = providers.Singleton(
        TimeSlotCRUD,
        model=TimeSlot,
    )

    token_service = providers.Singleton(
        TokenService,
        secret_key=settings.secret_key,
        refresh_secret_key=settings.refresh_secret_key,
        algorithm=settings.algorithm,
        access_exp_minutes=settings.access_token_expire_minutes,
        refresh_exp_days=settings.refresh_token_expire_days,
    )

    auth_service = providers.Singleton(
        AuthService,
        user_crud=user_crud,
        token_service=token_service,
    )
