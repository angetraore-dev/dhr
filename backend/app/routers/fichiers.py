"""
Router des fichiers et feuilles.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth import require_api_key
from app.db import get_db
from app.deps import OffsetPagination
from app.models import Feuille, Fichier
from app.schemas.common import PaginatedOffset
from app.schemas.fichiers import Fichier as FichierSchema, Feuille as FeuilleSchema
from app.schemas.referentiels import Source as SourceSchema

router = APIRouter(
    tags=["Fichiers"],
    dependencies=[Depends(require_api_key)],
)


# =====================================================================
# FICHIERS
# =====================================================================
@router.get(
    "/fichiers",
    response_model=PaginatedOffset[FichierSchema],
    summary="Liste des fichiers",
)
def list_fichiers(
    id_source: int | None = Query(None),
    statut: Literal["en_attente", "en_cours", "ingere", "partiel", "erreur"]
    | None = Query(None),
    pagination: OffsetPagination = Depends(),
    db: Session = Depends(get_db),
):
    stmt = select(Fichier).options(selectinload(Fichier.source))
    if id_source is not None:
        stmt = stmt.where(Fichier.id_source == id_source)
    if statut is not None:
        stmt = stmt.where(Fichier.statut == statut)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(
        stmt.order_by(Fichier.date_reception.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    ).all()

    return PaginatedOffset(
        data=[
            FichierSchema(
                id_fichier=f.id_fichier,
                nom_fichier_original=f.nom_fichier_original,
                source=SourceSchema.model_validate(f.source),
                hash_sha256=f.hash_sha256,
                taille_octets=f.taille_octets,
                date_reception=f.date_reception,
                date_ingestion=f.date_ingestion,
                statut=f.statut,
                nb_feuilles=f.nb_feuilles,
                nb_lignes_total=f.nb_lignes_total,
                est_reingestion=f.est_reingestion,
                commentaire=f.commentaire,
            )
            for f in rows
        ],
        pagination=pagination.to_response(total=total),
    )


@router.get(
    "/fichiers/{id}",
    response_model=FichierSchema,
    summary="Détail d'un fichier",
)
def get_fichier(id: int, db: Session = Depends(get_db)):
    f = db.scalar(
        select(Fichier)
        .where(Fichier.id_fichier == id)
        .options(selectinload(Fichier.source))
    )
    if f is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fichier {id} introuvable",
        )
    return FichierSchema(
        id_fichier=f.id_fichier,
        nom_fichier_original=f.nom_fichier_original,
        source=SourceSchema.model_validate(f.source),
        hash_sha256=f.hash_sha256,
        taille_octets=f.taille_octets,
        date_reception=f.date_reception,
        date_ingestion=f.date_ingestion,
        statut=f.statut,
        nb_feuilles=f.nb_feuilles,
        nb_lignes_total=f.nb_lignes_total,
        est_reingestion=f.est_reingestion,
        commentaire=f.commentaire,
    )


# =====================================================================
# FEUILLES
# =====================================================================
@router.get(
    "/fichiers/{id}/feuilles",
    response_model=PaginatedOffset[FeuilleSchema],
    summary="Feuilles d'un fichier",
)
def list_feuilles_fichier(
    id: int,
    pagination: OffsetPagination = Depends(),
    db: Session = Depends(get_db),
):
    # Vérifie que le fichier existe
    fichier = db.get(Fichier, id)
    if fichier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fichier {id} introuvable",
        )

    stmt = select(Feuille).where(Feuille.id_fichier == id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(
        stmt.order_by(Feuille.index_feuille)
        .offset(pagination.offset)
        .limit(pagination.limit)
    ).all()

    return PaginatedOffset(
        data=[FeuilleSchema.model_validate(r) for r in rows],
        pagination=pagination.to_response(total=total),
    )