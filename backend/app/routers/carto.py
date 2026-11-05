"""
Router carto : endpoints GeoJSON pour l'UI cartographique.

On utilise ST_AsGeoJSON() côté SQL pour éviter les problèmes de conversion
WKB (les colonnes générées geom ne sont pas déclarées en ORM).
"""
from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import func, literal_column, or_, select
from sqlalchemy.orm import Session, selectinload, aliased

from app.auth import require_api_key
from app.db import get_db
from app.deps import OuvrageFilters
from app.models import (
    Feuille,
    Fichier,
    LigneIngeree,
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


# =====================================================================
# Helpers
# =====================================================================
def _normaliser(texte: str | None) -> str:
    """Miroir de consolidation._normaliser — dupliqué localement pour ne pas
    coupler carto.py au service de consolidation."""
    if texte is None:
        return ""
    texte = str(texte).strip().lower()
    texte = "".join(
        c for c in unicodedata.normalize("NFD", texte)
        if unicodedata.category(c) != "Mn"
    )
    texte = re.sub(r"[\s\-_]+", " ", texte).strip()
    return texte


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


def _infer_type_alimentation(nom_feuille: str | None) -> str:
    """Déduit le type d'alimentation du nom de feuille.
    Doit rester cohérent avec consolidation._map_alimentation
    (mais ici, pas de fallback sur type_ouvrage_brut : on n'a que la feuille)."""
    nom_upper = (nom_feuille or "").upper()
    if "PMH" in nom_upper:
        return "PMH"
    if "HVA" in nom_upper:
        return "HVA"
    if "PEA" in nom_upper:
        return "PEA"
    if "HV" in nom_upper:
        return "HV"
    return "AUTRE"


def _infer_nature_et_realisation(
    donnees_brutes: dict[str, Any] | None,
) -> tuple[str, str]:
    """Extrait nature_ouvrage et realisation_par depuis les données brutes.
    Aligné sur consolidation._map_nature / _map_realisation."""
    nature_ouvrage = "inconnu"
    realisation_par = "inconnu"
    if not donnees_brutes:
        return nature_ouvrage, realisation_par

    for k, v in donnees_brutes.items():
        if not k or not v:
            continue
        k_norm = _normaliser(k)
        v_norm = _normaliser(str(v))

        # Nature : clé "type d'ouvrage"
        if "type d ouvrage" in k_norm or "type d'ouvrage" in k_norm:
            if "forage" in v_norm:
                nature_ouvrage = "forage"
            elif "puits" in v_norm:
                nature_ouvrage = "puits"

        # Réalisation : clé "type de forage"
        # Note : deux `if` (pas `elif`) pour qu'une même clé puisse
        # renseigner les deux si elle contient les deux expressions.
        if "type de forage" in k_norm:
            if "public" in v_norm or "administratif" in v_norm:
                realisation_par = "public"
            elif "prive" in v_norm:
                realisation_par = "prive"

    return nature_ouvrage, realisation_par


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

    type_alimentation = _infer_type_alimentation(nom_feuille)
    nature_ouvrage, realisation_par = _infer_nature_et_realisation(
        ligne.donnees_brutes
    )

    return {
        "type": "Feature",
        "id": str(ligne.id_ligne),
        "geometry": geom,
        "properties": {
            "id_ligne": ligne.id_ligne,
            "id_fichier": fichier.id_fichier,
            "nom_fichier": fichier.nom_fichier_original,
            "type_alimentation": type_alimentation,
            "nature_ouvrage": nature_ouvrage,
            "realisation_par": realisation_par,
            "statut_qualite": ligne.statut_qualite,
            "localite": ligne.localite_brute,
            "donnees_brutes": ligne.donnees_brutes or {},
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
            "nature_ouvrage": o.nature_ouvrage,
            "type_alimentation": o.type_alimentation,
            "realisation_par": o.realisation_par,
            "etat": o.etat,
            "annee_realisation": o.annee_realisation,
            "localite": o.localite.nom_usage if o.localite else None,
            "details": details,
        },
    }


# =====================================================================
# Helpers de filtres JSONB (mode Fichier)
# =====================================================================
def _contains_json_value(column_expr, value: str):
    """Filtre 'donnees_brutes contient cette valeur textuelle'.

    Note : utilise `::text` + contains → pas indexable via l'index GIN
    JSONB. Acceptable pour le MVP (faible volumétrie). Pour une V2, passer
    à `jsonb_path_exists` ou stocker des champs normalisés dédiés.
    """
    return func.lower(literal_column(f"{column_expr}::text")).contains(
        f'"{value}"'
    )


# =====================================================================
# MODE FICHIER / RUN / FEUILLE
# =====================================================================
def _build_feature_collection_fichier(
    id_fichier: int,
    id_feuille: int | None,
    id_run: int | None,
    statut_qualite: str | None,
    type_alimentation: str | None,
    nature_ouvrage: str | None,
    realisation_par: str | None,
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

    # Filtre type_alimentation : on filtre sur le NOM DE FEUILLE (ce qui est
    # utilisé pour déduire l'alimentation dans _ligne_to_feature).
    # Avant : on filtrait sur type_ouvrage_brut — incohérent avec l'affichage.
    if type_alimentation is not None:
        matching_feuille_ids = [
            f.id_feuille
            for f in feuilles
            if _infer_type_alimentation(f.nom_feuille) == type_alimentation
        ]
        if not matching_feuille_ids:
            # Aucune feuille ne matche → résultat vide, pas la peine d'aller plus loin
            return {
                "type": "FeatureCollection",
                "features": [],
                "meta": {
                    "id_fichier": id_fichier,
                    "nom_fichier": fichier.nom_fichier_original,
                    "count": 0,
                },
            }
        stmt = stmt.where(LigneIngeree.id_feuille.in_(matching_feuille_ids))

    # Filtres nature / réalisation : recherche textuelle dans donnees_brutes.
    # Limitation connue : scan complet, faux positifs possibles. Documenté.
    if nature_ouvrage:
        if nature_ouvrage == "forage":
            stmt = stmt.where(_contains_json_value("ligne_ingeree.donnees_brutes", "forage"))
        elif nature_ouvrage == "puits":
            stmt = stmt.where(_contains_json_value("ligne_ingeree.donnees_brutes", "puits"))

    if realisation_par:
        if realisation_par == "public":
            stmt = stmt.where(
                or_(
                    _contains_json_value("ligne_ingeree.donnees_brutes", "public"),
                    _contains_json_value("ligne_ingeree.donnees_brutes", "administratif"),
                )
            )
        elif realisation_par == "prive":
            stmt = stmt.where(_contains_json_value("ligne_ingeree.donnees_brutes", "prive"))

    # Filtres géographiques (par localité / région / département / sous-préfecture)
    # Note : en mode Fichier, on filtre les lignes ingérées qui ont été
    # rapprochées (id_localite rempli). Les lignes non rapprochées sont exclues
    # dès qu'un filtre géo est actif — comportement attendu.
    if localite or region or departement or sous_prefecture:
        stmt = stmt.join(
            Localite, Localite.id_localite == LigneIngeree.id_localite
        )
        rg_loc = aliased(RefGeoAdmin)
        rg_sp = aliased(RefGeoAdmin)
        rg_dep = aliased(RefGeoAdmin)
        rg_reg = aliased(RefGeoAdmin)
        stmt = stmt.join(rg_loc, Localite.id_geo == rg_loc.id_geo)
        stmt = stmt.outerjoin(rg_sp, rg_loc.parent_id == rg_sp.id_geo)
        stmt = stmt.outerjoin(rg_dep, rg_sp.parent_id == rg_dep.id_geo)
        stmt = stmt.outerjoin(rg_reg, rg_dep.parent_id == rg_reg.id_geo)

        if region:
            stmt = stmt.where(rg_reg.nom == region)
        if departement:
            stmt = stmt.where(rg_dep.nom == departement)
        if sous_prefecture:
            stmt = stmt.where(rg_sp.nom == sous_prefecture)
        if localite:
            stmt = stmt.where(Localite.nom_usage.ilike(f"%{localite}%"))

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
        "meta": {
            "id_fichier": id_fichier,
            "nom_fichier": fichier.nom_fichier_original,
            "count": len(features),
        },
    }


# =====================================================================
# MODE TOUS (OUVRAGES CONSOLIDÉS)
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
            selectinload(Ouvrage.localite).selectinload(Localite.ref_geo),
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

    # Filtre bailleur : inner join volontaire — si on filtre par bailleur,
    # on ne veut que les ouvrages effectivement financés par lui.
    if getattr(filters, "bailleur", None):
        stmt = (
            stmt.join(OuvrageProjet)
            .join(ProjetFinancement)
            .join(Source)
            .where(Source.nom == filters.bailleur)
        )

    rows = db.execute(stmt).all()
    features = []
    for row in rows:
        o, geojson_str = row[0], row[1]
        loc_meta = o.localite.metadata_ if o.localite else {}
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
    type_alimentation: str | None = Query(None),
    nature_ouvrage: str | None = Query(None),
    realisation_par: str | None = Query(None),
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
        nature_ouvrage=nature_ouvrage,
        realisation_par=realisation_par,
        localite=localite,
        region=region,
        departement=departement,
        sous_prefecture=sous_prefecture,
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
    type_alimentation: str | None = Query(None),
    nature_ouvrage: str | None = Query(None),
    realisation_par: str | None = Query(None),
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
        nature_ouvrage=nature_ouvrage,
        realisation_par=realisation_par,
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