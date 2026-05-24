from typing import Any

from sqlalchemy.orm import validates
from typing_extensions import Self


def create_validator_mixin(field_validators: dict) -> type:
    """Создание фабрики миксинов для валидации полей.

    Args:
        field_validators: Словарь {поле: валидатор}.

    Returns:
        Класс-миксин с валидацией указанных полей.

    """

    @validates(*field_validators.keys())
    def validate_field(self: Self, key: str, value: Any) -> Any:
        """Валидация поля по ключу."""
        validator = field_validators.get(key)
        if validator and value is not None:
            return validator(value)
        return value

    attrs = {
        '_FIELD_VALIDATORS': field_validators,
        'validate_field': validate_field,
    }

    return type('ValidatorMixin', (), attrs)
