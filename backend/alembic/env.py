"""
Configuration Alembic.

Filtre strict : ne compare QUE les tables de Base.metadata.
Toute autre table (PostGIS, tiger, topology, spatial_ref_sys, alembic_version)
est ignorée.

Garde-fou : si Base.metadata.tables est vide, on lève une exception
plutôt que de laisser Alembic ne rien faire silencieusement.

NOTE — faux positifs d'autogenerate :
Les migrations autogénérées (`alembic revision --autogenerate`) contiendront
TOUJOURS des faux positifs sur :
  - les colonnes générées (`geom`, `geom_centre`)
  - les index GIN et GIST
Ces objets sont créés en SQL brut dans les migrations (SQLAlchemy ne les gère
pas nativement). Ne PAS appliquer ces migrations de test. Vérifier qu'elles
ne contiennent pas de `op.drop_table` ou `op.drop_column` sur des colonnes
non générées (ce qui signalerait une vraie dérive).
"""
from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# --- Assure que le package `app` est importable ---
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import get_settings  # noqa: E402
from app.db import Base  # noqa: E402
from app import models  # noqa: F401, E402

# --- Config Alembic ---
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# --- Résolution de l'URL SQLAlchemy ---
# Priorité :
#   1. URL déjà définie dans la config (cas des tests via
#      `alembic_cfg.set_main_option("sqlalchemy.url", ...)`, ou cas
#      d'un override CLI via `-x sqlalchemy.url=...`).
#   2. URL par défaut depuis `settings.database_url` (cas prod/dev).
#
# On ignore les valeurs de `alembic.ini` qui seraient des placeholders
# non résolus (`%(...)s`) ou des chaînes vides.
settings = get_settings()
url_from_cfg = config.get_main_option("sqlalchemy.url")
if not url_from_cfg or url_from_cfg.startswith("%(") or "${" in url_from_cfg:
    config.set_main_option("sqlalchemy.url", str(settings.database_url))


# --- Liste blanche : uniquement nos tables ---
NOS_TABLES = set(Base.metadata.tables.keys())

if not NOS_TABLES:
    raise RuntimeError(
        "Base.metadata.tables est vide. "
        "Vérifie que `from app import models` importe bien TOUS les modèles "
        "(sinon Alembic ne créera aucune table silencieusement)."
    )

print(f"[alembic] Tables gérées par Alembic : {sorted(NOS_TABLES)}")

# Tables explicitement exclues (en plus de celles hors NOS_TABLES)
EXCLUDED_TABLES = {"alembic_version"}


def include_object(object, name, type_, reflected, compare_to):
    """
    N'inclut QUE les tables de Base.metadata.
    Toute autre table (PostGIS, tiger, topology, alembic_version, ...) est exclue.
    """
    if type_ == "table":
        if name in EXCLUDED_TABLES:
            return False
        return name in NOS_TABLES
    if type_ == "index":
        table = getattr(object, "table", None)
        if table is not None:
            return table.name in NOS_TABLES
        return False
    return True


# --- Modes offline / online ---
def run_migrations_offline() -> None:
    """Exécute les migrations en mode 'offline' (sans connexion DB)."""
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
    """Exécute les migrations en mode 'online' (avec connexion DB)."""
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