"""
Router carto : endpoints GeoJSON pour l'UI cartographique.

Mode Fichier : lit la vue v_points_par_fichier (Bible § 2.2.D).
Mode Tous    : lit ouvrage + v_points_consolides (jointures manuelles).

On utilise ST_AsGeoJSON() côté SQL pour éviter les problèmes de conversion
WKB (les colonnes générées geom ne sont pas déclarées en ORM).
"""
from __future__ import annotations

import json
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import exists, func, literal_column, select, text
from sqlalchemy.orm import Session, selectinload, aliased

from app.auth import require_api_key
from app.db import get_db
from app.deps import OuvrageFilters
from app.models import (
    Fichier,
    Localite,
    Ouvrage,
    OuvrageProjet,
    ProjetFinancement,
    RefGeoAdmin,
    Source,
)

router = APIRouter(
    tags=["Carto"],
    dependencies=[Depends(require_api_key)],
)

# Types autorisés (alignés sur les CHECK SQL / Literal des schémas)
TypeAlimentation = Literal["PMH", "HVA", "PEA", "HV", "AUTRE"]
NatureOuvrage = Literal["puits", "forage", "inconnu"]
RealisationPar = Literal["public", "prive", "inconnu"]
StatutQualite = Literal[
    "ok", "localite_non_resolue", "geom_invalide",
    "type_ouvrage_inconnu", "rejete", "doublon_suspect",
]


# =====================================================================
# Helpers
# =====================================================================
def _parse_geojson_geom(geojson_str: str | None) -> dict[str, Any] | None:
    """Parse une chaîne GeoJSON en dict {type, coordinates}."""
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


def _row_to_feature_fichier(row: Any) -> dict[str, Any] | None:
    """Convertit une ligne de v_points_par_fichier en Feature GeoJSON.

    Les propriétés exposent le BRUT (mode Par fichier), pas le métier consolidé.
    """
    m = row._mapping
    geom = _parse_geojson_geom(m["geojson"])
    if geom is None:
        return None

    return {
        "type": "Feature",
        "id": str(m["id_ligne"]),
        "geometry": geom,
        "properties": {
            "id_ligne": m["id_ligne"],
            "id_fichier": m["id_fichier"],
            "nom_fichier": m["nom_fichier_original"],
            "id_feuille": m["id_feuille"],
            "nom_feuille": m["nom_feuille"],
            "num_ligne_source": m["num_ligne_source"],
            "type_ouvrage_brut": m["type_ouvrage_brut"],
            "etat_ouvrage_brut": m["etat_ouvrage_brut"],
            "annee_projet": m["annee_projet"],
            "bailleur_brut": m["bailleur_brut"],
            "type_financement_brut": m["type_financement_brut"],
            "statut_qualite": m["statut_qualite"],
            "latitude_decimal": m["latitude_decimal"],
            "longitude_decimal": m["longitude_decimal"],
        },
    }


def _row_to_feature_ouvrage(row: Any) -> dict[str, Any] | None:
    """Convertit une ligne (Ouvrage, geojson) en Feature GeoJSON (mode Tous)."""
    o: Ouvrage = row[0]
    geom = _parse_geojson_geom(row[1])
    if geom is None:
        return None

    loc_meta = o.localite.metadata_ if o.localite else {}
    cgpe_meta = o.cgpes[0].metadata_ if o.cgpes else {}

    details = {
        "ouvrage": o.metadata_ or {},
        "localite": loc_meta or {},
        "cgpe": cgpe_meta or {},
        "qualite_eau": o.qualite_eau or {},
    }

    return {
        "type": "Feature",
        "id": str(o.id_ouvrage),
        "geometry": geom,
        "properties": {
            "id_ouvrage": o.id_ouvrage,
            "code_ouvrage": o.code_ouvrage,
            "nature_ouvrage": o.nature_ouvrage,
            "type_alimentation": o.type_alimentation,
            "realisation_par": o.realisation_par,
            "etat": o.etat,
            "annee_realisation": o.annee_realisation,
            "localite": o.localite.nom_usage if o.localite else None,
            "qualite_eau": o.qualite_eau,
            "details": details,
        },
    }


# =====================================================================
# MODE FICHIER (v_points_par_fichier)
# =====================================================================
# Colonnes exposées par la vue, dans l'ordre du SELECT.
_VUE_FICHIER_SELECT = """
    SELECT
        v.id_fichier,
        v.nom_fichier_original,
        v.date_ingestion,
        v.source,
        v.id_feuille,
        v.nom_feuille,
        v.id_ligne,
        v.num_ligne_source,
        v.type_ouvrage_brut,
        v.etat_ouvrage_brut,
        v.annee_projet,
        v.bailleur_brut,
        v.type_financement_brut,
        v.statut_qualite,
        v.latitude_decimal,
        v.longitude_decimal,
        ST_AsGeoJSON(v.geom) AS geojson
    FROM v_points_par_fichier v
    WHERE v.id_fichier = :id_fichier
"""


def _build_feature_collection_fichier(
    id_fichier: int,
    id_feuille: int | None,
    id_run: int | None,
    statut_qualite: StatutQualite | None,
    type_alimentation: TypeAlimentation | None,
    localite: str | None,
    region: str | None,
    departement: str | None,
    sous_prefecture: str | None,
    db: Session,
) -> dict[str, Any]:
    fichier = db.get(Fichier, id_fichier)
    if fichier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fichier {id_fichier} introuvable",
        )

    # Construction dynamique du WHERE (paramétré, pas d'injection).
    where_parts: list[str] = []
    params: dict[str, Any] = {"id_fichier": id_fichier}

    if id_feuille is not None:
        where_parts.append("v.id_feuille = :id_feuille")
        params["id_feuille"] = id_feuille
    if id_run is not None:
        # La vue n'expose pas id_run : on filtre via ligne_ingeree.
        where_parts.append(
            "v.id_ligne IN (SELECT id_ligne FROM ligne_ingeree WHERE id_run = :id_run)"
        )
        params["id_run"] = id_run
    if statut_qualite is not None:
        where_parts.append("v.statut_qualite = :statut_qualite")
        params["statut_qualite"] = statut_qualite
    if type_alimentation is not None:
        # Filtre sur le nom de feuille (seule source d'alimentation en mode brut).
        # Aligné sur _infer_type_alimentation (mais centralisé ici).
        patterns = {
            "PMH": "%PMH%",
            "HVA": "%HVA%",
            "PEA": "%PEA%",
            "HV": "%HV%",
            "AUTRE": None,  # pas de filtre "AUTRE" (tout ce qui ne matche pas)
        }
        pat = patterns[type_alimentation]
        if pat is None:
            # "AUTRE" = tout sauf PMH/HVA/PEA/HV
            where_parts.append(
                "NOT (v.nom_feuille ILIKE '%PMH%' "
                "OR v.nom_feuille ILIKE '%HVA%' "
                "OR v.nom_feuille ILIKE '%PEA%' "
                "OR v.nom_feuille ILIKE '%HV%')"
            )
        else:
            where_parts.append("v.nom_feuille ILIKE :pat_alim")
            params["pat_alim"] = pat

    # Filtres géographiques : la vue n'expose pas id_localite, on joint localite.
    if localite or region or departement or sous_prefecture:
        # On passe par ligne_ingeree → localite → ref_geo_admin.
        where_parts.append(
            "v.id_ligne IN ("
            "  SELECT li.id_ligne FROM ligne_ingeree li "
            "  JOIN localite l ON l.id_localite = li.id_localite "
            "  JOIN ref_geo_admin g_loc ON g_loc.id_geo = l.id_geo "
            "  LEFT JOIN ref_geo_admin g_sp ON g_sp.id_geo = g_loc.parent_id "
            "  LEFT JOIN ref_geo_admin g_dep ON g_dep.id_geo = g_sp.parent_id "
            "  LEFT JOIN ref_geo_admin g_reg ON g_reg.id_geo = g_dep.parent_id "
            "  WHERE 1=1"
            + (" AND g_reg.nom = :region" if region else "")
            + (" AND g_dep.nom = :departement" if departement else "")
            + (" AND g_sp.nom = :sous_prefecture" if sous_prefecture else "")
            + (" AND l.nom_usage ILIKE :localite" if localite else "")
            + ")"
        )
        if region:
            params["region"] = region
        if departement:
            params["departement"] = departement
        if sous_prefecture:
            params["sous_prefecture"] = sous_prefecture
        if localite:
            params["localite"] = f"%{localite}%"

    sql = _VUE_FICHIER_SELECT
    if where_parts:
        sql += " AND " + " AND ".join(where_parts)

    rows = db.execute(text(sql), params).all()
    features = [f for f in (_row_to_feature_fichier(r) for r in rows) if f]

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
# MODE TOUS (ouvrages consolidés)
# =====================================================================
def _build_feature_collection_tous(
    filters: OuvrageFilters,
    db: Session,
) -> dict[str, Any]:
    stmt = (
        select(
            Ouvrage,
            func.ST_AsGeoJSON(literal_column("ouvrage.geom")).label("geojson"),
        )
        .options(
            selectinload(Ouvrage.localite),
            selectinload(Ouvrage.cgpes),
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

    # Filtres géographiques
    if filters.region or filters.departement or filters.sous_prefecture or filters.localite:
        stmt = stmt.join(Ouvrage.localite)

        rg_loc = aliased(RefGeoAdmin)
        rg_sp = aliased(RefGeoAdmin)
        rg_dep = aliased(RefGeoAdmin)
        rg_reg = aliased(RefGeoAdmin)

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

    # Filtre bailleur : EXISTS (pas de join → pas de doublons de features).
    if filters.bailleur:
        stmt = stmt.where(
            exists(
                select(OuvrageProjet.id_ouvrage)
                .join(
                    ProjetFinancement,
                    ProjetFinancement.id_projet == OuvrageProjet.id_projet,
                )
                .join(Source, Source.id_source == ProjetFinancement.id_source_financeur)
                .where(OuvrageProjet.id_ouvrage == Ouvrage.id_ouvrage)
                .where(Source.nom == filters.bailleur)
            )
        )

    rows = db.execute(stmt).all()
    features = [f for f in (_row_to_feature_ouvrage(r) for r in rows) if f]

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
    summary="Points bruts d'un fichier (GeoJSON, mode Par fichier)",
    operation_id="get_points_fichier",
)
def points_fichier(
    id_fichier: int,
    id_feuille: int | None = Query(None),
    id_run: int | None = Query(None),
    statut_qualite: StatutQualite | None = Query(None),
    type_alimentation: TypeAlimentation | None = Query(None),
    localite: str | None = Query(None),
    region: str | None = Query(None),
    departement: str | None = Query(None),
    sous_prefecture: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return _build_feature_collection_fichier(
        id_fichier=id_fichier,
        id_feuille=id_feuille,
        id_run=id_run,
        statut_qualite=statut_qualite,
        type_alimentation=type_alimentation,
        localite=localite,
        region=region,
        departement=departement,
        sous_prefecture=sous_prefecture,
        db=db,
    )


@router.get(
    "/carto/tous/points",
    summary="Tous les ouvrages consolidés (GeoJSON, mode Tous)",
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
    statut_qualite: StatutQualite | None = Query(None),
    type_alimentation: TypeAlimentation | None = Query(None),
    localite: str | None = Query(None),
    region: str | None = Query(None),
    departement: str | None = Query(None),
    sous_prefecture: str | None = Query(None),
    db: Session = Depends(get_db),
):
    data = _build_feature_collection_fichier(
        id_fichier=id_fichier,
        id_feuille=id_feuille,
        id_run=id_run,
        statut_qualite=statut_qualite,
        type_alimentation=type_alimentation,
        localite=localite,
        region=region,
        departement=departement,
        sous_prefecture=sous_prefecture,
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
