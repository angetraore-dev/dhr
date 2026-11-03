"""
Service d'upload : sauvegarde d'un fichier Excel + détection des feuilles.

1. Sauvegarde le fichier dans /app/uploads/
2. Calcule le hash SHA-256 (détection de réingestion)
3. Détecte les feuilles (detecter_feuilles)
4. Crée les lignes feuille en base
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

import openpyxl
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Feuille, Fichier, Source
from app.services.ingestion import detecter_feuilles

logger = logging.getLogger("dhr.upload")


def _hash_fichier(chemin: Path) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def uploader_fichier(
    db: Session,
    file: UploadFile,
    id_source: int,
    commentaire: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """
    Upload un fichier Excel :
    1. Sauvegarde dans /app/uploads/
    2. Détecte les feuilles
    3. Crée fichier + feuille en base
    """
    settings = get_settings()

    # Vérifie que la source existe
    source = db.get(Source, id_source)
    if source is None:
        raise HTTPException(404, f"Source {id_source} introuvable")

    # Vérifie l'extension
    nom_original = file.filename or "fichier.xlsx"
    if not nom_original.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Seuls les fichiers .xlsx et .xls sont acceptés")

    # Sauvegarde dans /app/uploads/
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Nom unique : timestamp + nom original
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    nom_stockage = f"{ts}_{nom_original}"
    chemin = upload_dir / nom_stockage

    contenu = file.file.read()
    if len(contenu) == 0:
        raise HTTPException(400, "Fichier vide")
    chemin.write_bytes(contenu)

    taille = len(contenu)
    hash_sha256 = _hash_fichier(chemin)

    # Détection de réingestion (hash identique)
    est_reingestion = False
    existing = db.scalar(select(Fichier).where(Fichier.hash_sha256 == hash_sha256))
    if existing is not None and not force:
        # Supprime le fichier qu'on vient d'écrire
        chemin.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ce fichier a déjà été ingéré (id_fichier={existing.id_fichier}). Utilisez ?force=true pour forcer.",
        )
    if existing is not None:
        est_reingestion = True

    # Détecte les feuilles
    try:
        feuilles_info = detecter_feuilles(chemin)
    except Exception as e:
        chemin.unlink(missing_ok=True)
        raise HTTPException(400, f"Impossible d'analyser le fichier Excel : {e}")

    # Crée le fichier
    fichier = Fichier(
        id_source=id_source,
        nom_fichier_original=nom_original,
        chemin_stockage=str(chemin),
        hash_sha256=hash_sha256,
        taille_octets=taille,
        statut="en_attente",
        nb_feuilles=len(feuilles_info),
        nb_lignes_total=0,
        est_reingestion=est_reingestion,
        commentaire=commentaire,
    )
    db.add(fichier)
    db.flush()

    # Crée les feuilles
    for fi in feuilles_info:
        feuille = Feuille(
            id_fichier=fichier.id_fichier,
            nom_feuille=fi.nom,
            index_feuille=fi.index,
            type_contenu="inconnu",
            nb_lignes=fi.nb_lignes,
            statut_ingestion="en_attente",
        )
        db.add(feuille)
    db.flush()

    return {
        "id_fichier": fichier.id_fichier,
        "nom_fichier_original": nom_original,
        "statut": fichier.statut,
        "hash_sha256": hash_sha256,
        "est_reingestion": est_reingestion,
        "feuilles_detectees": [
            {"nom": fi.nom, "index": fi.index, "nb_lignes_estime": fi.nb_lignes}
            for fi in feuilles_info
        ],
    }