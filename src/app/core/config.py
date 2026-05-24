"""Модуль с конфигурацией приложения."""

from pathlib import Path
from typing import List
from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import ENCODING

BASE_DIR = Path(__file__).resolve().parents[3]

ENV_FILE = BASE_DIR / 'infra' / '.env'


class Settings(BaseSettings):
    """Настройки приложения."""

    # Base Set
    app_title: str
    app_description: str
    server_ip: str | None = None
    secret: str
    log_level: str
    log_file: str
    log_rotation: str
    log_retention: str

    # Token Set
    secret_key: str
    refresh_secret_key: str
    algorithm: str
    refresh_token_expire_days: int
    access_token_expire_minutes: int
    default_page_limit: int
    max_page_limit: int

    # Media Set
    media_dir: str
    max_image_size: int
    allowed_image_types: List[str]
    allowed_extentions: List[str]
    jpeg_quality: int

    # RabbitMQ Set
    rabbitmq_host: str
    rabbitmq_port: int
    rabbitmq_user: str
    rabbitmq_pass: str
    rabbitmq_vhost: str
    rabbitmq_heartbeat: int
    rabbitmq_connection_attempts: int
    rabbitmq_delivery_mode: int

    # Celery Set
    backend_result: str

    # SMTP Set
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from_email: str
    smtp_use_tls: bool
    smtp_use_ssl: bool

    # Postgres Set
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

    # Init DB
    first_superuser_email: str
    first_superuser_password: str
    first_superuser_phonenumber: str
    first_manager_email: str
    first_manager_password: str
    first_manager_phonenumber: str
    first_user_email: str
    first_user_password: str
    first_user_phonenumber: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE if ENV_FILE.exists() else None,  # ←  из os.environ
        env_file_encoding=ENCODING,
        extra='ignore',
    )

    @property
    def database_url(self) -> str:
        """Автоматическая генерация URL подключения к БД."""
        return (
            f'postgresql+asyncpg://'
            f'{self.postgres_user}:{self.postgres_password}@'
            f'{self.postgres_host}:{self.postgres_port}/'
            f'{self.postgres_db}'
        )

    @property
    def sync_database_url(self) -> str:
        """Автоматическая генерация sync URL подключения к БД."""
        return (
            f'postgresql://'
            f'{self.postgres_user}:{self.postgres_password}@'
            f'{self.postgres_host}:{self.postgres_port}/'
            f'{self.postgres_db}'
        )

    @property
    def resolved_broker_url(self) -> str:
        """Собрать URL брокера из RabbitMQ-переменных окружения."""
        encoded_user = quote(self.rabbitmq_user, safe='')
        encoded_password = quote(self.rabbitmq_pass, safe='')
        encoded_vhost = quote(self.rabbitmq_vhost, safe='')

        if self.rabbitmq_vhost == '/':
            encoded_vhost = '%2F'

        return (
            f'amqp://{encoded_user}:{encoded_password}@'
            f'{self.rabbitmq_host}:{self.rabbitmq_port}/{encoded_vhost}'
        )


settings = Settings()  # type: ignore
