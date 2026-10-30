"""
Import des localités depuis la feuille 'Localités' d'un fichier Excel.

Stratégie :
1. Lit la feuille 'Localités'
2. Pour chaque ligne, extrait la hiérarchie administrative :
   - Région (Q1.2. Région)
   - Département (Q1.3. Département)
   - Sous-préfecture (Q1.4. Commune/Sous-préfecture)
   - Localité (Q1.5. Localité/Campement)
3. Crée la hiérarchie ref_geo_admin (district → région → département → sous-préfecture → localité)
   - District : on le déduit ou on le laisse NULL (à compléter manuellement)
4. Crée une localite rattachée au nœud 'localite'
5. Remplit metadata (population, etc.)
"""
from __future__ import annotations

import logging
from typing import Any

import openpyxl
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Localite, RefGeoAdmin

logger = logging.getLogger("dhr.import_localites")


# =====================================================================
# Helpers
# =====================================================================
def _normaliser(texte: str | None) -> str:
    """Normalise un texte (minuscules, sans accents, espaces compactés)."""
    if texte is None:
        return ""
    import re
    import unicodedata
    texte = str(texte).strip().lower()
    texte = "".join(
        c for c in unicodedata.normalize("NFD", texte)
        if unicodedata.category(c) != "Mn"
    )
    texte = re.sub(r"[\s\-_]+", " ", texte).strip()
    return texte

def _get_or_create_district_defaut(db: Session) -> RefGeoAdmin:
    """Récupère ou crée un district par défaut pour les régions sans district connu."""
    existing = db.scalar(
        select(RefGeoAdmin).where(
            RefGeoAdmin.niveau == "district",
            RefGeoAdmin.nom == "DISTRICT_NON_DEFINI",
        )
    )
    if existing is not None:
        return existing

    district = RefGeoAdmin(
        niveau="district",
        nom="DISTRICT_NON_DEFINI",
        parent_id=None,
    )
    db.add(district)
    db.flush()
    return district

def _get_or_create_ref_geo(
    db: Session,
    niveau: str,
    nom: str,
    parent_id: int | None,
    type_localite: str | None = None,
) -> RefGeoAdmin:
    """
    Récupère ou crée un nœud ref_geo_admin.
    """
    nom_clean = str(nom).strip() if nom else ""
    if not nom_clean:
        raise ValueError(f"Nom vide pour le niveau {niveau}")

    # Cherche par nom + parent + niveau
    existing = db.scalar(
        select(RefGeoAdmin).where(
            RefGeoAdmin.niveau == niveau,
            RefGeoAdmin.nom == nom_clean,
            RefGeoAdmin.parent_id == parent_id,
        )
    )
    if existing is not None:
        return existing

    # Crée
    node = RefGeoAdmin(
        niveau=niveau,
        nom=nom_clean,
        parent_id=parent_id,
        type_localite=type_localite if niveau == "localite" else None,
    )
    db.add(node)
    db.flush()
    return node


def _get_or_create_localite(
    db: Session,
    id_geo: int,
    nom_usage: str,
    latitude: float | None,
    longitude: float | None,
    metadata: dict[str, Any] | None = None,
) -> Localite:
    """
    Récupère ou crée une localité métier.
    """
    nom_clean = str(nom_usage).strip() if nom_usage else ""
    if not nom_clean:
        raise ValueError("Nom de localité vide")

    # Cherche par nom + id_geo
    existing = db.scalar(
        select(Localite).where(
            Localite.id_geo == id_geo,
            Localite.nom_usage == nom_clean,
        )
    )
    if existing is not None:
        return existing

    localite = Localite(
        id_geo=id_geo,
        nom_usage=nom_clean,
        latitude_centre=latitude,
        longitude_centre=longitude,
        metadata_=metadata or {},
    )
    db.add(localite)
    db.flush()
    return localite


# =====================================================================
# Import principal
# =====================================================================
def importer_localites(
    db: Session,
    chemin_fichier: str,
    nom_feuille: str = "Localités",
    header_row: int = 1,
) -> dict[str, Any]:
    """
    Importe les localités depuis la feuille spécifiée.
    Retourne les stats.
    """
    from pathlib import Path
    if not Path(chemin_fichier).exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin_fichier}")

    wb = openpyxl.load_workbook(chemin_fichier, read_only=True, data_only=True)
    try:
        if nom_feuille not in wb.sheetnames:
            raise ValueError(f"Feuille '{nom_feuille}' introuvable dans {chemin_fichier}")
        ws = wb[nom_feuille]

        # Lit les entêtes
        entetes: list[str] = []
        for cell in next(ws.iter_rows(min_row=header_row, max_row=header_row, values_only=False)):
            entetes.append(str(cell.value) if cell.value is not None else "")

        # Détecte les colonnes utiles
        idx_region = idx_departement = idx_sous_pref = idx_localite = None
        idx_type_localite = idx_lat = idx_lon = idx_population = None

        for i, h in enumerate(entetes):
            h_norm = _normaliser(h)
            if not h_norm:
                continue
            if "q1.2" in h_norm or h_norm == "region":
                idx_region = i
            elif "q1.3" in h_norm or h_norm == "departement":
                idx_departement = i
            elif "q1.4" in h_norm or "commune" in h_norm:
                idx_sous_pref = i
            elif "q1.5" in h_norm or h_norm == "localite":
                idx_localite = i
            elif "q1.6" in h_norm or "nom du campement" in h_norm:
                if idx_localite is None:
                    idx_localite = i
            elif h_norm.startswith("localite_ou_campement"):
                idx_type_localite = i
            elif h_norm == "latitude":
                idx_lat = i
            elif h_norm == "longitude":
                idx_lon = i
            elif "q1.7" in h_norm or "population" in h_norm:
                idx_population = i

        logger.info(
            "Colonnes détectées : region=%s, dept=%s, sous_pref=%s, localite=%s, type=%s, lat=%s, lon=%s, pop=%s",
            idx_region, idx_departement, idx_sous_pref, idx_localite,
            idx_type_localite, idx_lat, idx_lon, idx_population,
        )

        if idx_localite is None or idx_sous_pref is None:
            raise ValueError("Colonnes 'Localité' ou 'Sous-préfecture' introuvables")

        # Compteurs
        nb_lignes = 0
        nb_localites_creees = 0
        nb_localites_existantes = 0
        nb_erreurs = 0

        # Itère sur toutes les lignes (une seule fois)
        for row_idx, row in enumerate(
            ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True),
            start=1,
        ):
            if row_idx <= header_row:
                continue

            # Ignore les lignes vides
            if all(v is None or str(v).strip() == "" for v in row):
                continue

            nb_lignes += 1

            try:
                # Extrait les valeurs
                region = row[idx_region] if idx_region is not None and idx_region < len(row) else None
                departement = row[idx_departement] if idx_departement is not None and idx_departement < len(row) else None
                sous_pref = row[idx_sous_pref] if idx_sous_pref < len(row) else None
                localite = row[idx_localite] if idx_localite < len(row) else None
                type_localite = row[idx_type_localite] if idx_type_localite is not None and idx_type_localite < len(row) else None
                lat = row[idx_lat] if idx_lat is not None and idx_lat < len(row) else None
                lon = row[idx_lon] if idx_lon is not None and idx_lon < len(row) else None
                population = row[idx_population] if idx_population is not None and idx_population < len(row) else None

                if not sous_pref or not localite:
                    nb_erreurs += 1
                    continue

                # Crée la hiérarchie : district par défaut → région → département → sous-préfecture
                district_defaut = _get_or_create_district_defaut(db)

                region_node = None
                if region:
                    region_node = _get_or_create_ref_geo(
                        db, "region", str(region).strip(),
                        parent_id=district_defaut.id_geo,
                    )

                dept_node = None
                if departement:
                    dept_node = _get_or_create_ref_geo(
                        db, "departement", str(departement).strip(),
                        parent_id=region_node.id_geo if region_node else district_defaut.id_geo,
                    )

                sous_pref_node = _get_or_create_ref_geo(
                    db, "sous_prefecture", str(sous_pref).strip(),
                    parent_id=dept_node.id_geo if dept_node else (region_node.id_geo if region_node else district_defaut.id_geo),
                )

                # Type de localité (village/campement)
                type_loc = None
                if type_localite:
                    tl_norm = _normaliser(str(type_localite))
                    if "camp" in tl_norm:
                        type_loc = "campement"
                    elif "vill" in tl_norm or "localit" in tl_norm:
                        type_loc = "village"
                    else:
                        type_loc = "autre"

                localite_node = _get_or_create_ref_geo(
                    db, "localite", str(localite).strip(),
                    parent_id=sous_pref_node.id_geo,
                    type_localite=type_loc,
                )

                # Crée la localité métier
                lat_float = None
                lon_float = None
                try:
                    if lat is not None:
                        lat_float = float(str(lat).replace(",", "."))
                    if lon is not None:
                        lon_float = float(str(lon).replace(",", "."))
                except (ValueError, TypeError):
                    pass

                metadata = {}
                if population is not None:
                    try:
                        metadata["population"] = int(float(str(population)))
                    except (ValueError, TypeError):
                        metadata["population_brute"] = str(population)

                existing = db.scalar(
                    select(Localite).where(
                        Localite.id_geo == localite_node.id_geo,
                        Localite.nom_usage == str(localite).strip(),
                    )
                )
                if existing is not None:
                    nb_localites_existantes += 1
                else:
                    _get_or_create_localite(
                        db,
                        id_geo=localite_node.id_geo,
                        nom_usage=str(localite).strip(),
                        latitude=lat_float,
                        longitude=lon_float,
                        metadata=metadata,
                    )
                    nb_localites_creees += 1

            except Exception as e:
                logger.error("Erreur ligne %s : %s", row_idx, e)
                nb_erreurs += 1

        db.flush()

        return {
            "nb_lignes": nb_lignes,
            "nb_localites_creees": nb_localites_creees,
            "nb_localites_existantes": nb_localites_existantes,
            "nb_erreurs": nb_erreurs,
        }

    finally:
        wb.close()