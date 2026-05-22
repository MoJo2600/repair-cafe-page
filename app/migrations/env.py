"""Alembic configuration and main script."""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure the project root ('app' package parent) is on sys.path so that
# 'from app.models import db' works whether this file is invoked via
# run_migrations.py or the alembic CLI directly.
_MIGRATIONS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_MIGRATIONS_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# This is the Alembic Config object
config = context.config


def _build_db_url() -> str:
    """Build the database URL from environment variables (same defaults as BaseConfig)."""
    host = os.environ.get("MYSQL_HOST", "db")
    database = os.environ.get("MYSQL_DATABASE", "repaircafepage")
    user = os.environ.get("MYSQL_USER", "root")
    password = os.environ.get("MYSQL_PASSWORD", "mariadb")
    port = os.environ.get("MYSQL_PORT", "3306")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


# Override the placeholder URL from alembic.ini with the real one from env vars.
_ini_url = config.get_main_option("sqlalchemy.url")
if not _ini_url or _ini_url == "driver://user:pass@localhost/dbname":
    config.set_main_option("sqlalchemy.url", _build_db_url())

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# db.metadata is populated when models are imported; no app context required.
from app.models import db  # noqa: E402

target_metadata = db.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = _build_db_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
