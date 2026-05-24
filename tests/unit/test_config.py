"""Тесты конфигурации приложения."""

from app.core.config import Settings


def test_database_urls_are_derived_from_postgres_settings() -> None:
    """Async и sync DSN должны собираться из одного набора POSTGRES_* полей."""
    settings = Settings.model_construct(
        app_title='Booking',
        app_description='Booking app',
        secret='secret',
        log_level='INFO',
        log_file='logs/app.log',
        log_rotation='10 MB',
        log_retention='10 files',
        secret_key='secret-key',
        refresh_secret_key='refresh-secret-key',
        algorithm='HS256',
        refresh_token_expire_days=7,
        access_token_expire_minutes=15,
        default_page_limit=50,
        max_page_limit=1000,
        media_dir='media',
        max_image_size=5242880,
        allowed_image_types=['image/jpeg'],
        allowed_extentions=['.jpg'],
        jpeg_quality=85,
        rabbitmq_host='localhost',
        rabbitmq_port=5672,
        rabbitmq_user='guest',
        rabbitmq_pass='guest',
        rabbitmq_vhost='/',
        rabbitmq_heartbeat=600,
        rabbitmq_connection_attempts=5,
        rabbitmq_delivery_mode=2,
        backend_result='rpc://',
        smtp_host='smtp4dev',
        smtp_port=25,
        smtp_user='',
        smtp_password='',
        smtp_from_email='booking@example.com',
        smtp_use_tls=False,
        smtp_use_ssl=False,
        postgres_user='db_user',
        postgres_password='db_password',
        postgres_db='booking_db',
        postgres_host='db',
        postgres_port=5432,
        first_superuser_email='admin@example.com',
        first_superuser_password='Admin1234!',
        first_superuser_phonenumber='+79000000001',
        first_manager_email='manager@example.com',
        first_manager_password='Manager1234!',
        first_manager_phonenumber='+79000000002',
        first_user_email='user@example.com',
        first_user_password='User1234!',
        first_user_phonenumber='+79000000003',
    )

    assert settings.database_url == (
        'postgresql+asyncpg://db_user:db_password@db:5432/booking_db'
    )
    assert settings.sync_database_url == (
        'postgresql://db_user:db_password@db:5432/booking_db'
    )
