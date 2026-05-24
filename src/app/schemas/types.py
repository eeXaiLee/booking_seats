"""Простые типы данных с валидацией для повторного использования в схемах."""

import re
from typing import Annotated

from pydantic import AfterValidator, Field

from app.core.constants import (
    DESCRIPTION_PATTERN,
    DISH_NAME_PATTERN,
    EMAIL_PATTERN,
    PHONE_PATTERN,
    PRICE_PATTERN,
    TABLE_MAX_SEAT_NUMBER,
    TABLE_MIN_SEAT_NUMBER,
    TG_ID_PATTERN,
    USERNAME_PATTERN,
)

PASSWORD_PATTERN = re.compile(
    r'^'
    r'(?=.*[A-Z])'
    r'(?=.*[a-z])'
    r'(?=.*\d)'
    r'\S{6,}$',
)

NAME_PATTERN = re.compile(
    r'^'
    r'(?:[а-яА-ЯёЁ]+(?:[ -][а-яА-ЯёЁ]+)*'
    r'|'
    r'[A-Za-z]+(?:[ -][A-Za-z]+)*)'
    r'$',
)


def validate_phone(phone: str) -> str:
    """Валидация номера телефона с нормализацией."""
    if not re.fullmatch(PHONE_PATTERN, phone):
        raise ValueError('Неверный формат номера телефона.')
    return '+7' + phone[1:] if phone.startswith('8') else phone


def validate_password(password: str) -> str:
    """Валидация пароля."""
    if len(password) < 6 or ' ' in password:
        raise ValueError(
            'Пароль должен содержать минимум 6 символов без пробелов.',
        )

    if not PASSWORD_PATTERN.fullmatch(password):
        raise ValueError(
            'Пароль должен содержать минимум  одну заглавную букву, '
            'одну строчную букву и одну цифру',
        )
    return password


def validate_email(email: str) -> str:
    """Валидация email."""
    if not re.fullmatch(EMAIL_PATTERN, email):
        raise ValueError('Неверный формат email.')
    return email.lower()


def validate_name(name: str) -> str:
    """Валидация имени."""
    if not (1 <= len(name) <= 255):
        raise ValueError('Длина имени должна быть от 1 до 255 символов.')
    if not NAME_PATTERN.fullmatch(name):
        raise ValueError('Неверный формат имени.')
    return name


def validate_username(username: str) -> str:
    """Валидация username."""
    if not (1 <= len(username) <= 255):
        raise ValueError('Длина username должна быть от 1 до 255 символов.')
    if not re.fullmatch(USERNAME_PATTERN, username):
        raise ValueError('Неверный формат username.')
    return username


def validate_dish_name(name: str) -> str:
    """Валидация названия блюда."""
    if not re.fullmatch(DISH_NAME_PATTERN, name):
        raise ValueError(
            'Название блюда должно содержать от 3 до 255 симфволов. '
            'Допустимы буквы, цифры, пробелы и знаки: -.,!?()/%',
        )
    return name.strip()


def validate_description(description: str) -> str:
    """Валидация описания."""
    if not re.fullmatch(DESCRIPTION_PATTERN, description):
        raise ValueError('Описание должно содержать от 1 до 500 символов.')
    return description.strip()


def validate_price(price: float) -> float:
    """Валидация цены."""
    price_str = f'{price:.2f}'
    if not re.fullmatch(PRICE_PATTERN, price_str):
        raise ValueError(
            'Цена должна быть положительным числом до 999999.99.',
        )
    if not (0.01 <= price <= 999999.99):
        raise ValueError('Цена должна быть в диапазоне от 0.01 до 999999.99')
    return round(price, 2)


def validate_tg_id(tg_id: str) -> str:
    """Валидация tg_id."""
    if not re.fullmatch(TG_ID_PATTERN, tg_id):
        raise ValueError('Неверный формат tg_id.')
    return tg_id


def validate_seat_number(seat_number: int) -> int:
    """Валидация количества мест за столом."""
    if not (
        TABLE_MIN_SEAT_NUMBER
        <= seat_number
        <= TABLE_MAX_SEAT_NUMBER
    ):
        raise ValueError(
            'Количество мест за столом должно быть '
            f'от {TABLE_MIN_SEAT_NUMBER} до {TABLE_MAX_SEAT_NUMBER}.',
        )
    return seat_number


# Простые типы — Field с pattern
PhoneNumber = Annotated[str, AfterValidator(validate_phone)]
Username = Annotated[str, Field(pattern=USERNAME_PATTERN)]
Password = Annotated[str, AfterValidator(validate_password)]
TgId = Annotated[str, Field(pattern=TG_ID_PATTERN)]
Name = Annotated[
    str,
    Field(pattern=NAME_PATTERN.pattern, min_length=1, max_length=255),
]
Description = Annotated[str, Field(pattern=DESCRIPTION_PATTERN)]
DishName = Annotated[str, AfterValidator(validate_dish_name)]
Price = Annotated[float, AfterValidator(validate_price)]
Email = Annotated[str, AfterValidator(validate_email)]
SeatNumber = Annotated[int, AfterValidator(validate_seat_number)]
