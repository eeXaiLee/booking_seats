"""Задачи Celery: email-уведомления и напоминания о бронированиях."""

import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from celery import Task
from kombu.exceptions import KombuError
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.booking import Booking
from app.models.user import User
from app.schemas.booking import BookingStatus
from app.schemas.user import UserRole
from celery_app.utils.celery_db import get_session
from celery_app.utils.email_templates import EmailTemplates
from celery_app.worker import celery_app


@celery_app.task(
    name='send_email_booking_notification',
    queue='email',
    bind=True,
    max_retries=3,
)
def send_email_booking_notification(
    self: Task,
    booking_id: int,
    correlation_id: str = '-',
) -> dict:
    """Отправить email-уведомление о бронировании."""
    logger.info(
        'email.notification start bid={booking_id} req={request_id}',
        booking_id=booking_id,
        request_id=correlation_id,
    )
    with get_session() as session:
        stmt = (
            select(Booking)
            .where(Booking.id == booking_id)
            .options(selectinload(Booking.user), selectinload(Booking.cafe))
        )
        result = session.execute(stmt)
        booking = result.unique().scalar_one_or_none()

        if booking is None:
            return {
                'message': f'Бронирование с ID {booking_id} не найдено',
                'status': 'not_found',
            }

        if not booking.user:
            return {
                'message': f'У бронирования {booking_id} нет пользователя',
                'status': 'skipped',
            }

        if booking.status == BookingStatus.CANCELED:
            return {
                'message': f'Бронирование {booking_id} отменено',
                'status': 'skipped',
            }

        if not booking.user.email:
            return {
                'message': 'У пользователя нет email',
                'status': 'skipped',
            }

        if not booking.user.is_active:
            return {'message': 'Пользователь неактивен', 'status': 'skipped'}

        admin_stmt = select(User).where(
            User.role == UserRole.ADMINISTRATOR,
        )
        administrators = session.execute(admin_stmt).scalars().all()

        if not administrators:
            return {'message': 'Администратор не найден', 'status': 'skipped'}

        try:
            user_email_template = EmailTemplates.user_booking_confirmation(
                booking,
                booking.user,
            )
            send_email_smtp.delay(
                subject=user_email_template['subject'],
                body=user_email_template['body'],
                to=booking.user.email,
                correlation_id=correlation_id,
            )

            admin_email_template = (
                EmailTemplates.admin_new_booking_notification(
                    booking,
                    booking.user,
                )
            )
            for admin in administrators:
                if not admin.email:
                    continue
                send_email_smtp.delay(
                    subject=admin_email_template['subject'],
                    body=admin_email_template['body'],
                    to=admin.email,
                    correlation_id=correlation_id,
                )

            logger.info(
                'email.notification ok bid={booking_id} req={request_id}',
                booking_id=booking_id,
                request_id=correlation_id,
            )
            return {
                'message': f'Уведомление по брони {booking_id} отправлено',
                'status': 'success',
            }
        except (KombuError, OSError) as e:
            raise self.retry(exc=e, countdown=300)


@celery_app.task(
    name='send_email_smtp',
    queue='email',
    bind=True,
    max_retries=3,
)
def send_email_smtp(
    self: Task,
    subject: str,
    body: str,
    to: str,
    correlation_id: str = '-',
) -> None:
    """Отправить email через SMTP."""
    msg = MIMEMultipart()
    msg['From'] = settings.smtp_from_email
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        if settings.smtp_use_ssl:
            server = smtplib.SMTP_SSL(
                settings.smtp_host,
                settings.smtp_port,
            )
        else:
            server = smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
            )

        if settings.smtp_use_tls:
            server.starttls()

        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)

        server.sendmail(settings.smtp_from_email, to, msg.as_string())
        server.quit()
        logger.info(
            'email.smtp sent to={to} req={request_id}',
            to=to,
            request_id=correlation_id,
        )
    except (smtplib.SMTPException, OSError) as e:
        raise self.retry(exc=e, countdown=300)


@celery_app.task(
    name='booking_reminder',
    queue='email',
    max_retries=3,
)
def booking_reminder() -> dict:
    """Отправить напоминания о бронированиях на завтра."""
    with get_session() as session:
        tomorrow = datetime.now().date() + timedelta(days=1)
        stmt = (
            select(Booking)
            .where(
                Booking.status == BookingStatus.BOOKING,
                Booking.booking_date == tomorrow,
            )
            .options(selectinload(Booking.user), selectinload(Booking.cafe))
        )
        bookings = session.execute(stmt).scalars().all()

        if not bookings:
            return {
                'message': f'На {tomorrow} нет бронирований',
                'status': 'no_bookings',
            }

        for booking in bookings:
            send_email_booking_notification.delay(
                booking.id,
                correlation_id='scheduler',
            )

        return {
            'message': f'Задач поставлено в очередь: {len(bookings)}',
            'status': 'completed',
            'queued': len(bookings),
        }
