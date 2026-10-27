"""
Schémas des ouvrages consolidés, CGPE et qualité.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.geo import GeoJSONPoint
from app.schemas.referentiels import LocaliteResume


# ----- Ouvrage -----
class TypeOuvrageResume(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    libelle: str


class CGPESummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    existe: bool
    statut: str | None = None


class FinancementResume(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_projet: int
    nom_projet: str
    bailleur: str
    role: Literal["principal", "co_financement"]


class Ouvrage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_ouvrage: int
    code_ouvrage: str | None = None
    type_ouvrage: TypeOuvrageResume
    etat: Literal["fonctionnel", "en_panne", "abandonne", "inconnu"]
    annee_realisation: int | None = None
    localite: LocaliteResume
    geom: GeoJSONPoint | None = None
    cgpe: CGPESummary | None = None
    financements: list[FinancementResume] = Field(default_factory=list)
    metadata: dict[str, Any] | None = Field(
        None,
        description="Présent uniquement si ?include=metadata",
    )


# ----- CGPE -----
class CGPE(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_cgpe: int
    id_localite: int
    id_ouvrage: int | None = None
    existe: bool
    date_creation: date | None = None
    statut: Literal["fonctionnel", "non_fonctionnel", "inconnu"] | None = None
    nb_membres: int | None = None
    commentaire: str | None = None
    metadata: dict[str, Any] | None = None


# ----- Qualité -----
class QualiteStats(BaseModel):
    ok: int = 0
    localite_non_resolue: int = 0
    geom_invalide: int = 0
    type_ouvrage_inconnu: int = 0
    rejete: int = 0
    doublon_suspect: int = 0


class QualiteFichier(BaseModel):
    id_fichier: int
    nom_fichier: str
    source: str
    statut: str
    nb_lignes_total: int
    qualite: QualiteStats
    taux_reussite: float