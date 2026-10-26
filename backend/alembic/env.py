"""
Configuration Alembic.

- Charge l'URL DB depuis app.config (pas depuis alembic.ini)
- Importe tous les modèles pour qu'autogenerate les voie
- Exclut strictement les schémas PostGIS (tiger, topology) et spatial_ref_sys
- Mode offline (SQL) et online (engine) supportés
"""
from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# --- Ajout du répertoire backend au PYTHONPATH ---
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import get_settings  # noqa: E402
from app.db import Base  # noqa: E402
from app import models  # noqa: F401,E402


# --- Alembic Config ---
config = context.config

# --- Logging ---
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- URL DB depuis app.config ---
settings = get_settings()
config.set_main_option("sqlalchemy.url", str(settings.database_url))

# --- Metadata cible ---
target_metadata = Base.metadata


# --- Filtre des objets à ignorer dans l'autogenerate ---
def include_object(object, name, type_, reflected, compare_to):
    """
    Exclut les objets gérés par PostGIS ou Alembic lui-même.

    On filtre par nom ET par schéma, car object.schema peut être None
    dans certains contextes Alembic.
    """
    # Tables de PostGIS / Alembic à ne jamais toucher
    TABLES_INTERDITES = {
        "spatial_ref_sys",
        "alembic_version",
        "layer",          # topology.layer
        "topology",       # topology.topology
    }
    if type_ == "table":
        if name in TABLES_INTERDITES:
            return False
        # Filtre par schéma (si disponible)
        schema = getattr(object, "schema", None)
        if schema in ("tiger", "topology"):
            return False
    return True


def run_migrations_offline() -> None:
    """Mode offline : génère le SQL sans se connecter."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=False,        # ← FALSE : on ne compare que le schéma public
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Mode online : se connecte et applique les migrations."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=False,    # ← FALSE : on ne compare que le schéma public
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()