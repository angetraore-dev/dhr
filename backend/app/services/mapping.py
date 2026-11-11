"""
Service de mapping des colonnes Excel → champs normalisés.

Fonctions :
- proposer_mapping_fichier(db, id_fichier) → mapping auto (proposition)
- sauvegarder_mapping_feuille(db, id_feuille, colonnes) → sauvegarde validée
- charger_mapping_pour_ingestion(db, feuille, entetes, header_row) → mapping pour l'ingestion
"""
from __future__ import annotations

import logging
import re
import unicodedata
from decimal import Decimal
from pathlib import Path

import openpyxl
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Feuille, Fichier, MappingFeuille
from app.schemas.fichiers import (
    MappingColonne,
    MappingProposalFeuille,
    MappingValidationColonne,
)
from app.services.patterns import COLUMN_PATTERNS

logger = logging.getLogger("dhr.mapping")


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


def _detecter_header_row(ws, max_scan: int = 30) -> int:
    """Détecte la ligne d'entête."""
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


def _get_patterns() -> dict[str, list[re.Pattern]]:
    """Récupère les patterns partagés."""
    return COLUMN_PATTERNS


# =====================================================================
# Proposition de mapping
# =====================================================================
def _proposer_mapping_feuille(
    ws,
    header_row: int,
    entetes: list[str],
) -> list[MappingColonne]:
    """Propose un mapping automatique pour une feuille."""
    patterns = _get_patterns()
    champs_deja_mappes: set[str] = set()
    colonnes: list[MappingColonne] = []

    for _col_idx, entete in enumerate(entetes):
        if not entete or not entete.strip():
            continue

        entete_norm = _normaliser(entete)
        champ_cible = None
        confiance = Decimal("0.00")

        for champ, pats in patterns.items():
            if champ in champs_deja_mappes:
                continue
            for pat in pats:
                if pat.search(entete_norm):
                    champ_cible = champ
                    confiance = Decimal("1.00")
                    break
            if champ_cible:
                break

        if champ_cible:
            champs_deja_mappes.add(champ_cible)

        colonnes.append(
            MappingColonne(
                id_mapping=None,
                entete_brut=entete,
                champ_cible=champ_cible,
                confiance=confiance if champ_cible else None,
                valide_par_utilisateur=False,
            )
        )

    return colonnes


def proposer_mapping_fichier(
    db: Session,
    id_fichier: int,
) -> list[MappingProposalFeuille]:
    """
    Propose un mapping pour toutes les feuilles d'un fichier.
    Retourne une liste de MappingProposalFeuille.
    """
    fichier = db.get(Fichier, id_fichier)
    if fichier is None:
        raise ValueError(f"Fichier {id_fichier} introuvable")

    if not Path(fichier.chemin_stockage).exists():
        raise ValueError(f"Fichier introuvable sur disque : {fichier.chemin_stockage}")

    feuilles = db.scalars(
        select(Feuille).where(Feuille.id_fichier == id_fichier).order_by(Feuille.index_feuille)
    ).all()

    if not feuilles:
        raise ValueError(f"Aucune feuille pour le fichier {id_fichier}")

    resultats: list[MappingProposalFeuille] = []

    wb = openpyxl.load_workbook(fichier.chemin_stockage, read_only=True, data_only=True)
    try:
        for feuille in feuilles:
            if feuille.nom_feuille not in wb.sheetnames:
                logger.warning("Feuille '%s' introuvable dans le fichier", feuille.nom_feuille)
                continue

            ws = wb[feuille.nom_feuille]
            header_row = _detecter_header_row(ws)

            entetes: list[str] = []
            for cell in next(ws.iter_rows(min_row=header_row, max_row=header_row, values_only=False)):
                entetes.append(str(cell.value) if cell.value is not None else "")

            # Si un mapping validé existe, on l'utilise
            mapping_valide = db.scalars(
                select(MappingFeuille).where(
                    MappingFeuille.id_feuille == feuille.id_feuille,
                    MappingFeuille.valide_par_utilisateur is True,
                )
            ).all()

            if mapping_valide:
                colonnes = [
                    MappingColonne(
                        id_mapping=m.id_mapping,
                        entete_brut=m.entete_brut,
                        champ_cible=m.champ_cible,
                        confiance=m.confiance,
                        valide_par_utilisateur=True,
                    )
                    for m in mapping_valide
                ]
            else:
                colonnes = _proposer_mapping_feuille(ws, header_row, entetes)

            resultats.append(
                MappingProposalFeuille(
                    id_feuille=feuille.id_feuille,
                    nom_feuille=feuille.nom_feuille,
                    header_row=header_row,
                    colonnes=colonnes,
                )
            )
    finally:
        wb.close()

    return resultats


# =====================================================================
# Sauvegarde du mapping validé
# =====================================================================
def sauvegarder_mapping_feuille(
    db: Session,
    id_feuille: int,
    colonnes: list[MappingValidationColonne],
) -> MappingProposalFeuille:
    """
    Sauvegarde le mapping validé pour une feuille.
    Remplace l'ancien mapping validé s'il existe.
    """
    feuille = db.get(Feuille, id_feuille)
    if feuille is None:
        raise ValueError(f"Feuille {id_feuille} introuvable")

    # Supprime l'ancien mapping validé
    db.execute(
        delete(MappingFeuille).where(
            MappingFeuille.id_feuille == id_feuille,
            MappingFeuille.valide_par_utilisateur is True,
        )
    )

    # Insère le nouveau mapping
    for col in colonnes:
        m = MappingFeuille(
            id_feuille=id_feuille,
            entete_brut=col.entete_brut,
            champ_cible=col.champ_cible,
            confiance=Decimal("1.00") if col.champ_cible else None,
            valide_par_utilisateur=True,
        )
        db.add(m)

    db.flush()

    # Recalcule le header_row (à partir du fichier source)
    header_row = 1
    fichier = db.get(Fichier, feuille.id_fichier)
    if fichier is not None and Path(fichier.chemin_stockage).exists():
        wb = openpyxl.load_workbook(fichier.chemin_stockage, read_only=True, data_only=True)
        try:
            if feuille.nom_feuille in wb.sheetnames:
                ws = wb[feuille.nom_feuille]
                header_row = _detecter_header_row(ws)
        finally:
            wb.close()

    # Récupère le mapping sauvegardé
    mapping = db.scalars(
        select(MappingFeuille).where(
            MappingFeuille.id_feuille == id_feuille,
            MappingFeuille.valide_par_utilisateur is True,
        )
    ).all()

    return MappingProposalFeuille(
        id_feuille=feuille.id_feuille,
        nom_feuille=feuille.nom_feuille,
        header_row=header_row,
        colonnes=[
            MappingColonne(
                id_mapping=m.id_mapping,
                entete_brut=m.entete_brut,
                champ_cible=m.champ_cible,
                confiance=m.confiance,
                valide_par_utilisateur=True,
            )
            for m in mapping
        ],
    )


# =====================================================================
# Chargement du mapping (pour l'ingestion)
# =====================================================================
def charger_mapping_pour_ingestion(
    db: Session,
    feuille: Feuille,
    entetes: list[str],
    header_row: int,
) -> dict[int, str]:
    """
    Retourne un dict {idx_col: champ_cible} pour l'ingestion.
    Priorité :
    1. Mapping validé par l'utilisateur
    2. Mapping auto (fallback)
    """
    # 1. Mapping validé
    mappings = db.scalars(
        select(MappingFeuille).where(
            MappingFeuille.id_feuille == feuille.id_feuille,
            MappingFeuille.valide_par_utilisateur is True,
        )
    ).all()

    if mappings:
        mapping_par_entete = {m.entete_brut: m.champ_cible for m in mappings}
        result: dict[int, str] = {}
        for idx, entete in enumerate(entetes):
            if entete in mapping_par_entete:
                champ = mapping_par_entete[entete]
                if champ:
                    result[idx] = champ
        return result

    # 2. Fallback : mapping auto (via une fonction locale pour éviter l'import circulaire)
    from app.services.ingestion import _analyser_entetes
    mapping_auto = _analyser_entetes(entetes, feuille.index_feuille, header_row)
    return mapping_auto.colonnes_mappees
