"""Роутеры API для эндпоинтов приложения."""

from app.api.endpoints.action import router as action_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.booking import router as booking_router
from app.api.endpoints.cafe import router as cafe_router
from app.api.endpoints.dish import router as dish_router
from app.api.endpoints.media import router as media_router
from app.api.endpoints.table import router as table_router
from app.api.endpoints.time_slot import router as time_slot_router
from app.api.endpoints.user import router as user_router

__all__ = [
    'action_router',
    'booking_router',
    'cafe_router',
    'dish_router',
    'table_router',
    'time_slot_router',
    'auth_router',
    'user_router',
    'media_router',
]
