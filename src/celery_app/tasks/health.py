"""Периодический мониторинг работоспособности pipeline обработки событий."""

from datetime import datetime, timedelta, timezone

from celery import Task
from loguru import logger
from sqlalchemy import func, select

from app.core.constants import (
    HEALTH_FAILED_WARN_COUNT,
    HEALTH_PENDING_STALE_MINUTES,
    HEALTH_PENDING_WARN_COUNT,
    OUTBOX_STATUS_FAILED,
    OUTBOX_STATUS_PENDING,
)
from app.models.outbox_event import OutboxEvent
from app.models.processed_event import ProcessedEvent
from celery_app.utils.celery_db import get_session
from celery_app.worker import celery_app

# Пороги для предупреждений берутся из централизованных констант
PENDING_EVENTS_STALE_MINUTES = HEALTH_PENDING_STALE_MINUTES
PENDING_EVENTS_WARN_COUNT = HEALTH_PENDING_WARN_COUNT
FAILED_EVENTS_WARN_COUNT = HEALTH_FAILED_WARN_COUNT


@celery_app.task(
    name='check_pipeline_health',
    queue='default',
    bind=True,
    max_retries=0,
)
def check_pipeline_health(self: Task) -> dict:
    """Проверить накопленные метрики pipeline и залогировать предупреждения.

    Проверяет:
    - количество `pending` событий старше порога (зависание publisher)
    - общее количество `failed` событий
    - кол-во обработанных событий за 5 мин (активность consumer)

    При превышении порогов логирует WARNING/ERROR, что позволяет команде
    замечать деградацию без внешней системы мониторинга.
    """
    now = datetime.now(timezone.utc)
    stale_cutoff = now - timedelta(minutes=PENDING_EVENTS_STALE_MINUTES)
    recent_cutoff = now - timedelta(minutes=5)

    with get_session() as session:
        # Количество pending событий, зависших дольше порога
        stale_pending_count = (
            session.execute(
                select(func.count())
                .select_from(OutboxEvent)
                .where(
                    OutboxEvent.status == OUTBOX_STATUS_PENDING,
                    OutboxEvent.created_at < stale_cutoff,
                ),
            ).scalar()
            or 0
        )

        # Общее количество pending событий
        total_pending_count = (
            session.execute(
                select(func.count())
                .select_from(OutboxEvent)
                .where(
                    OutboxEvent.status == OUTBOX_STATUS_PENDING,
                ),
            ).scalar()
            or 0
        )

        # Количество failed событий
        failed_count = (
            session.execute(
                select(func.count())
                .select_from(OutboxEvent)
                .where(
                    OutboxEvent.status == OUTBOX_STATUS_FAILED,
                ),
            ).scalar()
            or 0
        )

        # Количество обработанных событий за последние 5 минут
        recent_processed_count = (
            session.execute(
                select(func.count())
                .select_from(ProcessedEvent)
                .where(
                    ProcessedEvent.processed_at >= recent_cutoff,
                ),
            ).scalar()
            or 0
        )

    metrics = {
        'stale_pending_count': stale_pending_count,
        'total_pending_count': total_pending_count,
        'failed_count': failed_count,
        'recent_processed_count': recent_processed_count,
        'checked_at': now.isoformat(),
    }

    # Логирование по порогам
    if failed_count >= FAILED_EVENTS_WARN_COUNT:
        logger.error(
            'health.alert pipeline_failed_events '
            'failed_count={failed_count} threshold={threshold}',
            failed_count=failed_count,
            threshold=FAILED_EVENTS_WARN_COUNT,
        )

    if stale_pending_count >= PENDING_EVENTS_WARN_COUNT:
        logger.warning(
            'health.alert stale_pending_events '
            'stale_count={stale_count} threshold={threshold} '
            'stale_minutes={stale_minutes}',
            stale_count=stale_pending_count,
            threshold=PENDING_EVENTS_WARN_COUNT,
            stale_minutes=PENDING_EVENTS_STALE_MINUTES,
        )
    elif stale_pending_count > 0:
        logger.warning(
            'health.warn stale_pending_events stale_count={stale_count} '
            'stale_minutes={stale_minutes}',
            stale_count=stale_pending_count,
            stale_minutes=PENDING_EVENTS_STALE_MINUTES,
        )

    logger.info(
        'health.check ok total_pending={total_pending} '
        'failed={failed} recent_processed={recent_processed}',
        total_pending=total_pending_count,
        failed=failed_count,
        recent_processed=recent_processed_count,
    )

    return {'status': 'ok', 'metrics': metrics}
