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
from sqlalchemy.orm import Session, selectinload, aliased

from app.auth import require_api_key
from app.db import get_db
from app.deps import OuvrageFilters
from app.models import (
    CGPE,
    Feuille,
    Fichier,
    LigneIngeree,
    Localite,
    Ouvrage,
    OuvrageProjet,
    ProjetFinancement,
    RefGeoAdmin,
    Source,
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
    """Convertit une ligne ingérée en Feature GeoJSON (mode Fichier/Run/Feuille)."""
    geom = _parse_geojson_geom(geojson_str)
    if geom is None:
        return None

    # Type d'ouvrage déduit du nom de feuille (prioritaire) ou brut
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
            # Données brutes pour le popup
            "donnees_brutes": ligne.donnees_brutes or {},
            # Pas de details structurés en mode brut
            "details": None,
        },
    }


def _ouvrage_to_feature(
    o: Ouvrage,
    geojson_str: str | None,
    localite_metadata: dict | None = None,
    cgpe_metadata: dict | None = None,
) -> dict[str, Any] | None:
    """Convertit un ouvrage en Feature GeoJSON (mode Tous)."""
    geom = _parse_geojson_geom(geojson_str)
    if geom is None:
        return None

    details = {
        "ouvrage": o.metadata_ or {},
        "localite": localite_metadata or {},
        "cgpe": cgpe_metadata or {},
    }

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
            "details": details,
        },
    }


# =====================================================================
# MODE FICHIER / RUN / FEUILLE
# =====================================================================
def _build_feature_collection_fichier(
    id_fichier: int,
    id_feuille: int | None,
    id_run: int | None,
    statut_qualite: str | None,
    type_ouvrage: str | None,
    db: Session,
) -> dict[str, Any]:
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
            "meta": {"id_fichier": id_fichier, "nom_fichier": fichier.nom_fichier_original, "count": 0},
        }

    feuilles_ids = [f.id_feuille for f in feuilles]
    feuille_noms = {f.id_feuille: f.nom_feuille for f in feuilles}

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
    features = []
    for row in rows:
        ligne, geojson_str = row[0], row[1]
        nom_feuille = feuille_noms.get(ligne.id_feuille)
        feature = _ligne_to_feature(ligne, fichier, geojson_str, nom_feuille)
        if feature:
            features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {"id_fichier": id_fichier, "nom_fichier": fichier.nom_fichier_original, "count": len(features)},
    }


# =====================================================================
# MODE TOUS (OUVRAGES CONSOLIDÉS)
# =====================================================================
def _build_feature_collection_tous(
    filters: OuvrageFilters,
    db: Session,
) -> dict[str, Any]:
    # Chargement des ouvrages avec leurs relations
    stmt = (
        select(
            Ouvrage,
            func.ST_AsGeoJSON(literal_column("ouvrage.geom")).label("geojson"),
        )
        .options(
            selectinload(Ouvrage.type_ouvrage),
            selectinload(Ouvrage.localite).selectinload(Localite.ref_geo),
            selectinload(Ouvrage.cgpes),
        )
    )

    # Filtres métier
    if filters.type_ouvrage:
        stmt = stmt.join(TypeOuvrage).where(TypeOuvrage.code == filters.type_ouvrage)
    if filters.etat:
        stmt = stmt.where(Ouvrage.etat == filters.etat)
    if filters.annee_min is not None:
        stmt = stmt.where(Ouvrage.annee_realisation >= filters.annee_min)
    if filters.annee_max is not None:
        stmt = stmt.where(Ouvrage.annee_realisation <= filters.annee_max)

    # Filtres géographiques
    if filters.region or filters.departement or filters.sous_prefecture or filters.localite:
        stmt = stmt.join(Ouvrage.localite)

        # On utilise une référence à ref_geo_admin et ses parents
        from sqlalchemy.orm import aliased
        rg_loc = aliased(RefGeoAdmin) # Niveau localité
        rg_sp = aliased(RefGeoAdmin)  # Niveau sous-prefecture
        rg_dep = aliased(RefGeoAdmin) # Niveau departement
        rg_reg = aliased(RefGeoAdmin) # Niveau region

        stmt = stmt.join(rg_loc, Localite.id_geo == rg_loc.id_geo)
        stmt = stmt.outerjoin(rg_sp, rg_loc.parent_id == rg_sp.id_geo)
        stmt = stmt.outerjoin(rg_dep, rg_sp.parent_id == rg_dep.id_geo)
        stmt = stmt.outerjoin(rg_reg, rg_dep.parent_id == rg_reg.id_geo)

        if filters.region:
            stmt = stmt.where(rg_reg.nom == filters.region)
        if filters.departement:
            stmt = stmt.where(rg_dep.nom == filters.departement)
        if filters.sous_prefecture:
            stmt = stmt.where(rg_sp.nom == filters.sous_prefecture)

        if filters.localite:
            stmt = stmt.where(Localite.nom_usage.ilike(f"%{filters.localite}%"))

    # Filtre bailleur (via ouvrage_projet -> projet_financement -> source)
    if getattr(filters, "bailleur", None):
        stmt = stmt.join(OuvrageProjet).join(ProjetFinancement).join(Source).where(Source.nom == filters.bailleur)

    rows = db.execute(stmt).all()
    features = []
    for row in rows:
        o, geojson_str = row[0], row[1]
        # Extrait les métadonnées de localité (via sa ref_geo)
        loc_meta = o.localite.metadata_ if o.localite else {}
        # Extrait les métadonnées du premier CGPE (s'il existe)
        cgpe_meta = o.cgpes[0].metadata_ if o.cgpes else {}

        feature = _ouvrage_to_feature(o, geojson_str, loc_meta, cgpe_meta)
        if feature:
            features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {"count": len(features)},
    }


# =====================================================================
# ROUTES
# =====================================================================
@router.get(
    "/carto/fichiers/{id_fichier}/points",
    summary="Points d'un fichier, d'un run ou d'une feuille (GeoJSON)",
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


@router.get(
    "/carto/tous/points",
    summary="Tous les ouvrages consolidés (GeoJSON)",
    operation_id="get_tous_points",
)
def points_tous(
    filters: OuvrageFilters = Depends(),
    db: Session = Depends(get_db),
):
    return _build_feature_collection_tous(filters, db)


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
        headers={"Content-Disposition": f'attachment; filename="fichier_{id_fichier}.geojson"'},
    )