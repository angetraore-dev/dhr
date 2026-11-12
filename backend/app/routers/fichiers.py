"""
Router des fichiers et feuilles.
"""
from __future__ import annotations

import logging
from typing import Literal

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth import JWTUser, require_api_key, require_jwt
from app.db import SessionLocal, get_db
from app.deps import OffsetPagination
from app.models import Feuille, Fichier, IngestionRun
from app.schemas.common import PaginatedOffset
from app.schemas.fichiers import (
    Feuille as FeuilleSchema,
)
from app.schemas.fichiers import (
    Fichier as FichierSchema,
)
from app.schemas.fichiers import (
    MappingProposalFeuille,
    MappingValidation,
)
from app.schemas.ingestion import IngestionRun as IngestionRunSchema
from app.schemas.referentiels import Source as SourceSchema
from app.services.mapping import (
    proposer_mapping_fichier,
    sauvegarder_mapping_feuille,
)
from app.services.run import creer_run, executer_pipeline
from app.services.upload import uploader_fichier

logger = logging.getLogger("dhr.fichiers")

router = APIRouter(tags=["Fichiers"])


# =====================================================================
# FICHIERS
# =====================================================================
@router.get(
    "/fichiers",
    response_model=PaginatedOffset[FichierSchema],
    summary="Liste des fichiers",
    dependencies=[Depends(require_api_key)],
)
def list_fichiers(
    id_source: int | None = Query(None),
    statut: Literal["en_attente", "en_cours", "ingere", "partiel", "erreur"] | None = Query(None),
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
    dependencies=[Depends(require_api_key)],
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
    dependencies=[Depends(require_api_key)],
)
def list_feuilles_fichier(
    id: int,
    pagination: OffsetPagination = Depends(),
    db: Session = Depends(get_db),
):
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


# =====================================================================
# MAPPING
# =====================================================================
@router.get(
    "/fichiers/{id}/mapping-proposal",
    response_model=list[MappingProposalFeuille],
    summary="Proposition de mapping automatique",
    dependencies=[Depends(require_api_key)],
)
def get_mapping_proposal(id: int, db: Session = Depends(get_db)):
    try:
        return proposer_mapping_fichier(db, id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put(
    "/fichiers/{id}/mapping",
    response_model=MappingProposalFeuille,
    summary="Sauvegarde le mapping validé par l'utilisateur",
)
def put_mapping(
    id: int,
    payload: MappingValidation,
    id_feuille: int | None = Query(None, description="Feuille cible (défaut: première feuille)"),
    db: Session = Depends(get_db),
    user: JWTUser = Depends(require_jwt),
):
    fichier = db.get(Fichier, id)
    if fichier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Fichier {id} introuvable")

    if id_feuille is not None:
        feuille = db.get(Feuille, id_feuille)
        if feuille is None or feuille.id_fichier != id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feuille {id_feuille} introuvable pour le fichier {id}",
            )
    else:
        feuille = db.scalar(
            select(Feuille)
            .where(Feuille.id_fichier == id)
            .order_by(Feuille.index_feuille)
            .limit(1)
        )
        if feuille is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune feuille pour le fichier {id}",
            )

    try:
        result = sauvegarder_mapping_feuille(db, feuille.id_feuille, payload.colonnes)
        db.commit()
        return result
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


# =====================================================================
# UPLOAD
# =====================================================================
@router.post(
    "/fichiers",
    status_code=status.HTTP_201_CREATED,
    summary="Uploader un fichier (synchrone : analyse des feuilles)",
)
def upload_fichier(
    file: UploadFile = File(...),
    id_source: int = Form(...),
    commentaire: str | None = Form(None),
    force: bool = Query(False, description="Forcer la réingestion si le hash existe déjà"),
    db: Session = Depends(get_db),
    user: JWTUser = Depends(require_jwt),
):
    result = uploader_fichier(db, file, id_source, commentaire, force)
    db.commit()
    return result


# =====================================================================
# RUNS
# =====================================================================
def _valider_parametres_run(
    mode: str,
    limite_lignes: int | None,
    ligne_debut: int | None,
    ligne_fin: int | None,
) -> None:
    if mode == "complet" and any(x is not None for x in (limite_lignes, ligne_debut, ligne_fin)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="En mode 'complet', limite_lignes, ligne_debut et ligne_fin doivent être vides.",
        )
    if mode == "echantillon":
        if limite_lignes is None or limite_lignes <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="En mode 'echantillon', limite_lignes doit être un entier positif.",
            )
        if ligne_debut is not None or ligne_fin is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="En mode 'echantillon', ligne_debut et ligne_fin doivent être vides.",
            )
    if mode == "plage":
        if limite_lignes is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="En mode 'plage', limite_lignes doit être vide.",
            )
        if ligne_debut is None or ligne_fin is None or ligne_fin < ligne_debut:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="En mode 'plage', ligne_debut et ligne_fin sont requis avec ligne_fin >= ligne_debut.",
            )

@router.post(
    "/fichiers/{id}/runs",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Lancer une ingestion (asynchrone)",
)
def lancer_run(
    id: int,
    background_tasks: BackgroundTasks,
    mode: Literal["complet", "echantillon", "plage"] = Query("complet"),
    id_feuille: int | None = Query(None),
    limite_lignes: int | None = Query(None),
    ligne_debut: int | None = Query(None),
    ligne_fin: int | None = Query(None),
    db: Session = Depends(get_db),
    user: JWTUser = Depends(require_jwt),
):
    """
    Lance un run d'ingestion asynchrone.
    Le pipeline complet est exécuté en arrière-plan :
    1. Ingestion
    2. Rapprochement
    3. Consolidation
    Le client doit poller GET /runs/{id} pour suivre l'avancement.
    """
    _valider_parametres_run(mode, limite_lignes, ligne_debut, ligne_fin)

    try:
        run = creer_run(
            db,
            id,
            id_feuille=id_feuille,
            mode=mode,
            limite_lignes=limite_lignes,
            ligne_debut=ligne_debut,
            ligne_fin=ligne_fin,
        )
        db.commit()
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


    def _pipeline() -> None:
        db2 = SessionLocal()
        try:
            executer_pipeline(db2, run.id_run)
            db2.commit()
        except Exception as e:
            logger.exception("Erreur pipeline run %s : %s", run.id_run, e)
            # executer_pipeline a déjà fait son rollback et passé run/fichier en 'erreur'.
            # On commit pour sauvegarder ces statuts d'erreur en base !
            db2.commit()
        finally:
            db2.close()

    background_tasks.add_task(_pipeline)

    return {
        "id_run": run.id_run,
        "id_fichier": id,
        "statut": "en_cours",
        "started_at": run.started_at.isoformat(),
        "poll_url": f"/v1/runs/{run.id_run}",
    }

@router.get(
    "/fichiers/{id}/runs",
    response_model=PaginatedOffset[IngestionRunSchema],
    summary="Historique des runs d'un fichier",
    dependencies=[Depends(require_api_key)],
)
def list_runs_fichier(
    id: int,
    pagination: OffsetPagination = Depends(),
    db: Session = Depends(get_db),
):
    fichier = db.get(Fichier, id)
    if fichier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fichier {id} introuvable",
        )

    stmt = select(IngestionRun).where(IngestionRun.id_fichier == id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(
        stmt.order_by(IngestionRun.id_run.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    ).all()

    return PaginatedOffset(
        data=[IngestionRunSchema.model_validate(r) for r in rows],
        pagination=pagination.to_response(total=total),
    )
