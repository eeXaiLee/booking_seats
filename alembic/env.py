# pylint: disable=no-member

import os
import sys
from importlib import import_module
from logging.config import fileConfig
from typing import Any, cast

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context as alembic_context


def _load_app_modules() -> tuple[Any, Any]:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    config_module = import_module('app.core.config')
    db_module = import_module('app.core.db')

    return config_module.settings, db_module.Base


app_settings, model_base = _load_app_modules()


def _build_sync_database_url(database_url: str) -> str:
    if database_url.startswith('postgresql+asyncpg://'):
        return database_url.replace(
            'postgresql+asyncpg://',
            'postgresql+psycopg2://',
            1,
        )
    return database_url


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
context = cast(Any, alembic_context)
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option(
    'sqlalchemy.url',
    _build_sync_database_url(app_settings.database_url),
)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = model_base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
