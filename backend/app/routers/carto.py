"""
Router carto : endpoints GeoJSON pour l'UI cartographique.
"""
from __future__ import annotations

import json
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import require_api_key
from app.db import get_db
from app.deps import OuvrageFilters
from app.models import Feuille, Fichier, LigneIngeree, Ouvrage, TypeOuvrage

router = APIRouter(
    tags=["Carto"],
    dependencies=[Depends(require_api_key)],
)


# =====================================================================
# Helpers GeoJSON
# =====================================================================
def _ligne_to_feature(ligne: LigneIngeree, fichier: Fichier) -> dict[str, Any] | None:
    """Convertit une ligne ingérée en Feature GeoJSON."""
    if ligne.geom is None:
        return None
    try:
        from geoalchemy2.shape import to_shape
        shape = to_shape(ligne.geom)
    except Exception:
        return None

    return {
        "type": "Feature",
        "id": str(ligne.id_ligne),
        "geometry": {"type": "Point", "coordinates": [shape.x, shape.y]},
        "properties": {
            "id_ligne": ligne.id_ligne,
            "id_fichier": fichier.id_fichier,
            "nom_fichier": fichier.nom_fichier_original,
            "type_ouvrage": ligne.type_ouvrage_brut,
            "statut_qualite": ligne.statut_qualite,
            "localite": ligne.localite_brute,
        },
    }


def _ouvrage_to_feature(o: Ouvrage) -> dict[str, Any] | None:
    """Convertit un ouvrage en Feature GeoJSON."""
    if o.geom is None:
        return None
    try:
        from geoalchemy2.shape import to_shape
        shape = to_shape(o.geom)
    except Exception:
        return None

    return {
        "type": "Feature",
        "id": str(o.id_ouvrage),
        "geometry": {"type": "Point", "coordinates": [shape.x, shape.y]},
        "properties": {
            "id_ouvrage": o.id_ouvrage,
            "code_ouvrage": o.code_ouvrage,
            "type_ouvrage": o.type_ouvrage.code if o.type_ouvrage else None,
            "etat": o.etat,
            "annee_realisation": o.annee_realisation,
            "localite": o.localite.nom_usage if o.localite else None,
        },
    }


def _build_feature_collection_fichier(
    id_fichier: int,
    id_feuille: int | None,
    id_run: int | None,
    statut_qualite: str | None,
    type_ouvrage: str | None,
    db: Session,
) -> dict[str, Any]:
    """
    Logique métier partagée par points_fichier et telecharger_geojson_fichier.
    N'est PAS une route FastAPI (pas de décorateur).
    """
    fichier = db.get(Fichier, id_fichier)
    if fichier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fichier {id_fichier} introuvable",
        )

    feuilles_ids = db.scalars(
        select(Feuille.id_feuille).where(Feuille.id_fichier == id_fichier)
    ).all()

    if not feuilles_ids:
        return {
            "type": "FeatureCollection",
            "features": [],
            "meta": {
                "id_fichier": id_fichier,
                "nom_fichier": fichier.nom_fichier_original,
                "count": 0,
            },
        }

    stmt = select(LigneIngeree).where(LigneIngeree.id_feuille.in_(feuilles_ids))
    if id_feuille is not None:
        stmt = stmt.where(LigneIngeree.id_feuille == id_feuille)
    if id_run is not None:
        stmt = stmt.where(LigneIngeree.id_run == id_run)
    if statut_qualite is not None:
        stmt = stmt.where(LigneIngeree.statut_qualite == statut_qualite)
    if type_ouvrage is not None:
        stmt = stmt.where(LigneIngeree.type_ouvrage_brut == type_ouvrage)

    lignes = db.scalars(stmt).all()
    features = [
        f for f in (_ligne_to_feature(l, fichier) for l in lignes) if f is not None
    ]

    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            "id_fichier": id_fichier,
            "nom_fichier": fichier.nom_fichier_original,
            "count": len(features),
        },
    }


# =====================================================================
# POINTS D'UN FICHIER (route)
# =====================================================================
@router.get(
    "/carto/fichiers/{id_fichier}/points",
    summary="Points d'un fichier (GeoJSON)",
    operation_id="get_points_fichier",
)
def points_fichier(
    id_fichier: int,
    id_feuille: int | None = Query(None),
    id_run: int | None = Query(None),
    statut_qualite: Literal[
        "ok", "localite_non_resolue", "geom_invalide",
        "type_ouvrage_inconnu", "rejete", "doublon_suspect",
    ] | None = Query(None),
    type_ouvrage: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return _build_feature_collection_fichier(
        id_fichier=id_fichier,
        id_feuille=id_feuille,
        id_run=id_run,
        statut_qualite=statut_qualite,
        type_ouvrage=type_ouvrage,
        db=db,
    )


# =====================================================================
# TOUS LES POINTS (OUVRAGES CONSOLIDÉS)
# =====================================================================
@router.get(
    "/carto/tous/points",
    summary="Tous les ouvrages consolidés (GeoJSON)",
    operation_id="get_tous_points",
)
def points_tous(
    filters: OuvrageFilters = Depends(),
    db: Session = Depends(get_db),
):
    stmt = select(Ouvrage).options(
        selectinload(Ouvrage.type_ouvrage),
        selectinload(Ouvrage.localite),
    )

    if filters.type_ouvrage:
        stmt = stmt.join(TypeOuvrage).where(TypeOuvrage.code == filters.type_ouvrage)
    if filters.etat:
        stmt = stmt.where(Ouvrage.etat == filters.etat)
    if filters.annee_min is not None:
        stmt = stmt.where(Ouvrage.annee_realisation >= filters.annee_min)
    if filters.annee_max is not None:
        stmt = stmt.where(Ouvrage.annee_realisation <= filters.annee_max)

    ouvrages = db.scalars(stmt).all()
    features = [f for f in (_ouvrage_to_feature(o) for o in ouvrages) if f is not None]

    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {"count": len(features)},
    }


# =====================================================================
# TÉLÉCHARGEMENT GEOJSON
# =====================================================================
@router.get(
    "/carto/fichiers/{id_fichier}/points.geojson",
    summary="Téléchargement GeoJSON des points d'un fichier",
    operation_id="download_points_fichier_geojson",
)
def telecharger_geojson_fichier(
    id_fichier: int,
    id_feuille: int | None = Query(None),
    id_run: int | None = Query(None),
    statut_qualite: Literal[
        "ok", "localite_non_resolue", "geom_invalide",
        "type_ouvrage_inconnu", "rejete", "doublon_suspect",
    ] | None = Query(None),
    db: Session = Depends(get_db),
):
    data = _build_feature_collection_fichier(
        id_fichier=id_fichier,
        id_feuille=id_feuille,
        id_run=id_run,
        statut_qualite=statut_qualite,
        type_ouvrage=None,
        db=db,
    )

    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return Response(
        content=payload,
        media_type="application/geo+json",
        headers={
            "Content-Disposition": f'attachment; filename="fichier_{id_fichier}.geojson"'
        },
    )