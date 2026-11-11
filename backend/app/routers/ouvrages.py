"""
Router des ouvrages consolidés et CGPE.
"""
from __future__ import annotations

import base64
import json
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, literal_column, select
from sqlalchemy.orm import Session, selectinload

from app.auth import require_api_key
from app.db import get_db
from app.deps import CursorPagination, OuvrageFilters
from app.models import (
    CGPE,
    Localite,
    Ouvrage,
    OuvrageProjet,
    ProjetFinancement,
    RefGeoAdmin,
)
from app.schemas.common import PaginatedCursor
from app.schemas.ouvrages import CGPE as CGPESchema  # noqa: N811
from app.schemas.ouvrages import CGPESummary, FinancementResume
from app.schemas.ouvrages import Ouvrage as OuvrageSchema
from app.schemas.referentiels import LocaliteResume
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
    return base64.urlsafe_b64encode(str(id_ouvrage).encode()).decode()


def _decode_cursor(cursor: str) -> int:
    try:
        return int(base64.urlsafe_b64decode(cursor.encode()).decode())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Curseur invalide",
        ) from e


def _parse_geojson(geojson_str: str | None) -> dict[str, Any] | None:
    if not geojson_str:
        return None
    try:
        data = json.loads(geojson_str)
        return {
            "type": data.get("type", "Point"),
            "coordinates": data.get("coordinates"),
        }
    except (json.JSONDecodeError, TypeError):
        return None


def _build_ouvrage_schema(
    o: Ouvrage,
    include_metadata: bool,
    geojson_str: str | None = None,
) -> OuvrageSchema:
    localite = LocaliteResume(
        id_localite=o.localite.id_localite,
        nom_usage=o.localite.nom_usage,
    )
    cgpe_summary = None
    if o.cgpes:
        c = o.cgpes[0]
        cgpe_summary = CGPESummary(existe=c.existe, statut=c.statut)

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

    geom = _parse_geojson(geojson_str)

    return OuvrageSchema(
        id_ouvrage=o.id_ouvrage,
        code_ouvrage=o.code_ouvrage,
        nature_ouvrage=o.nature_ouvrage,
        type_alimentation=o.type_alimentation,
        realisation_par=o.realisation_par,
        etat=o.etat,
        annee_realisation=o.annee_realisation,
        localite=localite,
        geom=geom,
        cgpe=cgpe_summary,
        financements=financements,
        metadata=o.metadata_ if include_metadata else None,
        qualite_eau=o.qualite_eau,   # ← ajout (IMP-1)
    )


def _apply_geo_filters(stmt, filters: OuvrageFilters):
    """Applique les filtres géographiques (region, departement, sous_prefecture, localite)."""
    if not (filters.region or filters.departement or filters.sous_prefecture or filters.localite):
        return stmt

    stmt = stmt.join(Ouvrage.localite)

    rg_loc = RefGeoAdmin.__table__.alias("rg_loc")
    rg_sp = RefGeoAdmin.__table__.alias("rg_sp")
    rg_dep = RefGeoAdmin.__table__.alias("rg_dep")
    rg_reg = RefGeoAdmin.__table__.alias("rg_reg")

    stmt = stmt.join(rg_loc, Localite.id_geo == rg_loc.c.id_geo)
    stmt = stmt.outerjoin(rg_sp, rg_loc.c.parent_id == rg_sp.c.id_geo)
    stmt = stmt.outerjoin(rg_dep, rg_sp.c.parent_id == rg_dep.c.id_geo)
    stmt = stmt.outerjoin(rg_reg, rg_dep.c.parent_id == rg_reg.c.id_geo)

    if filters.region:
        stmt = stmt.where(rg_reg.c.nom == filters.region)
    if filters.departement:
        stmt = stmt.where(rg_dep.c.nom == filters.departement)
    if filters.sous_prefecture:
        stmt = stmt.where(rg_sp.c.nom == filters.sous_prefecture)
    if filters.localite:
        stmt = stmt.where(Localite.nom_usage.ilike(f"%{filters.localite}%"))

    return stmt


def _apply_bailleur_filter(stmt, filters: OuvrageFilters):
    """Applique le filtre bailleur (jointure sur ouvrage_projet + projet_financement)."""
    if not getattr(filters, "bailleur", None):
        return stmt
    from app.models import Source
    stmt = (
        stmt.join(OuvrageProjet)
        .join(ProjetFinancement)
        .join(Source)
        .where(Source.nom == filters.bailleur)
    )
    return stmt


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
        select(
            Ouvrage,
            func.ST_AsGeoJSON(literal_column("ouvrage.geom")).label("geojson"),
        )
        .options(
            # Note : on NE fait PAS selectinload sur type_alimentation /
            # nature_ouvrage, ce sont des colonnes (pas des relations).
            selectinload(Ouvrage.localite),
            selectinload(Ouvrage.cgpes),
            selectinload(Ouvrage.financements)
            .selectinload(OuvrageProjet.projet)
            .selectinload(ProjetFinancement.financeur),
        )
    )

    # Filtres métier
    if filters.type_alimentation:
        stmt = stmt.where(Ouvrage.type_alimentation == filters.type_alimentation)
    if filters.nature_ouvrage:
        stmt = stmt.where(Ouvrage.nature_ouvrage == filters.nature_ouvrage)
    if filters.realisation_par:
        stmt = stmt.where(Ouvrage.realisation_par == filters.realisation_par)
    if filters.etat:
        stmt = stmt.where(Ouvrage.etat == filters.etat)
    if filters.annee_min is not None:
        stmt = stmt.where(Ouvrage.annee_realisation >= filters.annee_min)
    if filters.annee_max is not None:
        stmt = stmt.where(Ouvrage.annee_realisation <= filters.annee_max)

    # Filtres géo et bailleur
    stmt = _apply_geo_filters(stmt, filters)
    stmt = _apply_bailleur_filter(stmt, filters)

    if pagination.cursor:
        last_id = _decode_cursor(pagination.cursor)
        stmt = stmt.where(Ouvrage.id_ouvrage > last_id)

    stmt = stmt.order_by(Ouvrage.id_ouvrage).limit(pagination.limit + 1)

    rows = db.execute(stmt).all()
    has_more = len(rows) > pagination.limit
    if has_more:
        rows = rows[: pagination.limit]

    next_cursor = _encode_cursor(rows[-1][0].id_ouvrage) if has_more and rows else None
    include_metadata = include == "metadata"

    data = [
        _build_ouvrage_schema(row[0], include_metadata, row[1])
        for row in rows
    ]

    return PaginatedCursor(
        data=data,
        pagination=pagination.to_response(next_cursor=next_cursor, has_more=has_more),
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
    with_summary: bool = Query(True, description="Inclure la feuille Synthèse"),
    db: Session = Depends(get_db),
):
    filters_dict = filters.to_dict()
    include_metadata = include == "metadata"

    return StreamingResponse(
        export_ouvrages_xlsx(db, filters_dict, include_metadata, with_summary),
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
    filters_dict = filters.to_dict()
    include_metadata = include == "metadata"

    return StreamingResponse(
        export_ouvrages_csv(db, filters_dict, include_metadata),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename_csv()}"'
        },
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
    stmt = (
        select(
            Ouvrage,
            func.ST_AsGeoJSON(literal_column("ouvrage.geom")).label("geojson"),
        )
        .where(Ouvrage.id_ouvrage == id)
        .options(
            selectinload(Ouvrage.localite),
            selectinload(Ouvrage.cgpes),
            selectinload(Ouvrage.financements)
            .selectinload(OuvrageProjet.projet)
            .selectinload(ProjetFinancement.financeur),
        )
    )
    row = db.execute(stmt).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ouvrage {id} introuvable",
        )
    return _build_ouvrage_schema(row[0], include == "metadata", row[1])


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
