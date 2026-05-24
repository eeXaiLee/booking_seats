"""зависимости для FastAPI."""

from typing import Annotated, Callable

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
)
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.models.user import User
from app.schemas.user import UserRole
from app.services.auth import AuthService
from app.services.booking import BookingService
from app.services.cafe import CafeService
from app.services.table import TableService
from containers import Container

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')

SessionDependency = Annotated[
    AsyncSession,
    Depends(Provide[Container.db_session]),
]

CRUDActionDependency = Annotated[
    CRUDAction,
    Depends(Provide[Container.action_crud]),
]


AuthServiceDependency = Annotated[
    AuthService,
    Depends(Provide[Container.auth_service]),
]

CRUDUserDependency = Annotated[
    CRUDUser,
    Depends(Provide[Container.user_crud]),
]

BookingServiceDependency = Annotated[
    BookingService,
    Depends(Provide[Container.booking_service]),
]

CRUDBookingDependency = Annotated[
    BookingCRUD,
    Depends(Provide[Container.booking_crud]),
]

CRUDCafeDependency = Annotated[
    CafeCRUD,
    Depends(Provide[Container.cafe_crud]),
]

CafeServiceDependency = Annotated[
    CafeService,
    Depends(Provide[Container.cafe_service]),
]

CRUDDishDependency = Annotated[
    CRUDDish,
    Depends(Provide[Container.dish_crud]),
]

CRUDTableDependency = Annotated[
    TableCRUD,
    Depends(Provide[Container.table_crud]),
]

TableServiceDependency = Annotated[
    TableService,
    Depends(Provide[Container.table_service]),
]

CRUDTimeSlotDependency = Annotated[
    TimeSlotCRUD,
    Depends(Provide[Container.time_slot_crud]),
]

TokenServiceDependency = Annotated[
    TokenService,
    Depends(Provide[Container.token_service]),
]


@inject
async def get_current_user(
    auth_service: AuthServiceDependency,
    session: SessionDependency,
    token: str = Depends(oauth2_scheme),
) -> User:
    """Возвращает текущего аутентифицированного пользователя."""
    return await auth_service.get_current_user(token, session)


def role_checker(*allowed_roles: UserRole) -> Callable[..., User]:
    """Создаёт зависимость для проверки доступа по ролям."""

    @inject
    async def checker(
        session: SessionDependency,
        auth_service: AuthServiceDependency,
        token: str = Depends(oauth2_scheme),
    ) -> User:
        user = await auth_service.get_current_user(token, session)
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='У вас нет прав для этого действия',
            )
        return user

    return checker


UserDependency = Annotated[
    User,
    Depends(get_current_user),
]

AdminOnlyDependency = Annotated[
    User,
    Depends(
        role_checker(UserRole.ADMINISTRATOR),
    ),
]

AdminAndManagerDependency = Annotated[
    User,
    Depends(role_checker(UserRole.ADMINISTRATOR, UserRole.MANAGER)),
]
