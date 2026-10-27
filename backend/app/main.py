"""
Point d'entrée FastAPI.

Phase 3 : ajout des routers + authentification API key.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse as _ORJSONResponse

from app import __version__
from app.config import get_settings
from app.db import check_db


# Routers
from app.routers import (
    carto,
    fichiers,
    ouvrages,
    qualite,
    referentiels,
)


class ORJSONResponse(_ORJSONResponse):
    """ORJSONResponse avec charset=utf-8 explicite."""

    media_type = "application/json; charset=utf-8"

settings = get_settings()
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("dhr")

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
    return {
        "name": "API DHR",
        "version": __version__,
        "env": settings.env,
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"], summary="Healthcheck")
def health() -> dict:
    db_ok = check_db()
    return ORJSONResponse(
        status_code=200 if db_ok else 503,
        content={
            "status": "ok" if db_ok else "degraded",
            "db": db_ok,
            "version": __version__,
            "env": settings.env,
        },
    )


# --- Routers v1 ---
app.include_router(referentiels.router, prefix="/v1")
app.include_router(fichiers.router, prefix="/v1")
app.include_router(ouvrages.router, prefix="/v1")
app.include_router(carto.router, prefix="/v1")
app.include_router(qualite.router, prefix="/v1")


@app.on_event("startup")
def on_startup() -> None:
    logger.info("Démarrage API DHR v%s (env=%s)", __version__, settings.env)
    if not check_db():
        logger.warning("La base de données ne répond pas au démarrage")