"""Конфигурация Celery."""

from celery.schedules import crontab
from kombu import Exchange, Queue

from app.core.config import settings

default_exchange = Exchange('default', type='direct')
email_exchange = Exchange('email', type='direct')
high_priority_exchange = Exchange('high', type='direct')
broadcast_exchange = Exchange('broadcast', type='fanout')


class CeleryConfig:
    """Конфигурация Celery."""

    broker_url = settings.resolved_broker_url
    result_backend = settings.backend_result
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    timezone = 'Europe/Moscow'
    enable_utc = True
    worker_send_task_events = True
    task_send_sent_event = True

    task_time_limit = 30 * 60
    task_soft_time_limit = 25 * 60

    task_queues = (
        Queue('default', default_exchange, routing_key='default'),
        Queue(
            'high_priority',
            high_priority_exchange,
            routing_key='high_priority',
        ),
        Queue('email', email_exchange, routing_key='email'),
        Queue('broadcast', broadcast_exchange),
    )
    task_default_queue = 'default'
    task_default_exchange = 'default'
    task_default_routing_key = 'default'

    beat_schedule = {
        'check-bookings-every-day': {
            'task': 'booking_reminder',
            'schedule': crontab(hour=1, minute=0),
        },
        'publish-outbox-every-minute': {
            'task': 'publish_pending_outbox_events',
            'schedule': 60.0,
        },
        'consume-domain-events-every-20-seconds': {
            'task': 'consume_domain_events',
            'schedule': 20.0,
        },
        'check-pipeline-health-every-5-minutes': {
            'task': 'check_pipeline_health',
            'schedule': 300.0,
        },
    }
