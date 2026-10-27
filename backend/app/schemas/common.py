"""
Schémas communs : erreurs RFC 7807, pagination.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Problem(BaseModel):
    """Format d'erreur RFC 7807 (Problem Details)."""

    type: str = Field(..., description="URI identifiant le type d'erreur")
    title: str = Field(..., description="Résumé lisible")
    status: int = Field(..., description="Code HTTP")
    detail: str | None = Field(None, description="Message précis")
    instance: str | None = Field(None, description="URI de la requête")
    errors: list[dict[str, Any]] | None = Field(
        None, description="Liste des erreurs par champ"
    )


class PaginationOffset(BaseModel):
    """Pagination offset (petites listes)."""

    offset: int
    limit: int
    total: int | None = None


class PaginationCursor(BaseModel):
    """Pagination cursor (listes volumineuses)."""

    limit: int
    next_cursor: str | None = None
    has_more: bool


class PaginatedOffset[T](BaseModel):
    """Réponse paginée offset."""

    data: list[T]
    pagination: PaginationOffset


class PaginatedCursor[T](BaseModel):
    """Réponse paginée cursor."""

    data: list[T]
    pagination: PaginationCursor