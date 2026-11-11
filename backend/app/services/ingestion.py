"""
Service d'ingestion : parsing des fichiers Excel multi-feuilles.

Étapes :
1. detecter_feuilles()      → liste les feuilles + nb lignes estimé
2. _detecter_header_row()   → détecte la ligne d'entête (auto ou manuel)
3. _analyser_entetes()      → détecte les colonnes (regex)
4. _extraire_lignes()       → extrait et normalise chaque ligne
5. ingerer_feuille()        → insère dans ligne_ingeree
6. ingerer_fichier()        → orchestre sur toutes les feuilles

Modes : complet / echantillon / plage

IMPORTANT (Bible § 3.2.1) :
- L'ingestion NE met PAS à jour `fichier.statut` (c'est `run.py` qui le fait
  en fin de pipeline, cf. décision A3).
- Les lignes de total/sous-total sont détectées (mots-clés) et NE sont PAS
  stockées (statut `rejete`). Elles sont comptées dans `fichier.nb_lignes_total`
  via `nb_lignes_stockees + nb_lignes_rejetees` (cf. décision C4).
- Les lignes entièrement vides sont ignorées (ni stockées, ni comptées).
"""
from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import openpyxl
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Feuille, Fichier, IngestionRun, LigneIngeree
from app.services.coordonnees import parser_coordonnees
from app.services.patterns import COLUMN_PATTERNS

logger = logging.getLogger("dhr.ingestion")


# =====================================================================
# Helpers
# =====================================================================
def _normaliser(texte: str | None) -> str:
    """Normalise un texte (minuscules, sans accents, espaces compactés)."""
    if texte is None:
        return ""
    texte = str(texte).strip().lower()
    texte = "".join(
        c for c in unicodedata.normalize("NFD", texte)
        if unicodedata.category(c) != "Mn"
    )
    texte = re.sub(r"[\s\-_]+", " ", texte).strip()
    return texte


def _hash_fichier(chemin: str | Path) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _to_int(val: Any) -> int | None:
    if val is None or val == "":
        return None
    try:
        return int(float(str(val).replace(",", ".").strip()))
    except (ValueError, TypeError):
        return None


def _to_bool(val: Any) -> bool | None:
    if val is None or val == "":
        return None
    s = _normaliser(str(val))
    if s in ("oui", "yes", "true", "1", "vrai"):
        return True
    if s in ("non", "no", "false", "0", "faux"):
        return False
    return None


def _to_float(s: str) -> float | None:
    """Convertit une chaîne en float, gère la virgule. Retourne None si invalide."""
    try:
        return float(s.replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None


def _serialiser_valeur(val: Any) -> Any:
    from datetime import date, datetime, time
    if val is None:
        return None
    if isinstance(val, datetime | date | time):
        return val.isoformat()
    if isinstance(val, int | float | str | bool):
        return val
    return str(val)


# =====================================================================
# Détection des rejets (B5)
# =====================================================================
# Mots-clés (insensible casse/accents) qui signalent une ligne de total
# ou sous-total. Ces lignes ne sont PAS stockées (statut `rejete`).
REJET_MOTS_CLES: tuple[str, ...] = ("total", "sous-total", "somme", "cumul")


def _est_ligne_rejetee(row: tuple[Any, ...]) -> bool:
    """
    Retourne True si la ligne contient un mot-clé de rejet (total, sous-total...).
    La détection se fait sur les cellules texte uniquement.
    """
    for val in row:
        if val is None:
            continue
        s = _normaliser(str(val))
        if not s:
            continue
        for mot in REJET_MOTS_CLES:
            if mot in s:
                return True
    return False


def _est_ligne_vide(row: tuple[Any, ...]) -> bool:
    """Retourne True si toutes les cellules sont None ou ''."""
    return all(v is None or str(v).strip() == "" for v in row)


# =====================================================================
# 1. Détection des feuilles
# =====================================================================
@dataclass
class FeuilleInfo:
    index: int
    nom: str
    nb_lignes: int
    nb_colonnes: int
    header_row: int = 1
    entetes: list[str] = field(default_factory=list)


def _detecter_header_row(ws, max_scan: int = 30) -> int:
    """
    Détecte la ligne d'entête :
    - Cherche la première ligne avec >= 5 cellules non vides
    - Ignore les lignes de séparateurs (tirets/underscores/égal)
    - Ignore les lignes de titre (1-2 cellules non vides)
    - Score basé sur le nombre de colonnes uniques
    """
    best_row = 1
    best_score = 0

    for row_idx in range(1, min(max_scan + 1, (ws.max_row or 1) + 1)):
        # row = list(ws.iter_rows(min_row=row_idx, max_row=row_idx, values_only=True))[0]
        row = next(ws.iter_rows(min_row=row_idx, max_row=row_idx, values_only=True))
        non_vides = [str(v).strip() for v in row if v is not None and str(v).strip() != ""]

        if len(non_vides) < 5:
            continue
        if all(re.fullmatch(r"[-_=*]+", v) for v in non_vides):
            continue

        uniques = len(set(non_vides))
        if uniques > best_score:
            best_score = uniques
            best_row = row_idx
        if uniques >= 10:
            return row_idx

    return best_row


def detecter_feuilles(
    chemin: str | Path,
    header_row_force: int | None = None,
) -> list[FeuilleInfo]:
    """Ouvre un fichier Excel et liste ses feuilles."""
    try:
        wb = openpyxl.load_workbook(chemin, read_only=True, data_only=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible d'ouvrir le fichier Excel : {e}",
        ) from e
    try:
        feuilles: list[FeuilleInfo] = []
        for idx, nom in enumerate(wb.sheetnames, start=1):
            ws = wb[nom]
            nb_lignes_total = ws.max_row or 0
            nb_colonnes = ws.max_column or 0

            header_row = header_row_force or _detecter_header_row(ws)

            entetes: list[str] = []
            if nb_lignes_total >= header_row:
                for cell in next(
                    ws.iter_rows(min_row=header_row, max_row=header_row, values_only=False)
                ):
                    entetes.append(str(cell.value) if cell.value is not None else "")

            feuilles.append(FeuilleInfo(
                index=idx,
                nom=nom,
                nb_lignes=max(0, nb_lignes_total - header_row),
                nb_colonnes=nb_colonnes,
                header_row=header_row,
                entetes=entetes,
            ))
        return feuilles
    finally:
        wb.close()


# =====================================================================
# 2. Mapping des colonnes
# =====================================================================
@dataclass
class MappingFeuille:
    index_feuille: int
    header_row: int
    colonnes_mappees: dict[int, str] = field(default_factory=dict)
    colonnes_non_mappees: list[str] = field(default_factory=list)
    entetes: list[str] = field(default_factory=list)


def _analyser_entetes(
    entetes: list[str],
    index_feuille: int,
    header_row: int,
) -> MappingFeuille:
    mapping = MappingFeuille(
        index_feuille=index_feuille, header_row=header_row, entetes=entetes
    )
    champs_deja_mappes: set[str] = set()

    for col_idx, entete in enumerate(entetes):
        if not entete or not entete.strip():
            continue
        entete_norm = _normaliser(entete)
        matched_champ = None
        for champ, patterns in COLUMN_PATTERNS.items():
            if champ in champs_deja_mappes:
                continue
            for pat in patterns:
                if pat.search(entete_norm):
                    matched_champ = champ
                    break
            if matched_champ:
                break

        if matched_champ:
            mapping.colonnes_mappees[col_idx] = matched_champ
            champs_deja_mappes.add(matched_champ)
        else:
            mapping.colonnes_non_mappees.append(entete)

    return mapping


# =====================================================================
# 3. Extraction des lignes
# =====================================================================
def _extraire_lignes(
    ws,
    mapping: MappingFeuille,
    mode: str,
    limite_lignes: int | None,
    ligne_debut: int | None,
    ligne_fin: int | None,
) -> tuple[list[dict[str, Any]], int]:
    """
    Parcourt les lignes et normalise. Itération unique (optimisé read_only).

    Retourne (lignes_extraites, nb_rejetees).
    - Les lignes de total/sous-total ne sont PAS incluses dans `lignes_extraites`
      (elles sont comptées dans `nb_rejetees`).
    - Les lignes vides sont ignorées (ni dans lignes_extraites, ni dans nb_rejetees).
    """
    lignes: list[dict[str, Any]] = []
    nb_rejetees = 0

    start = mapping.header_row + 1
    end = None

    if mode == "complet":
        end = ws.max_row
    elif mode == "echantillon":
        end = min(start + (limite_lignes or 100) - 1, ws.max_row)
    elif mode == "plage":
        start = max(mapping.header_row + 1, (ligne_debut or start))
        end = min(ligne_fin or ws.max_row, ws.max_row)
    else:
        raise HTTPException(status_code=400, detail=f"Mode invalide : {mode}")

    for row_idx, row in enumerate(
        ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True),
        start=1,
    ):
        if row_idx < start:
            continue
        if end is not None and row_idx > end:
            break

        # Ignorer les lignes entièrement vides
        if _est_ligne_vide(row):
            continue

        # Détection des rejets (B5)
        if _est_ligne_rejetee(row):
            nb_rejetees += 1
            continue

        record: dict[str, Any] = {"num_ligne_source": row_idx}

        for col_idx, champ in mapping.colonnes_mappees.items():
            if col_idx < len(row):
                val = row[col_idx]
                if val is not None and str(val).strip() != "" and (
                    champ not in record
                    or record[champ] is None
                    or str(record[champ]).strip() == ""
                ):
                    record[champ] = val

        # Conversion coordonnées
        lat_brut = record.get("latitude_decimal")
        lon_brut = record.get("longitude_decimal")
        lat_dec, lon_dec = parser_coordonnees(lat_brut, lon_brut)
        record["latitude_decimal"] = lat_dec
        record["longitude_decimal"] = lon_dec

        # Données brutes
        brut: dict[str, Any] = {}
        for col_idx, val in enumerate(row):
            if (
                col_idx < len(mapping.entetes)
                and val is not None
                and mapping.entetes[col_idx]
            ):
                brut[mapping.entetes[col_idx]] = _serialiser_valeur(val)
        record["donnees_brutes"] = brut

        lignes.append(record)

    return lignes, nb_rejetees


# =====================================================================
# 4. Ingestion d'une feuille
# =====================================================================
def ingerer_feuille(
    db: Session,
    feuille: Feuille,
    run: IngestionRun,
    mode: str,
    limite_lignes: int | None,
    ligne_debut: int | None,
    ligne_fin: int | None,
    chemin_fichier: str,
    header_row_force: int | None = None,
) -> dict[str, int]:
    """
    Ingère une feuille dans ligne_ingeree.

    Retourne {'nb_stockees': int, 'nb_rejetees': int}.
    """
    if not Path(chemin_fichier).exists():
        raise HTTPException(
            status_code=404,
            detail=f"Fichier introuvable : {chemin_fichier}",
        )

    wb = openpyxl.load_workbook(chemin_fichier, read_only=True, data_only=True)
    try:
        if feuille.nom_feuille not in wb.sheetnames:
            raise HTTPException(404, f"Feuille '{feuille.nom_feuille}' introuvable")
        ws = wb[feuille.nom_feuille]

        header_row = header_row_force or _detecter_header_row(ws)

        entetes: list[str] = []
        for cell in next(
            ws.iter_rows(min_row=header_row, max_row=header_row, values_only=False)
        ):
            entetes.append(str(cell.value) if cell.value is not None else "")

        from app.services.mapping import charger_mapping_pour_ingestion
        mapping_colonnes = charger_mapping_pour_ingestion(db, feuille, entetes, header_row)

        from app.services.ingestion import MappingFeuille as MappingFeuilleSchema
        mapping = MappingFeuilleSchema(
            index_feuille=feuille.index_feuille,
            header_row=header_row,
            colonnes_mappees=mapping_colonnes,
            entetes=entetes,
        )

        lignes, nb_rejetees = _extraire_lignes(
            ws, mapping, mode, limite_lignes, ligne_debut, ligne_fin
        )

        # Fallback type_ouvrage_brut depuis le nom de la feuille
        nom_feuille_upper = feuille.nom_feuille.upper()
        type_feuille = None
        for code in ("PMH", "HVA", "PEA", "HV"):
            if code in nom_feuille_upper:
                type_feuille = code
                break

        nb_stockees = 0
        nb_valides = 0
        for ligne in lignes:
            lat = ligne.get("latitude_decimal")
            lon = ligne.get("longitude_decimal")
            if lat is None or lon is None:
                statut_qualite = "geom_invalide"
                message_qualite = "Coordonnées manquantes ou invalides"
            else:
                statut_qualite = "ok"
                message_qualite = None
                nb_valides += 1

            record = LigneIngeree(
                id_feuille=feuille.id_feuille,
                id_run=run.id_run,
                num_ligne_source=ligne["num_ligne_source"],
                donnees_brutes=ligne["donnees_brutes"],
                district_brut=ligne.get("district_brut"),
                region_brute=ligne.get("region_brute"),
                # I1 : departement_brut (pas departement_brute)
                departement_brut=ligne.get("departement_brute"),
                sous_prefecture_brute=ligne.get("sous_prefecture_brute"),
                localite_brute=ligne.get("localite_brute"),
                type_localite_brut=ligne.get("type_localite_brut"),
                latitude_decimal=lat,
                longitude_decimal=lon,
                type_ouvrage_brut=ligne.get("type_ouvrage_brut") or type_feuille,
                etat_ouvrage_brut=ligne.get("etat_ouvrage_brut"),
                annee_projet=_to_int(ligne.get("annee_projet")),
                bailleur_brut=ligne.get("bailleur_brut"),
                type_financement_brut=ligne.get("type_financement_brut"),
                usage_ouvrage_brut=ligne.get("usage_ouvrage_brut"),
                a_cgpe=_to_bool(ligne.get("a_cgpe")),
                statut_qualite=statut_qualite,
                message_qualite=message_qualite,
            )
            db.add(record)
            nb_stockees += 1

        db.flush()
        feuille.nb_lignes = nb_stockees
        feuille.nb_lignes_valides = nb_valides
        feuille.statut_ingestion = "ingere"
        db.flush()
        return {"nb_stockees": nb_stockees, "nb_rejetees": nb_rejetees}
    finally:
        wb.close()


# =====================================================================
# 5. Ingestion d'un fichier
# =====================================================================
def ingerer_fichier(
    db: Session,
    fichier: Fichier,
    run: IngestionRun,
    mode: str = "complet",
    limite_lignes: int | None = None,
    ligne_debut: int | None = None,
    ligne_fin: int | None = None,
    header_row_force: int | None = None,
) -> dict[str, Any]:
    """
    Orchestre l'ingestion d'un fichier.

    IMPORTANT (I2) : ne met PAS à jour `fichier.statut`.
    C'est `run.py` qui le fait en fin de pipeline (cf. décision A3).
    """

    feuilles = db.scalars(
        select(Feuille).where(Feuille.id_fichier == fichier.id_fichier)
    ).all()
    if not feuilles:
        raise HTTPException(
            400, f"Aucune feuille pour le fichier {fichier.id_fichier}"
        )

    total_stockees = 0
    total_rejetees = 0
    resultats = []

    for feuille in feuilles:
        # Capture les attributs AVANT le try (évite PendingRollbackError)
        feuille_id = feuille.id_feuille
        feuille_nom = feuille.nom_feuille

        try:
            res = ingerer_feuille(
                db, feuille, run, mode, limite_lignes, ligne_debut, ligne_fin,
                fichier.chemin_stockage, header_row_force,
            )
            total_stockees += res["nb_stockees"]
            total_rejetees += res["nb_rejetees"]
            resultats.append({
                "id_feuille": feuille_id,
                "nom_feuille": feuille_nom,
                "statut": "ok",
                "nb_stockees": res["nb_stockees"],
                "nb_rejetees": res["nb_rejetees"],
            })
        except Exception as e:
            db.rollback()
            logger.exception("Erreur feuille %s : %s", feuille_nom, e)
            feuille = db.get(Feuille, feuille_id)
            if feuille is not None:
                feuille.statut_ingestion = "erreur"
                feuille.message_erreur = str(e)
                db.flush()
            resultats.append({
                "id_feuille": feuille_id,
                "nom_feuille": feuille_nom,
                "statut": "erreur",
                "message": str(e),
            })

    # Mise à jour des compteurs agrégés
    run.nb_lignes_ingerees = total_stockees
    # B5 : nb_lignes_total = stockées + rejetées
    fichier.nb_lignes_total = total_stockees + total_rejetees
    # I2 : ne PAS toucher à fichier.statut (fait par run.py)
    # fichier.date_ingestion sera mise à jour par run.py aussi.
    db.flush()

    return {
        "id_fichier": fichier.id_fichier,
        "id_run": run.id_run,
        "total_stockees": total_stockees,
        "total_rejetees": total_rejetees,
        "feuilles": resultats,
    }
