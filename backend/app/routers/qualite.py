"""
Router qualité : tableau de bord d'ingestion par fichier.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.db import get_db
from app.models import Feuille, Fichier, LigneIngeree, Source
from app.schemas.ouvrages import QualiteFichier, QualiteStats

router = APIRouter(
    tags=["Qualité"],
    dependencies=[Depends(require_api_key)],
)


@router.get(
    "/qualite/fichiers/{id}",
    response_model=QualiteFichier,
    summary="Tableau de bord qualité d'un fichier",
)
def qualite_fichier(id: int, db: Session = Depends(get_db)):
    f = db.get(Fichier, id)
    if f is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fichier {id} introuvable",
        )

    source = db.get(Source, f.id_source)
    source_nom = source.nom if source else "?"

    # Compte par statut qualité (jointure sur Feuille)
    stmt = (
        select(LigneIngeree.statut_qualite, func.count())
        .join(Feuille, LigneIngeree.id_feuille == Feuille.id_feuille)
        .where(Feuille.id_fichier == id)
        .group_by(LigneIngeree.statut_qualite)
    )
    counts = dict(db.execute(stmt).all())

    stats = QualiteStats(
        ok=counts.get("ok", 0),
        localite_non_resolue=counts.get("localite_non_resolue", 0),
        geom_invalide=counts.get("geom_invalide", 0),
        type_ouvrage_inconnu=counts.get("type_ouvrage_inconnu", 0),
        rejete=counts.get("rejete", 0),
        doublon_suspect=counts.get("doublon_suspect", 0),
    )

    total_lignes = sum(counts.values())
    taux = stats.ok / total_lignes if total_lignes > 0 else 0.0

    return QualiteFichier(
        id_fichier=f.id_fichier,
        nom_fichier=f.nom_fichier_original,
        source=source_nom,
        statut=f.statut,
        nb_lignes_total=f.nb_lignes_total,
        qualite=stats,
        taux_reussite=round(taux, 3),
    )