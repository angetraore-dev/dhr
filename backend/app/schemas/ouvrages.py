"""
Schémas des ouvrages consolidés, CGPE et qualité.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.geo import GeoJSONPoint
from app.schemas.referentiels import LocaliteResume

# ----- Enums (miroir des CHECK SQL) -----
NatureOuvrage = Literal["puits", "forage", "inconnu"]
TypeAlimentation = Literal["PMH", "HVA", "PEA", "HV", "AUTRE"]
RealisationPar = Literal["public", "prive", "inconnu"]
EtatOuvrage = Literal["fonctionnel", "en_panne", "abandonne", "inconnu"]
StatutCGPE = Literal["fonctionnel", "non_fonctionnel", "inconnu"]


# ----- Ouvrage -----
class CGPESummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    existe: bool
    statut: StatutCGPE | None = None


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
    nature_ouvrage: NatureOuvrage | None = None
    type_alimentation: TypeAlimentation | None = None
    realisation_par: RealisationPar | None = None
    etat: EtatOuvrage
    annee_realisation: int | None = None
    localite: LocaliteResume
    geom: GeoJSONPoint | None = None
    cgpe: CGPESummary | None = None
    financements: list[FinancementResume] = Field(default_factory=list)
    metadata: dict[str, Any] | None = None
    qualite_eau: dict[str, Any] | None = None


# ----- CGPE -----
class CGPE(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_cgpe: int
    id_localite: int
    id_ouvrage: int | None = None
    existe: bool
    date_creation: date | None = None
    statut: StatutCGPE | None = None
    nb_membres: int | None = None
    commentaire: str | None = None
    metadata: dict[str, Any] | None = None


# ----- Qualité -----
class QualiteStats(BaseModel):
    ok: int = 0
    localite_non_resolue: int = 0
    geom_invalide: int = 0
    # Conservé : c'est un statut de ligne_ingeree.statut_qualite,
    # pas un champ de ouvrage (le CHECK SQL le référence toujours).
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
