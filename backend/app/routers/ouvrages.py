"""
Router des ouvrages consolidés et CGPE.
"""
from __future__ import annotations

import base64
import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth import require_api_key
from app.db import get_db
from app.deps import CursorPagination, OuvrageFilters
from app.models import CGPE, Localite, Ouvrage, OuvrageProjet, ProjetFinancement, Source, TypeOuvrage
from app.schemas.common import PaginatedCursor
from app.schemas.ouvrages import (
    CGPE as CGPESchema,
    CGPESummary,
    FinancementResume,
    Ouvrage as OuvrageSchema,
    TypeOuvrageResume,
)
from app.schemas.referentiels import LocaliteResume

from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
from app.services.export import (
    export_ouvrages_csv,
    export_ouvrages_xlsx,
    filename_csv,
    filename_xlsx,
)

router = APIRouter(
    tags=["Ouvrages"],
    dependencies=[Depends(require_api_key)],
)


# =====================================================================
# Helpers
# =====================================================================
def _encode_cursor(id_ouvrage: int) -> str:
    """Encode un curseur opaque (base64 de l'id)."""
    return base64.urlsafe_b64encode(str(id_ouvrage).encode()).decode()


def _decode_cursor(cursor: str) -> int:
    """Décode un curseur opaque."""
    try:
        return int(base64.urlsafe_b64decode(cursor.encode()).decode())
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Curseur invalide",
        )


def _build_ouvrage_schema(o: Ouvrage, include_metadata: bool) -> OuvrageSchema:
    """Construit le schéma Ouvrage à partir d'un modèle SQLAlchemy."""
    # Type d'ouvrage
    type_ouvrage = TypeOuvrageResume(
        code=o.type_ouvrage.code,
        libelle=o.type_ouvrage.libelle,
    )

    # Localité
    localite = LocaliteResume(
        id_localite=o.localite.id_localite,
        nom_usage=o.localite.nom_usage,
    )

    # CGPE (résumé)
    cgpe_summary = None
    if o.cgpes:
        c = o.cgpes[0]
        cgpe_summary = CGPESummary(existe=c.existe, statut=c.statut)

    # Financements
    financements = []
    for op in o.financements:
        if op.projet is None:
            continue
        financements.append(
            FinancementResume(
                id_projet=op.projet.id_projet,
                nom_projet=op.projet.nom_projet,
                bailleur=op.projet.financeur.nom if op.projet.financeur else "?",
                role=op.role_financement,
            )
        )

    # GeoJSON
    geom = None
    if o.geom is not None:
        # o.geom est un WKBElement ; on utilise ST_AsGeoJSON via WKT
        # Pour rester simple, on l'extrait via shapely
        try:
            from geoalchemy2.shape import to_shape
            shape = to_shape(o.geom)
            geom = {"type": "Point", "coordinates": [shape.x, shape.y]}
        except Exception:
            geom = None

    return OuvrageSchema(
        id_ouvrage=o.id_ouvrage,
        code_ouvrage=o.code_ouvrage,
        type_ouvrage=type_ouvrage,
        etat=o.etat,
        annee_realisation=o.annee_realisation,
        localite=localite,
        geom=geom,
        cgpe=cgpe_summary,
        financements=financements,
        metadata=o.metadata_ if include_metadata else None,
    )


# =====================================================================
# LISTE DES OUVRAGES
# =====================================================================
@router.get(
    "/ouvrages",
    response_model=PaginatedCursor[OuvrageSchema],
    summary="Liste des ouvrages consolidés",
)
def list_ouvrages(
    filters: OuvrageFilters = Depends(),
    pagination: CursorPagination = Depends(),
    include: Literal["metadata"] | None = Query(None),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Ouvrage)
        .options(
            selectinload(Ouvrage.type_ouvrage),
            selectinload(Ouvrage.localite),
            selectinload(Ouvrage.cgpes),
            selectinload(Ouvrage.financements).selectinload(OuvrageProjet.projet).selectinload(ProjetFinancement.financeur),
        )
    )

    # Filtres
    if filters.type_ouvrage:
        stmt = stmt.join(TypeOuvrage).where(TypeOuvrage.code == filters.type_ouvrage)
    if filters.etat:
        stmt = stmt.where(Ouvrage.etat == filters.etat)
    if filters.annee_min is not None:
        stmt = stmt.where(Ouvrage.annee_realisation >= filters.annee_min)
    if filters.annee_max is not None:
        stmt = stmt.where(Ouvrage.annee_realisation <= filters.annee_max)

    # Cursor
    if pagination.cursor:
        last_id = _decode_cursor(pagination.cursor)
        stmt = stmt.where(Ouvrage.id_ouvrage > last_id)

    stmt = stmt.order_by(Ouvrage.id_ouvrage).limit(pagination.limit + 1)

    rows = db.scalars(stmt).all()
    has_more = len(rows) > pagination.limit
    if has_more:
        rows = rows[: pagination.limit]

    next_cursor = _encode_cursor(rows[-1].id_ouvrage) if has_more and rows else None
    include_metadata = include == "metadata"

    return PaginatedCursor(
        data=[_build_ouvrage_schema(o, include_metadata) for o in rows],
        pagination=pagination.to_response(next_cursor=next_cursor, has_more=has_more),
    )


# =====================================================================
# DÉTAIL D'UN OUVRAGE
# =====================================================================
@router.get(
    "/ouvrages/{id}",
    response_model=OuvrageSchema,
    summary="Détail d'un ouvrage",
)
def get_ouvrage(
    id: int,
    include: Literal["metadata"] | None = Query(None),
    db: Session = Depends(get_db),
):
    o = db.scalar(
        select(Ouvrage)
        .where(Ouvrage.id_ouvrage == id)
        .options(
            selectinload(Ouvrage.type_ouvrage),
            selectinload(Ouvrage.localite),
            selectinload(Ouvrage.cgpes),
            selectinload(Ouvrage.financements).selectinload(OuvrageProjet.projet).selectinload(ProjetFinancement.financeur),
        )
    )
    if o is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ouvrage {id} introuvable",
        )
    return _build_ouvrage_schema(o, include == "metadata")


# =====================================================================
# DÉTAIL D'UN CGPE
# =====================================================================
@router.get(
    "/cgpe/{id}",
    response_model=CGPESchema,
    summary="Détail d'un CGPE",
)
def get_cgpe(
    id: int,
    include: Literal["metadata"] | None = Query(None),
    db: Session = Depends(get_db),
):
    c = db.get(CGPE, id)
    if c is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CGPE {id} introuvable",
        )
    return CGPESchema(
        id_cgpe=c.id_cgpe,
        id_localite=c.id_localite,
        id_ouvrage=c.id_ouvrage,
        existe=c.existe,
        date_creation=c.date_creation,
        statut=c.statut,
        nb_membres=c.nb_membres,
        commentaire=c.commentaire,
        metadata=c.metadata_ if include == "metadata" else None,
    )

# =====================================================================
# EXPORT EXCEL
# =====================================================================
@router.get(
    "/ouvrages/export",
    summary="Export Excel des ouvrages filtrés",
    response_class=StreamingResponse,
)
def export_ouvrages_excel(
    filters: OuvrageFilters = Depends(),
    include: Literal["metadata"] | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Génère un fichier .xlsx streamé avec les ouvrages filtrés.
    Limite : MAX_EXPORT_ROWS (défaut 100 000), au-delà → 413.
    """
    filters_dict = filters.to_dict()
    include_metadata = include == "metadata"

    return StreamingResponse(
        export_ouvrages_xlsx(db, filters_dict, include_metadata),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename_xlsx()}"'
        },
    )


# =====================================================================
# EXPORT CSV
# =====================================================================
@router.get(
    "/ouvrages/export.csv",
    summary="Export CSV des ouvrages filtrés",
    response_class=StreamingResponse,
)
def export_ouvrages_csv_endpoint(
    filters: OuvrageFilters = Depends(),
    include: Literal["metadata"] | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Génère un fichier .csv (UTF-8, séparateur ';') streamé.
    """
    filters_dict = filters.to_dict()
    include_metadata = include == "metadata"

    return StreamingResponse(
        export_ouvrages_csv(db, filters_dict, include_metadata),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename_csv()}"'
        },
    )