"""
Dépendances partagées entre les routers.
"""

from typing import Literal

from fastapi import Query

from app.schemas.common import PaginationCursor, PaginationOffset


# --- Pagination offset ---
class OffsetPagination:
    """Dépendance de pagination offset."""

    def __init__(
        self,
        offset: int = Query(0, ge=0, description="Décalage"),
        limit: int = Query(100, ge=1, le=1000, description="Taille de page"),
    ):
        self.offset = offset
        self.limit = limit

    def to_response(self, total: int | None = None) -> PaginationOffset:
        return PaginationOffset(offset=self.offset, limit=self.limit, total=total)


# --- Pagination cursor ---
class CursorPagination:
    """Dépendance de pagination cursor."""

    def __init__(
        self,
        cursor: str | None = Query(None, description="Curseur opaque"),
        limit: int = Query(100, ge=1, le=1000, description="Taille de page"),
    ):
        self.cursor = cursor
        self.limit = limit

    def to_response(self, next_cursor: str | None, has_more: bool) -> PaginationCursor:
        return PaginationCursor(
            limit=self.limit, next_cursor=next_cursor, has_more=has_more
        )


# --- Types alignés sur les CHECK SQL (Bible § 2.2.C) ---
TypeAlimentation = Literal["PMH", "HVA", "PEA", "HV", "AUTRE"]
NatureOuvrage = Literal["puits", "forage", "inconnu"]
RealisationPar = Literal["public", "prive", "inconnu"]
EtatOuvrage = Literal["fonctionnel", "en_panne", "abandonne", "inconnu"]
StatutQualite = Literal[
    "ok", "localite_non_resolue", "geom_invalide",
    "type_ouvrage_inconnu", "rejete", "doublon_suspect",
]

# --- Filtres carto/ouvrages ---
class OuvrageFilters:
    """Filtres communs aux endpoints ouvrages et carto.

    Les valeurs des filtres métier sont contraintes par `Literal` :
    une valeur hors domaine → 422 Validation Error (RFC 7807), aligné
    sur les CHECK SQL de `ouvrage` (Bible § 2.2.C).
    """

    def __init__(
        self,
        type_alimentation: TypeAlimentation | None = Query(
            None, description="Type d'alimentation (PMH, HVA, PEA, HV, AUTRE)"
        ),
        nature_ouvrage: NatureOuvrage | None = Query(
            None, description="Nature physique (puits, forage, inconnu)"
        ),
        realisation_par: RealisationPar | None = Query(
            None, description="Qui a réalisé (public, prive, inconnu)"
        ),
        etat: EtatOuvrage | None = Query(
            None, description="État (fonctionnel, en_panne, abandonne, inconnu)"
        ),
        region: str | None = Query(None),
        departement: str | None = Query(None),
        sous_prefecture: str | None = Query(None),
        localite: str | None = Query(None),
        bailleur: str | None = Query(None),
        annee_min: int | None = Query(None, ge=1900),
        annee_max: int | None = Query(None, ge=1900),
    ):
        self.type_alimentation = type_alimentation
        self.nature_ouvrage = nature_ouvrage
        self.realisation_par = realisation_par
        self.etat = etat
        self.region = region
        self.departement = departement
        self.sous_prefecture = sous_prefecture
        self.localite = localite
        self.bailleur = bailleur
        self.annee_min = annee_min
        self.annee_max = annee_max

    def to_dict(self) -> dict:
        return {
            "type_alimentation": self.type_alimentation,
            "nature_ouvrage": self.nature_ouvrage,
            "realisation_par": self.realisation_par,
            "etat": self.etat,
            "region": self.region,
            "departement": self.departement,
            "sous_prefecture": self.sous_prefecture,
            "localite": self.localite,
            "bailleur": self.bailleur,
            "annee_min": self.annee_min,
            "annee_max": self.annee_max,
        }
