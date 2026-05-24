"""Основной роутер, включающий все маршруты приложения."""

from fastapi import APIRouter

from app.api.endpoints import (
    action_router,
    auth_router,
    booking_router,
    cafe_router,
    dish_router,
    media_router,
    table_router,
    time_slot_router,
    user_router,
)

main_router = APIRouter()

main_router.include_router(
    auth_router,
    prefix='/auth',
    tags=['Аутентификация'],
)
main_router.include_router(
    user_router,
    prefix='/users',
    tags=['Пользователи'],
)
main_router.include_router(
    cafe_router,
    prefix='/cafes',
    tags=['Кафе'],
)
main_router.include_router(
    table_router,
    prefix='/cafe/{cafe_id}/tables',
    tags=['Столы'],
)
main_router.include_router(
    action_router,
    prefix='/actions',
    tags=['Акции'],
)
main_router.include_router(
    dish_router,
    prefix='/dishes',
    tags=['Блюда'],
)
main_router.include_router(
    time_slot_router,
    prefix='/cafe/{cafe_id}/time_slots',
    tags=['Временные слоты'],
)
main_router.include_router(
    media_router,
    prefix='/media',
    tags=['Медиа'],
)
main_router.include_router(
    booking_router,
    prefix='/booking',
    tags=['Бронирования'],
)
