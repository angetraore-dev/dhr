"""
Point d'entrée FastAPI.

Pour le MVP initial (Phase 1), seuls /health et / sont exposés.
Les routers (référentiels, fichiers, ingestion, ouvrages, carto, qualité)
seront ajoutés en Phase 2 (section 4.6).
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app import __version__
from app.config import get_settings
from app.db import check_db

# --- Logging ---
settings = get_settings()
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("dhr")


# --- Application ---
app = FastAPI(
    title="API DHR",
    version=__version__,
    description=(
        "API de la Direction de l'Hydraulique Rurale (DHR) pour la centralisation "
        "des ouvrages hydrauliques ruraux. Voir /docs pour la documentation interactive."
    ),
    default_response_class=ORJSONResponse,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Routes de base ---
@app.get("/", tags=["meta"], summary="Racine")
def root() -> dict:
    """Retourne les informations de base de l'API."""
    return {
        "name": "API DHR",
        "version": __version__,
        "env": settings.env,
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"], summary="Healthcheck")
def health() -> dict:
    """
    Healthcheck utilisé par Docker Compose et le front.

    Retourne :
    - 200 + {"status": "ok", "db": true} si tout va bien
    - 503 + {"status": "degraded", "db": false} si la DB ne répond pas
    """
    db_ok = check_db()
    status_code = 200 if db_ok else 503
    return ORJSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if db_ok else "degraded",
            "db": db_ok,
            "version": __version__,
            "env": settings.env,
        },
    )


# --- Démarrage ---
@app.on_event("startup")
def on_startup() -> None:
    logger.info("Démarrage API DHR v%s (env=%s)", __version__, settings.env)
    if not check_db():
        logger.warning("La base de données ne répond pas au démarrage")