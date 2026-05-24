"""Утилиты для работы с базой данных в Celery задачах."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.sync_database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    engine,
    expire_on_commit=False,
)


@contextmanager
def get_session() -> Generator:
    """Контекстный менеджер для сессии.

    Автоматически коммитит или откатывает.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
