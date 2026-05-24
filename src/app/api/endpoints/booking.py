"""Модуль с эндпоинтами для работы с бронированиями."""

from http import HTTPStatus

from dependency_injector.wiring import inject
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    BookingServiceDependency,
    CRUDBookingDependency,
    SessionDependency,
    UserDependency,
)
from app.crud import BookingCRUD
from app.models import Booking, User
from app.schemas import BookingCreate, BookingInfo, BookingUpdate

router = APIRouter()


async def get_booking_or_404(
    booking_id: int,
    session: AsyncSession,
    booking_crud: BookingCRUD,
) -> Booking:
    """Получить бронирование или вернуть 404."""
    booking = await booking_crud.get(
        obj_id=booking_id,
        session=session,
    )
    if booking is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Бронирование не найдено.',
        )
    return booking


def check_booking_access(
    booking: Booking,
    user: User,
) -> None:
    """Проверить доступ пользователя к бронированию."""
    if user.is_administrator or user.is_manager:
        return
    if booking.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='Недостаточно прав для доступа к бронированию.',
        )


@router.get(
    '/',
    response_model=list[BookingInfo],
    response_model_exclude_none=True,
    summary='Получить список бронирований',
    description='Получить список бронирований.',
)
@inject
async def get_bookings(
    session: SessionDependency,
    booking_crud: CRUDBookingDependency,
    current_user: UserDependency,
    show_all: bool = False,
    cafe_id: int | None = None,
    user_id: int | None = None,
) -> list[Booking]:
    """Получение списка бронирований с учетом роли пользователя."""
    if current_user.is_administrator or current_user.is_manager:
        return await booking_crud.get_multi(
            session=session,
            show_all=show_all,
            cafe_id=cafe_id,
            user_id=user_id,
        )
    return await booking_crud.get_multi(
        session=session,
        show_all=False,
        cafe_id=cafe_id,
        user_id=current_user.id,
    )


@router.post(
    '/',
    response_model=BookingInfo,
    response_model_exclude_none=True,
    status_code=HTTPStatus.CREATED,
    summary='Создать бронирование',
    description='Создать бронирование.',
)
@inject
async def create_booking(
    booking_in: BookingCreate,
    session: SessionDependency,
    booking_service: BookingServiceDependency,
    current_user: UserDependency,
    request: Request,
) -> Booking:
    """Создание бронирования текущим пользователем."""
    try:
        return await booking_service.create_booking(
            obj_in=booking_in,
            user_id=current_user.id,
            session=session,
            correlation_id=getattr(request.state, 'correlation_id', None),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get(
    '/{booking_id}',
    response_model=BookingInfo,
    response_model_exclude_none=True,
    summary='Получить бронирование по id',
    description='Получить бронирование по id.',
)
@inject
async def get_booking(
    booking_id: int,
    session: SessionDependency,
    booking_crud: CRUDBookingDependency,
    current_user: UserDependency,
) -> Booking:
    """Получение одного бронирования с проверкой доступа."""
    booking = await get_booking_or_404(
        booking_id=booking_id,
        session=session,
        booking_crud=booking_crud,
    )
    check_booking_access(
        booking=booking,
        user=current_user,
    )
    return booking


@router.patch(
    '/{booking_id}',
    response_model=BookingInfo,
    response_model_exclude_none=True,
    summary='Обновить бронирование',
    description='Обновить бронирование.',
)
@inject
async def update_booking(
    booking_id: int,
    booking_in: BookingUpdate,
    session: SessionDependency,
    booking_crud: CRUDBookingDependency,
    booking_service: BookingServiceDependency,
    current_user: UserDependency,
    request: Request,
) -> Booking:
    """Обновление бронирования с проверкой доступа."""
    booking = await get_booking_or_404(
        booking_id=booking_id,
        session=session,
        booking_crud=booking_crud,
    )
    check_booking_access(
        booking=booking,
        user=current_user,
    )
    try:
        return await booking_service.update_booking(
            booking=booking,
            obj_in=booking_in,
            session=session,
            correlation_id=getattr(request.state, 'correlation_id', None),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=str(error),
        ) from error
