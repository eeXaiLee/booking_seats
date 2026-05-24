"""Модуль с CRUD-операциями для всех моделей приложения."""

from app.crud.action import CRUDAction
from app.crud.booking import BookingCRUD
from app.crud.cafe import CafeCRUD
from app.crud.dish import CRUDDish
from app.crud.table import TableCRUD
from app.crud.time_slot import TimeSlotCRUD, time_slot_crud
from app.crud.user import CRUDUser, user_crud

from .base import CRUDBase

__all__ = [
    'BookingCRUD',
    'CafeCRUD',
    'CRUDAction',
    'CRUDBase',
    'CRUDDish',
    'CRUDUser',
    'TableCRUD',
    'TimeSlotCRUD',
    'CRUDBase',
    'CRUDUser',
    'time_slot_crud',
    'user_crud',
]
