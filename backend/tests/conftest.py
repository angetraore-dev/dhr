"""
Fixtures pytest pour les tests backend.

Stratégie :
- Une base PostgreSQL éphémère par session de test (via pytest-postgresql).
- Un schéma recréé à chaque test (transaction rollback après chaque test).
- Un client HTTP FastAPI avec dépendances overridées pour utiliser la session de test.

Prérequis :
- PostgreSQL doit être accessible (via DATABASE_URL ou valeurs par défaut).
- Les extensions PostGIS, pg_trgm, unaccent, fuzzystrmatch doivent être disponibles.
"""
from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base, get_db
from app.main import app


# =====================================================================
# Configuration de la base de test
# =====================================================================
@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Retourne l'URL de la base de test."""
    # Priorité 1 : variable d'environnement dédiée
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        return url

    # Priorité 2 : construire depuis les variables PG standard
    user = os.environ.get("POSTGRES_USER", "dhr")
    password = os.environ.get("POSTGRES_PASSWORD", "dhr")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_TEST_DB", "dhr_test")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


@pytest.fixture(scope="session")
def engine(test_db_url: str):
    """Crée l'engine SQLAlchemy pour la base de test."""
    eng = create_engine(test_db_url, pool_pre_ping=True, future=True)
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def apply_migrations(engine) -> None:
    """
    Applique les migrations Alembic une seule fois par session.
    Utilise la config Alembic du projet.
    """
    backend_dir = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", str(engine.url))

    # Reset le schéma public
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()

    # Applique les migrations
    command.upgrade(alembic_cfg, "head")


@pytest.fixture()
def db(engine, apply_migrations) -> Generator[Session, None, None]:
    """
    Session SQLAlchemy pour un test.
    Rollback automatique après le test (isolation).
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, expire_on_commit=False)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Client HTTP FastAPI avec get_db overridé pour utiliser la session de test.
    """
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# =====================================================================
# Fixtures de données
# =====================================================================
@pytest.fixture()
def source_onep(db: Session):
    """Source ONEP (seedée normalement, mais on la récupère)."""
    from app.models import Source
    src = db.query(Source).filter(Source.nom == "ONEP").first()
    assert src is not None, "Source ONEP absente (le seed n'a pas été appliqué)"
    return src


@pytest.fixture()
def fichier_vide(db: Session, source_onep):
    """Crée un fichier sans feuille (pour tester l'upload)."""
    from app.models import Fichier
    f = Fichier(
        id_source=source_onep.id_source,
        nom_fichier_original="test.xlsx",
        chemin_stockage="/tmp/test.xlsx",
        statut="en_attente",
    )
    db.add(f)
    db.flush()
    return f


@pytest.fixture()
def ref_geo_ci(db: Session):
    """
    Crée une mini-hiérarchie administrative :
    DISTRICT_TEST → REGION_TEST → DEPT_TEST → SP_TEST → LOCALITE_TEST.
    Retourne la localité de niveau 'localite'.
    """
    from app.models import RefGeoAdmin

    district = RefGeoAdmin(niveau="district", nom="DISTRICT_TEST", parent_id=None)
    db.add(district)
    db.flush()

    region = RefGeoAdmin(niveau="region", nom="REGION_TEST", parent_id=district.id_geo)
    db.add(region)
    db.flush()

    dept = RefGeoAdmin(niveau="departement", nom="DEPT_TEST", parent_id=region.id_geo)
    db.add(dept)
    db.flush()

    sp = RefGeoAdmin(niveau="sous_prefecture", nom="SP_TEST", parent_id=dept.id_geo)
    db.add(sp)
    db.flush()

    loc = RefGeoAdmin(
        niveau="localite", nom="LOC_TEST", parent_id=sp.id_geo, type_localite="village"
    )
    db.add(loc)
    db.flush()

    return loc


@pytest.fixture()
def localite_test(db: Session, ref_geo_ci):
    """Crée une localité métier rattachée à LOCALITE_TEST."""
    from app.models import Localite
    loc = Localite(
        id_geo=ref_geo_ci.id_geo,
        nom_usage="LOC_TEST",
        latitude_centre=7.5,
        longitude_centre=-5.5,
    )
    db.add(loc)
    db.flush()
    return loc


@pytest.fixture()
def fichier_avec_feuille(db: Session, source_onep):
    """Crée un fichier + une feuille, prêt pour un run."""
    from app.models import Feuille, Fichier
    f = Fichier(
        id_source=source_onep.id_source,
        nom_fichier_original="test.xlsx",
        chemin_stockage="/tmp/test.xlsx",
        statut="en_attente",
    )
    db.add(f)
    db.flush()
    fe = Feuille(
        id_fichier=f.id_fichier,
        nom_feuille="PMH",
        index_feuille=1,
        type_contenu="ouvrages",
    )
    db.add(fe)
    db.flush()
    return f, fe


# =====================================================================
# Fixture : fichier Excel de test
# =====================================================================
@pytest.fixture(scope="session")
def excel_fixture_path() -> Path:
    """
    Chemin vers le fichier Excel de test (créé dans tests/fixtures/).
    Si le fichier n'existe pas, il est créé à la volée.
    """
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)
    path = fixtures_dir / "test_pmh.xlsx"

    if not path.exists():
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "PMH"

        # Entête
        ws.append([
            "Localité", "Latitude", "Longitude", "Type_Ouvrage",
            "Etat", "Année", "Bailleur", "Usage_Ouvrage", "A_CGPE",
        ])
        # 1 ligne valide
        ws.append(["LOC_TEST", 7.5, -5.5, "Forage ADM", "Fonctionnel", 2020, "ONEP", "PMH", "Oui"])
        # 1 ligne sans coordonnées
        ws.append(["LOC_TEST", None, None, "PMH", "En panne", 2019, "ONEP", "PMH", "Non"])
        # 1 ligne de total (rejetée)
        ws.append(["TOTAL", "", "", "", "", "", "", "", ""])
        # 1 ligne vide
        ws.append([None, None, None, None, None, None, None, None, None])

        wb.save(path)

    return path