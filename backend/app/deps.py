"""
Dépendances partagées entre les routers.
"""
from __future__ import annotations

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


# --- Filtres carto/ouvrages ---
class OuvrageFilters:
    """Filtres communs aux endpoints ouvrages et carto."""

    def __init__(
        self,
        type_ouvrage: str | None = Query(None, description="Code type d'ouvrage"),
        etat: Literal["fonctionnel", "en_panne", "abandonne", "inconnu"] | None = Query(None),
        district: str | None = Query(None),
        region: str | None = Query(None),
        departement: str | None = Query(None),
        sous_prefecture: str | None = Query(None),
        annee_min: int | None = Query(None, ge=1900),
        annee_max: int | None = Query(None, ge=1900),
    ):
        self.type_ouvrage = type_ouvrage
        self.etat = etat
        self.district = district
        self.region = region
        self.departement = departement
        self.sous_prefecture = sous_prefecture
        self.annee_min = annee_min
        self.annee_max = annee_max

    def to_dict(self) -> dict:
        return {
            "type_ouvrage": self.type_ouvrage,
            "etat": self.etat,
            "district": self.district,
            "region": self.region,
            "departement": self.departement,
            "sous_prefecture": self.sous_prefecture,
            "annee_min": self.annee_min,
            "annee_max": self.annee_max,
        }