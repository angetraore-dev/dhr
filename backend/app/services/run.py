"""
Service de run : exécute le pipeline complet (ingestion → rapprochement → consolidation).

Utilisé par :
- POST /fichiers/{id}/runs (asynchrone via BackgroundTask)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Feuille, Fichier, IngestionRun
from app.services.consolidation import consolider_lignes_run
from app.services.ingestion import ingerer_fichier
from app.services.rapprochement import rapprocher_lignes_run

logger = logging.getLogger("dhr.run")


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

    Met à jour le run et le fichier.
    """
    run = db.get(IngestionRun, id_run)
    if run is None:
        raise ValueError(f"Run {id_run} introuvable")

    fichier = db.get(Fichier, run.id_fichier)
    if fichier is None:
        raise ValueError(f"Fichier {run.id_fichier} introuvable")

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

        # Met à jour le run
        run.statut = "termine"
        run.finished_at = datetime.now(timezone.utc)
        db.flush()

        return {
            "id_run": id_run,
            "id_fichier": fichier.id_fichier,
            "ingestion": resultat_ingestion,
            "rapprochement": stats_rapprochement,
            "consolidation": stats_consolidation,
        }

    except Exception as e:
        logger.exception("Erreur pipeline run %s : %s", id_run, e)
        db.rollback()
        # Recharge le run après rollback
        run = db.get(IngestionRun, id_run)
        if run is not None:
            run.statut = "erreur"
            run.message = str(e)
            run.finished_at = datetime.now(timezone.utc)
            db.flush()
        raise