"""
Point d'entrée FastAPI.

Phase 3 : ajout des routers + authentification API key.
Phase D : handlers d'erreur RFC 7807 + lifespan.
"""
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse as _ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.config import get_settings
from app.db import check_db

# Routers
from app.routers import (
    carto,
    fichiers,
    ingestion,
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


# =====================================================================
# RFC 7807 — Problem Details
# =====================================================================
# Base des URI de type d'erreur. Doit rester aligné sur la Bible § 4.4.
_ERROR_TYPE_BASE = "https://api.dhr.local/errors"

# Mapping code HTTP → (slug du type, titre lisible).
# Pour les codes non listés, on retombe sur un slug générique "http-<code>".
_ERROR_TYPES: dict[int, tuple[str, str]] = {
    400: ("bad-request", "Bad Request"),
    401: ("unauthorized", "Unauthorized"),
    403: ("forbidden", "Forbidden"),
    404: ("not-found", "Not Found"),
    409: ("conflict", "Conflict"),
    413: ("payload-too-large", "Payload Too Large"),
    422: ("validation", "Validation Error"),
    500: ("internal", "Internal Server Error"),
}


def _problem_response(
    *,
    status_code: int,
    detail: str | None,
    instance: str | None,
    errors: list[dict[str, Any]] | None = None,
) -> ORJSONResponse:
    """Construit une réponse RFC 7807 (Problem Details)."""
    slug, title = _ERROR_TYPES.get(
        status_code, (f"http-{status_code}", "Error")
    )
    body: dict[str, Any] = {
        "type": f"{_ERROR_TYPE_BASE}/{slug}",
        "title": title,
        "status": status_code,
    }
    if detail is not None:
        body["detail"] = detail
    if instance is not None:
        body["instance"] = instance
    if errors is not None:
        body["errors"] = errors
    return ORJSONResponse(status_code=status_code, content=body)


# =====================================================================
# Lifespan
# =====================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown (remplace @app.on_event)."""
    logger.info("Démarrage API DHR v%s (env=%s)", __version__, settings.env)
    if not check_db():
        logger.warning("La base de données ne répond pas au démarrage")
    yield
    logger.info("Arrêt API DHR")


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
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# Exception handlers RFC 7807
# =====================================================================
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> ORJSONResponse:
    """Convertit toute HTTPException en Problem Details.

    `exc.detail` peut être :
    - une chaîne → utilisée comme `detail` ;
    - un dict → si contient `type`/`title`/`status`, on le prend tel quel
      (permet aux routers de lever des Problem structurés) ;
    - autre → sérialisé en str.
    """
    detail: str | None = None
    errors: list[dict[str, Any]] | None = None

    if isinstance(exc.detail, dict):
        # Permet aux routers d'envoyer un Problem pré-formé.
        if "type" in exc.detail and "title" in exc.detail:
            body = dict(exc.detail)
            body.setdefault("status", exc.status_code)
            body.setdefault("instance", request.url.path)
            return ORJSONResponse(status_code=exc.status_code, content=body)
        # Sinon on extrait les champs connus.
        detail = exc.detail.get("detail") or exc.detail.get("message")
        errors = exc.detail.get("errors")
    elif exc.detail is not None:
        detail = str(exc.detail)

    return _problem_response(
        status_code=exc.status_code,
        detail=detail,
        instance=request.url.path,
        errors=errors,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> ORJSONResponse:
    """Convertit les erreurs Pydantic (422) en Problem Details.

    Chaque erreur est aplatie en `{field, message}` pour rester lisible
    côté UI (Bible § 4.4).
    """
    errors: list[dict[str, Any]] = []
    for err in exc.errors():
        # `loc` est un tuple du type ("query", "ligne_fin") ou ("body", ...).
        loc = [str(p) for p in err.get("loc", []) if p != "body"]
        field = ".".join(loc) if loc else "(racine)"
        errors.append({"field": field, "message": err.get("msg", "invalide")})

    return _problem_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Le body ou les paramètres de la requête sont invalides.",
        instance=request.url.path,
        errors=errors,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> ORJSONResponse:
    """Filet de sécurité : toute exception non gérée → 500 RFC 7807.

    On log l'exception complète côté serveur, mais on n'expose pas
    la stacktrace au client.
    """
    logger.exception("Exception non gérée sur %s : %s", request.url.path, exc)
    return _problem_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Une erreur interne est survenue.",
        instance=request.url.path,
    )


# =====================================================================
# Routes de base
# =====================================================================
@app.get("/", tags=["meta"], summary="Racine")
def root() -> dict:
    return {
        "name": "API DHR",
        "version": __version__,
        "env": settings.env,
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"], summary="Healthcheck")
def health() -> ORJSONResponse:
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


# =====================================================================
# Routers v1
# =====================================================================
app.include_router(referentiels.router, prefix="/v1")
app.include_router(fichiers.router, prefix="/v1")
app.include_router(ouvrages.router, prefix="/v1")
app.include_router(carto.router, prefix="/v1")
app.include_router(qualite.router, prefix="/v1")
app.include_router(ingestion.router, prefix="/v1")
