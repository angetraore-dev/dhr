"""
Router ingestion : suivi des runs et des lignes.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.db import get_db
from app.deps import CursorPagination
from app.models import Feuille, IngestionRun, LigneIngeree
from app.schemas.common import PaginatedCursor
from app.schemas.ingestion import (
    IngestionRun as IngestionRunSchema,
)
from app.schemas.ingestion import (
    LigneIngeree as LigneIngereeSchema,
)
from app.schemas.ingestion import (
    LigneIngereeAvecBrut,
)

router = APIRouter(tags=["Ingestion"])

StatutQualiteFilter = Literal[
    "ok",
    "localite_non_resolue",
    "geom_invalide",
    "type_ouvrage_inconnu",
    "rejete",
    "doublon_suspect",
]


def _parse_cursor(cursor: str) -> int:
    try:
        return int(cursor)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Curseur invalide",
        ) from e


@router.get(
    "/runs/{id}",
    response_model=IngestionRunSchema,
    summary="Suivi d'un run",
    dependencies=[Depends(require_api_key)],
)
def get_run(id: int, db: Session = Depends(get_db)) -> IngestionRunSchema:
    run = db.get(IngestionRun, id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {id} introuvable",
        )
    return IngestionRunSchema.model_validate(run)


@router.get(
    "/runs/{id}/lignes",
    response_model=PaginatedCursor[LigneIngereeSchema],
    summary="Lignes d'un run (cursor)",
    dependencies=[Depends(require_api_key)],
)
def list_lignes_run(
    id: int,
    statut_qualite: StatutQualiteFilter | None = Query(None),
    pagination: CursorPagination = Depends(),
    db: Session = Depends(get_db),
) -> PaginatedCursor[LigneIngereeSchema]:
    run = db.get(IngestionRun, id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {id} introuvable",
        )

    stmt = select(LigneIngeree).where(LigneIngeree.id_run == id)
    if statut_qualite:
        stmt = stmt.where(LigneIngeree.statut_qualite == statut_qualite)

    if pagination.cursor:
        last_id = _parse_cursor(pagination.cursor)
        stmt = stmt.where(LigneIngeree.id_ligne > last_id)

    stmt = stmt.order_by(LigneIngeree.id_ligne).limit(pagination.limit + 1)
    rows = db.scalars(stmt).all()
    has_more = len(rows) > pagination.limit
    if has_more:
        rows = rows[: pagination.limit]

    next_cursor = str(rows[-1].id_ligne) if has_more and rows else None
    return PaginatedCursor(
        data=[LigneIngereeSchema.model_validate(r) for r in rows],
        pagination=pagination.to_response(next_cursor=next_cursor, has_more=has_more),
    )


@router.get(
    "/feuilles/{id}/lignes",
    response_model=PaginatedCursor[LigneIngereeSchema],
    summary="Lignes d'une feuille (cursor)",
    dependencies=[Depends(require_api_key)],
)
def list_lignes_feuille(
    id: int,
    id_run: int | None = Query(None),
    statut_qualite: StatutQualiteFilter | None = Query(None),
    pagination: CursorPagination = Depends(),
    db: Session = Depends(get_db),
) -> PaginatedCursor[LigneIngereeSchema]:
    feuille = db.get(Feuille, id)
    if feuille is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feuille {id} introuvable",
        )

    stmt = select(LigneIngeree).where(LigneIngeree.id_feuille == id)
    if id_run is not None:
        stmt = stmt.where(LigneIngeree.id_run == id_run)
    if statut_qualite:
        stmt = stmt.where(LigneIngeree.statut_qualite == statut_qualite)

    if pagination.cursor:
        last_id = _parse_cursor(pagination.cursor)
        stmt = stmt.where(LigneIngeree.id_ligne > last_id)

    stmt = stmt.order_by(LigneIngeree.id_ligne).limit(pagination.limit + 1)
    rows = db.scalars(stmt).all()
    has_more = len(rows) > pagination.limit
    if has_more:
        rows = rows[: pagination.limit]

    next_cursor = str(rows[-1].id_ligne) if has_more and rows else None
    return PaginatedCursor(
        data=[LigneIngereeSchema.model_validate(r) for r in rows],
        pagination=pagination.to_response(next_cursor=next_cursor, has_more=has_more),
    )


@router.get(
    "/lignes/{id}",
    response_model=LigneIngereeAvecBrut | LigneIngereeSchema,
    summary="Détail d'une ligne",
    dependencies=[Depends(require_api_key)],
)
def get_ligne(
    id: int,
    include: Literal["brut"] | None = Query(None),
    db: Session = Depends(get_db),
) -> LigneIngereeAvecBrut | LigneIngereeSchema:
    ligne = db.get(LigneIngeree, id)
    if ligne is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ligne {id} introuvable",
        )

    if include == "brut":
        return LigneIngereeAvecBrut.model_validate(ligne)
    return LigneIngereeSchema.model_validate(ligne)
