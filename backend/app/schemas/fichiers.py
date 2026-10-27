"""
Schémas des fichiers et feuilles.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.referentiels import Source


# ----- Fichier -----
class Fichier(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_fichier: int
    nom_fichier_original: str
    source: Source
    hash_sha256: str | None = None
    taille_octets: int | None = None
    date_reception: datetime
    date_ingestion: datetime | None = None
    statut: Literal["en_attente", "en_cours", "ingere", "partiel", "erreur"]
    nb_feuilles: int
    nb_lignes_total: int
    est_reingestion: bool
    commentaire: str | None = None


# ----- Feuille -----
class Feuille(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_feuille: int
    id_fichier: int
    nom_feuille: str
    index_feuille: int
    type_contenu: Literal["ouvrages", "cgpe", "mixte", "autre", "inconnu"]
    nb_lignes: int
    nb_lignes_valides: int
    statut_ingestion: Literal[
        "en_attente", "en_cours", "ingere", "partiel", "erreur"
    ]
    message_erreur: str | None = None