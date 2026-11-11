"""
Fixtures pytest pour les tests backend.

Stratégie (MVP) :
- On utilise la MÊME base que l'application (`dhr`), pas une base séparée.
- Les migrations sont déjà appliquées (le backend a démarré).
- Chaque test ouvre une transaction et fait un rollback à la fin.
  → Les données insérées par les fixtures ne polluent pas `dhr`.

Prérequis :
- Le backend a démarré au moins une fois (migrations appliquées).
- Les extensions PostGIS, pg_trgm, unaccent, fuzzystrmatch sont installées.
"""
from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db import Base, get_db
from app.main import app


# =====================================================================
# Configuration de la base (même base que l'application)
# =====================================================================
@pytest.fixture(scope="session")
def test_db_url() -> str:
    """
    URL de la base de test.
    On utilise la même base que l'app (`dhr`), car les migrations y sont
    déjà appliquées. Le rollback par test évite la pollution.
    """
    return str(get_settings().database_url)


@pytest.fixture(scope="session", autouse=True)
def engine(test_db_url: str):
    """Crée l'engine SQLAlchemy pour la base `dhr`."""
    eng = create_engine(test_db_url, pool_pre_ping=True, future=True)
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def apply_migrations(engine) -> None:
    """
    Vérifie que les migrations sont déjà appliquées sur `dhr`.
    Ne fait PAS de DROP SCHEMA (on ne veut pas détruire les données de dev).

    Si les tables n'existent pas, on lève une erreur claire qui invite à
    lancer `alembic upgrade head` sur `dhr`.
    """
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            )
        ).scalar()

    if result is None or result < 13:
        raise RuntimeError(
            f"La base `dhr` ne contient que {result} tables (attendu : 13). "
            "Lance `alembic upgrade head` sur `dhr` avant de lancer les tests."
        )


@pytest.fixture()
def db(engine, apply_migrations) -> Generator[Session, None, None]:
    """
    Session SQLAlchemy pour un test.
    Ouvre une transaction, yield la session, puis ROLLBACK à la fin.
    → Les données insérées par le test ne polluent pas `dhr`.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, expire_on_commit=False)()

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
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
    """
    Source ONEP (seedée normalement par la migration).
    Si elle n'existe pas, on la crée à la volée (mais elle devrait exister).
    """
    from app.models import Source
    src = db.query(Source).filter(Source.nom == "ONEP").first()
    if src is None:
        src = Source(
            nom="ONEP",
            type_source="public",
            commentaire="Office National de l'Eau Potable",
        )
        db.add(src)
        db.flush()
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
    Chemin vers le fichier Excel de test.
    Créé dans /tmp/ (toujours writable, même si tests/ est read-only).
    """
    path = Path("/tmp/test_pmh.xlsx")

    if not path.exists():
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "PMH"

        ws.append([
            "Localité", "Latitude", "Longitude", "Type_Ouvrage",
            "Etat", "Année", "Bailleur", "Usage_Ouvrage", "A_CGPE",
        ])
        ws.append(["LOC_TEST", 7.5, -5.5, "Forage ADM", "Fonctionnel", 2020, "ONEP", "PMH", "Oui"])
        ws.append(["LOC_TEST", None, None, "PMH", "En panne", 2019, "ONEP", "PMH", "Non"])
        ws.append(["TOTAL", "", "", "", "", "", "", "", ""])
        ws.append([None, None, None, None, None, None, None, None, None])

        wb.save(path)

    return path