"""
Schémas des référentiels : Source, TypeOuvrage, RefGeoAdmin, Localite.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.geo import GeoJSONPoint


# ----- Source -----
class SourceBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nom: str
    type_source: Literal["public", "prive", "bailleur", "etat", "autre"]
    actif: bool


class Source(SourceBase):
    id_source: int


# ----- TypeOuvrage -----
class TypeOuvrage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_type_ouvrage: int
    code: str
    libelle: str
    description: str | None = None
    actif: bool


# ----- RefGeoAdmin -----
class RefGeoParent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_geo: int
    niveau: str
    nom: str


class RefGeoAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_geo: int
    niveau: Literal[
        "district", "region", "departement", "sous_prefecture", "localite"
    ]
    nom: str
    code_officiel: str | None = None
    type_localite: Literal["village", "campement", "autre"] | None = None
    parent: RefGeoParent | None = None


# ----- Localite -----
class LocaliteResume(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_localite: int
    nom_usage: str


class Localite(LocaliteResume):
    latitude_centre: float | None = None
    longitude_centre: float | None = None
    geom_centre: GeoJSONPoint | None = None
    alias: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] | None = Field(
        None,
        description="Présent uniquement si ?include=metadata",
    )