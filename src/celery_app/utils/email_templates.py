"""Утилиты для генерации шаблонов email-уведомлений."""

from typing import Dict

from app.models.booking import Booking
from app.models.user import User


class EmailTemplates:
    """Шаблоны email-уведомлений."""

    @staticmethod
    def user_booking_confirmation(
        booking: Booking,
        user: User,
    ) -> Dict[str, str]:
        """Шаблон письма для пользователя."""
        subject = f'Бронирование #{booking.id} подтверждено'
        body = f"""Здравствуйте, {user.username}!

Ваше бронирование подтверждено.

Детали бронирования:
━━━━━━━━━━━━━━━━━━━━━━
• Кафе: {booking.cafe.name}
• Адрес: {booking.cafe.address if booking.cafe.address else 'Не указан'}
• Дата: {booking.booking_date.strftime('%d.%m.%Y %H:%M')}
• Количество гостей: {booking.guest_number}
━━━━━━━━━━━━━━━━━━━━━━

Спасибо за выбор нашего сервиса!

С уважением,
Команда Booking
"""
        return {'subject': subject, 'body': body}

    @staticmethod
    def admin_new_booking_notification(
        booking: Booking,
        user: User,
    ) -> Dict[str, str]:
        """Шаблон письма для администратора."""
        subject = f'Новая бронь #{booking.id}'
        body = f"""Здравствуйте!

Поступила новая бронь.

Детали бронирования:
━━━━━━━━━━━━━━━━━━━━━━
• Пользователь: {user.username} ({user.email})
• Кафе: {booking.cafe.name}
• Дата: {booking.booking_date.strftime('%d.%m.%Y %H:%M')}
• Количество гостей: {booking.guest_number}
━━━━━━━━━━━━━━━━━━━━━━

Пожалуйста, обработайте бронирование.

С уважением,
Booking System
"""
        return {'subject': subject, 'body': body}

        return {'subject': subject, 'body': body}
