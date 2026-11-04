"""
Router carto : endpoints GeoJSON pour l'UI cartographique.

On utilise ST_AsGeoJSON() côté SQL pour éviter les problèmes de conversion
WKB (les colonnes générées geom ne sont pas déclarées en ORM).
"""
from __future__ import annotations

import json
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import func, literal_column, select
from sqlalchemy.orm import Session, selectinload

from app.auth import require_api_key
from app.db import get_db
from app.deps import OuvrageFilters
from app.models import (
    Feuille,
    Fichier,
    LigneIngeree,
    Localite,
    Ouvrage,
    RefGeoAdmin,
    TypeOuvrage,
)

router = APIRouter(
    tags=["Carto"],
    dependencies=[Depends(require_api_key)],
)


# =====================================================================
# Helpers GeoJSON
# =====================================================================
def _parse_geojson_geom(geojson_str: str | None) -> dict[str, Any] | None:
    """Parse une chaîne GeoJSON (ST_AsGeoJSON) en dict {type, coordinates}."""
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


def _ligne_to_feature(
    ligne: LigneIngeree,
    fichier: Fichier,
    geojson_str: str | None,
    nom_feuille: str | None,
) -> dict[str, Any] | None:
    """Convertit une ligne ingérée en Feature GeoJSON."""
    geom = _parse_geojson_geom(geojson_str)
    if geom is None:
        return None

    # Détermine le type d'ouvrage : nom de feuille prioritaire, sinon type brut
    type_ouvrage = ligne.type_ouvrage_brut
    nom_upper = (nom_feuille or "").upper()
    if "PMH" in nom_upper:
        type_ouvrage = "PMH"
    elif "HVA" in nom_upper:
        type_ouvrage = "HVA"
    elif "PEA" in nom_upper:
        type_ouvrage = "PEA"
    elif "HV" in nom_upper:
        type_ouvrage = "HV"

    return {
        "type": "Feature",
        "id": str(ligne.id_ligne),
        "geometry": geom,
        "properties": {
            "id_ligne": ligne.id_ligne,
            "id_fichier": fichier.id_fichier,
            "nom_fichier": fichier.nom_fichier_original,
            "type_ouvrage": type_ouvrage,
            "statut_qualite": ligne.statut_qualite,
            "localite": ligne.localite_brute,
        },
    }


def _ouvrage_to_feature(
    o: Ouvrage,
    geojson_str: str | None,
) -> dict[str, Any] | None:
    """Convertit un ouvrage en Feature GeoJSON."""
    geom = _parse_geojson_geom(geojson_str)
    if geom is None:
        return None

    return {
        "type": "Feature",
        "id": str(o.id_ouvrage),
        "geometry": geom,
        "properties": {
            "id_ouvrage": o.id_ouvrage,
            "code_ouvrage": o.code_ouvrage,
            "type_ouvrage": o.type_ouvrage.code if o.type_ouvrage else None,
            "etat": o.etat,
            "annee_realisation": o.annee_realisation,
            "localite": o.localite.nom_usage if o.localite else None,
            "metadata": o.metadata_ or {},
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
    """Logique métier partagée par points_fichier et telecharger_geojson_fichier."""
    fichier = db.get(Fichier, id_fichier)
    if fichier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fichier {id_fichier} introuvable",
        )

    feuilles = db.scalars(
        select(Feuille).where(Feuille.id_fichier == id_fichier)
    ).all()

    if not feuilles:
        return {
            "type": "FeatureCollection",
            "features": [],
            "meta": {
                "id_fichier": id_fichier,
                "nom_fichier": fichier.nom_fichier_original,
                "count": 0,
            },
        }

    feuilles_ids = [f.id_feuille for f in feuilles]
    feuille_noms: dict[int, str] = {f.id_feuille: f.nom_feuille for f in feuilles}

    # ST_AsGeoJSON : convertit la géométrie en chaîne JSON directement en SQL
    stmt = select(
        LigneIngeree,
        func.ST_AsGeoJSON(literal_column("ligne_ingeree.geom")).label("geojson"),
    ).where(LigneIngeree.id_feuille.in_(feuilles_ids))

    if id_feuille is not None:
        stmt = stmt.where(LigneIngeree.id_feuille == id_feuille)
    if id_run is not None:
        stmt = stmt.where(LigneIngeree.id_run == id_run)
    if statut_qualite is not None:
        stmt = stmt.where(LigneIngeree.statut_qualite == statut_qualite)
    if type_ouvrage is not None:
        stmt = stmt.where(LigneIngeree.type_ouvrage_brut == type_ouvrage)

    rows = db.execute(stmt).all()
    features: list[dict[str, Any]] = []
    for row in rows:
        ligne = row[0]
        geojson_str = row[1]
        nom_feuille = feuille_noms.get(ligne.id_feuille)
        feature = _ligne_to_feature(ligne, fichier, geojson_str, nom_feuille)
        if feature is not None:
            features.append(feature)

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
# POINTS D'UN FICHIER
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
    stmt = select(
        Ouvrage,
        func.ST_AsGeoJSON(literal_column("ouvrage.geom")).label("geojson"),
    ).options(
        selectinload(Ouvrage.type_ouvrage),
        selectinload(Ouvrage.localite),
    )

    # Filtre par type d'ouvrage
    if filters.type_ouvrage:
        stmt = stmt.join(TypeOuvrage).where(TypeOuvrage.code == filters.type_ouvrage)

    # Filtre par état
    if filters.etat:
        stmt = stmt.where(Ouvrage.etat == filters.etat)

    # Filtre par année
    if filters.annee_min is not None:
        stmt = stmt.where(Ouvrage.annee_realisation >= filters.annee_min)
    if filters.annee_max is not None:
        stmt = stmt.where(Ouvrage.annee_realisation <= filters.annee_max)

    # Filtres géographiques (district, region, departement, sous_prefecture)
    # → jointure sur localite → ref_geo_admin
    if filters.district or filters.region or filters.departement or filters.sous_prefecture:
        stmt = stmt.join(Ouvrage.localite).join(Localite.ref_geo)

        if filters.district:
            stmt = stmt.where(RefGeoAdmin.niveau == "district", RefGeoAdmin.nom == filters.district)
        if filters.region:
            stmt = stmt.where(RefGeoAdmin.niveau == "region", RefGeoAdmin.nom == filters.region)
        if filters.departement:
            stmt = stmt.where(RefGeoAdmin.niveau == "departement", RefGeoAdmin.nom == filters.departement)
        if filters.sous_prefecture:
            stmt = stmt.where(RefGeoAdmin.niveau == "sous_prefecture", RefGeoAdmin.nom == filters.sous_prefecture)

    rows = db.execute(stmt).all()
    features: list[dict[str, Any]] = []
    for row in rows:
        o = row[0]
        geojson_str = row[1]
        feature = _ouvrage_to_feature(o, geojson_str)
        if feature is not None:
            features.append(feature)

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