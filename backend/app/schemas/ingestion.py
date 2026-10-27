"""
Schémas des runs d'ingestion et lignes normalisées.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.geo import GeoJSONPoint


# ----- IngestionRun -----
class IngestionRun(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_run: int
    id_fichier: int
    id_feuille: int | None = None
    mode: Literal["complet", "echantillon", "plage"]
    limite_lignes: int | None = None
    ligne_debut: int | None = None
    ligne_fin: int | None = None
    nb_lignes_ingerees: int
    statut: Literal["en_cours", "termine", "erreur", "annule"]
    message: str | None = None
    started_at: datetime
    finished_at: datetime | None = None


# ----- Requêtes de lancement de run -----
class RunComplet(BaseModel):
    id_feuille: int | None = None
    mode: Literal["complet"] = "complet"


class RunEchantillon(BaseModel):
    id_feuille: int | None = None
    mode: Literal["echantillon"] = "echantillon"
    limite_lignes: int = Field(..., ge=1)


class RunPlage(BaseModel):
    id_feuille: int | None = None
    mode: Literal["plage"] = "plage"
    ligne_debut: int = Field(..., ge=1)
    ligne_fin: int = Field(..., ge=1)


# ----- LigneIngeree -----
class LigneIngeree(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_ligne: int
    id_feuille: int
    num_ligne_source: int
    localite_brute: str | None = None
    type_ouvrage_brut: str | None = None
    latitude_decimal: float | None = None
    longitude_decimal: float | None = None
    geom: GeoJSONPoint | None = None
    statut_qualite: Literal[
        "ok",
        "localite_non_resolue",
        "geom_invalide",
        "type_ouvrage_inconnu",
        "rejete",
        "doublon_suspect",
    ]
    annee_projet: int | None = None
    bailleur_brut: str | None = None


class LigneIngereeAvecBrut(LigneIngeree):
    donnees_brutes: dict[str, Any]