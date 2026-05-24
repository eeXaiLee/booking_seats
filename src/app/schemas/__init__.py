"""Схемы данных для приложения."""

from app.schemas.action import (
    ActionCreate,
    ActionInfo,
    ActionUpdate,
)
from app.schemas.booking import (
    BookingCreate,
    BookingInfo,
    BookingStatus,
    BookingUpdate,
)
from app.schemas.cafe import (
    CafeCreate,
    CafeInfo,
    CafeShortInfo,
    CafeUpdate,
)
from app.schemas.dish import (
    DishCreate,
    DishInfo,
    DishUpdate,
)
from app.schemas.events import EventType, OutboxEventCreate
from app.schemas.table import (
    TableCreate,
    TableInfo,
    TableShortInfo,
    TableUpdate,
)
from app.schemas.time_slot import (
    TimeSlotCreate,
    TimeSlotInfo,
    TimeSlotShortInfo,
    TimeSlotUpdate,
)
from app.schemas.types import (
    Description,
    DishName,
    Name,
    Password,
    PhoneNumber,
    Price,
    TgId,
    Username,
)
from app.schemas.user import (
    Token,
    TokenData,
    UserBase,
    UserCreate,
    UserCreateByAdmin,
    UserInfo,
    UserRole,
    UserShortInfo,
    UserUpdateByAdmin,
    UserUpdateOwn,
)

__all__ = [
    'ActionCreate',
    'ActionInfo',
    'ActionUpdate',
    'BookingCreate',
    'BookingInfo',
    'BookingStatus',
    'BookingUpdate',
    'CafeCreate',
    'CafeInfo',
    'CafeShortInfo',
    'CafeUpdate',
    'DishCreate',
    'DishInfo',
    'DishUpdate',
    'EventType',
    'OutboxEventCreate',
    'TableCreate',
    'TableInfo',
    'TableShortInfo',
    'TableUpdate',
    'TimeSlotCreate',
    'TimeSlotInfo',
    'TimeSlotShortInfo',
    'TimeSlotUpdate',
    'Token',
    'TokenData',
    'UserBase',
    'UserCreate',
    'UserInfo',
    'UserRole',
    'UserShortInfo',
    'UserUpdateOwn',
    'UserCreateByAdmin',
    'UserUpdateByAdmin',
    'Description',
    'DishName',
    'Password',
    'PhoneNumber',
    'Price',
    'TgId',
    'Username',
    'Name',
]
