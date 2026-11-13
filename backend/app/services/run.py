"""
Service de run : exécute le pipeline complet (ingestion → rapprochement → consolidation).

IMPORTANT (Bible § 3.2.4, décision A3) :
- `fichier.statut` est mis à jour ICI, en fin de pipeline, pas par `ingestion.py`.
- `fichier.date_ingestion` idem.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Feuille, Fichier, IngestionRun
from app.services.consolidation import consolider_lignes_run
from app.services.ingestion import ingerer_fichier
from app.services.rapprochement import rapprocher_lignes_run

logger = logging.getLogger("dhr.run")


def _determiner_statut_fichier(db: Session, fichier: Fichier) -> str:
    """
    Détermine le statut du fichier à partir des feuilles :
    - 'ingere'  : au moins une feuille 'ingere' et aucune 'erreur'
    - 'partiel' : au moins une 'erreur' et au moins une 'ingere'
    - 'erreur'  : toutes les feuilles 'erreur'
    """
    feuilles = db.scalars(
        select(Feuille).where(Feuille.id_fichier == fichier.id_fichier)
    ).all()
    if not feuilles:
        return "erreur"

    statuts = [f.statut_ingestion for f in feuilles]
    nb_ok = sum(1 for s in statuts if s == "ingere")
    nb_err = sum(1 for s in statuts if s == "erreur")

    if nb_err == len(statuts):
        return "erreur"
    if nb_err > 0 and nb_ok > 0:
        return "partiel"
    return "ingere"

def creer_run(
    db: Session,
    id_fichier: int,
    id_feuille: int | None = None,
    mode: str = "complet",
    limite_lignes: int | None = None,
    ligne_debut: int | None = None,
    ligne_fin: int | None = None,
) -> IngestionRun:
    """Crée un IngestionRun en statut 'en_cours'."""
    fichier = db.get(Fichier, id_fichier)
    if fichier is None:
        raise HTTPException(404, f"Fichier {id_fichier} introuvable")

    if id_feuille is not None:
        feuille = db.get(Feuille, id_feuille)
        if feuille is None or feuille.id_fichier != id_fichier:
            raise HTTPException(
                404,
                f"Feuille {id_feuille} introuvable pour le fichier {id_fichier}",
            )

    run = IngestionRun(
        id_fichier=id_fichier,
        id_feuille=id_feuille,
        mode=mode,
        limite_lignes=limite_lignes,
        ligne_debut=ligne_debut,
        ligne_fin=ligne_fin,
        statut="en_cours",
    )
    db.add(run)
    db.flush()
    return run

def executer_pipeline(db: Session, id_run: int) -> dict[str, Any]:
    """
    Exécute le pipeline complet pour un run :
    1. Ingestion
    2. Rapprochement
    3. Consolidation

    Met à jour le run ET le fichier (statut, date_ingestion).
    """
    run = db.get(IngestionRun, id_run)
    if run is None:
        raise ValueError(f"Run {id_run} introuvable")

    fichier = db.get(Fichier, run.id_fichier)
    if fichier is None:
        raise ValueError(f"Fichier {run.id_fichier} introuvable")

    # Capture de l'ID avant le try pour éviter tout accès post-rollback
    fichier_id = fichier.id_fichier

    try:
        # 1. INGESTION
        logger.info("Run %s : ingestion", id_run)
        resultat_ingestion = ingerer_fichier(
            db, fichier, run,
            mode=run.mode,
            limite_lignes=run.limite_lignes,
            ligne_debut=run.ligne_debut,
            ligne_fin=run.ligne_fin,
        )
        db.flush()

        # 2. RAPPROCHEMENT
        logger.info("Run %s : rapprochement", id_run)
        stats_rapprochement = rapprocher_lignes_run(db, id_run)
        db.flush()

        # 3. CONSOLIDATION
        logger.info("Run %s : consolidation", id_run)
        stats_consolidation = consolider_lignes_run(db, id_run)
        db.flush()

        # Mise à jour du run
        total = resultat_ingestion["total_stockees"]
        run.statut = "termine" if total > 0 else "erreur"
        run.finished_at = datetime.now(UTC)
        db.flush()

        # Mise à jour du fichier (I2 : c'est ici, pas dans ingestion.py)
        fichier.statut = _determiner_statut_fichier(db, fichier)
        fichier.date_ingestion = datetime.now(UTC)
        db.flush()

        return {
            "id_run": id_run,
            "id_fichier": fichier_id,
            "ingestion": resultat_ingestion,
            "rapprochement": stats_rapprochement,
            "consolidation": stats_consolidation,
        }

    except Exception as e:
        logger.exception("Erreur pipeline run %s : %s", id_run, e)
        db.rollback()
        run_err = db.get(IngestionRun, id_run)
        if run_err is not None:
            run_err.statut = "erreur"
            run_err.message = str(e)
            run_err.finished_at = datetime.now(UTC)
        fichier_err = db.get(Fichier, fichier_id)
        if fichier_err is not None:
            fichier_err.statut = "erreur"
        db.commit()
        raise
