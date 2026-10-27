"""
Configuration Alembic.

Filtre strict : ne compare QUE les tables de Base.metadata.
Toute autre table (PostGIS, tiger, topology, spatial_ref_sys) est ignorée.
"""
from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import get_settings  # noqa: E402
from app.db import Base  # noqa: E402
from app import models  # noqa: F401,E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", str(settings.database_url))


# --- Liste blanche : uniquement nos tables ---
NOS_TABLES = set(Base.metadata.tables.keys())


def include_object(object, name, type_, reflected, compare_to):
    """
    N'inclut QUE les tables de Base.metadata.
    Toute autre table (PostGIS, tiger, topology, alembic_version, ...) est exclue.
    """
    if type_ == "table":
        return name in NOS_TABLES
    if type_ == "index":
        table = getattr(object, "table", None)
        if table is not None:
            return table.name in NOS_TABLES
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=False,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=False,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()