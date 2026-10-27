"""
Router des référentiels : sources, types d'ouvrage, référentiel géo, localités.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth import require_api_key
from app.db import get_db
from app.deps import OffsetPagination
from app.models import Localite, RefGeoAdmin, Source, TypeOuvrage
from app.schemas.common import PaginatedOffset
from app.schemas.referentiels import (
    Localite as LocaliteSchema,
    LocaliteResume,
    RefGeoAdmin as RefGeoAdminSchema,
    Source as SourceSchema,
    TypeOuvrage as TypeOuvrageSchema,
)

router = APIRouter(
    tags=["Référentiels"],
    dependencies=[Depends(require_api_key)],
)


# =====================================================================
# SOURCES
# =====================================================================
@router.get(
    "/sources",
    response_model=PaginatedOffset[SourceSchema],
    summary="Liste des sources",
)
def list_sources(
    pagination: OffsetPagination = Depends(),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count()).select_from(Source))
    rows = db.scalars(
        select(Source).order_by(Source.nom).offset(pagination.offset).limit(pagination.limit)
    ).all()
    return PaginatedOffset(
        data=[SourceSchema.model_validate(r) for r in rows],
        pagination=pagination.to_response(total=total),
    )


# =====================================================================
# TYPES D'OUVRAGE
# =====================================================================
@router.get(
    "/types-ouvrage",
    response_model=list[TypeOuvrageSchema],
    summary="Liste des types d'ouvrage",
)
def list_types_ouvrage(db: Session = Depends(get_db)):
    rows = db.scalars(select(TypeOuvrage).order_by(TypeOuvrage.code)).all()
    return [TypeOuvrageSchema.model_validate(r) for r in rows]


# =====================================================================
# RÉFÉRENTIEL GÉOGRAPHIQUE
# =====================================================================
@router.get(
    "/ref-geo",
    response_model=PaginatedOffset[RefGeoAdminSchema],
    summary="Nœuds du référentiel géographique administratif",
)
def list_ref_geo(
    niveau: Literal[
        "district", "region", "departement", "sous_prefecture", "localite"
    ]
    | None = Query(None),
    parent_id: int | None = Query(None),
    pagination: OffsetPagination = Depends(),
    db: Session = Depends(get_db),
):
    stmt = select(RefGeoAdmin)
    if niveau is not None:
        stmt = stmt.where(RefGeoAdmin.niveau == niveau)
    if parent_id is not None:
        stmt = stmt.where(RefGeoAdmin.parent_id == parent_id)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(
        stmt.order_by(RefGeoAdmin.niveau, RefGeoAdmin.nom)
        .offset(pagination.offset)
        .limit(pagination.limit)
    ).all()

    # Charge les parents (1 niveau) pour la réponse
    result = []
    for r in rows:
        parent = None
        if r.parent_id is not None:
            p = db.get(RefGeoAdmin, r.parent_id)
            if p is not None:
                parent = {"id_geo": p.id_geo, "niveau": p.niveau, "nom": p.nom}
        result.append(
            RefGeoAdminSchema(
                id_geo=r.id_geo,
                niveau=r.niveau,
                nom=r.nom,
                code_officiel=r.code_officiel,
                type_localite=r.type_localite,
                parent=parent,
            )
        )

    return PaginatedOffset(
        data=result,
        pagination=pagination.to_response(total=total),
    )


@router.get(
    "/ref-geo/{id}/chemin",
    response_model=list[RefGeoAdminSchema],
    summary="Chaîne hiérarchique district → localité",
)
def get_ref_geo_chemin(id: int, db: Session = Depends(get_db)):
    node = db.get(RefGeoAdmin, id)
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ref_geo_admin {id} introuvable",
        )

    chain: list[RefGeoAdmin] = []
    current = node
    while current is not None:
        chain.append(current)
        current = db.get(RefGeoAdmin, current.parent_id) if current.parent_id else None

    chain.reverse()  # district → localité
    return [
        RefGeoAdminSchema(
            id_geo=n.id_geo,
            niveau=n.niveau,
            nom=n.nom,
            code_officiel=n.code_officiel,
            type_localite=n.type_localite,
            parent=None,
        )
        for n in chain
    ]


# =====================================================================
# LOCALITÉS
# =====================================================================
@router.get(
    "/localites",
    response_model=PaginatedOffset[LocaliteResume],
    summary="Liste des localités",
)
def list_localites(
    id_geo: int | None = Query(None),
    q: str | None = Query(None, description="Recherche floue sur le nom"),
    pagination: OffsetPagination = Depends(),
    db: Session = Depends(get_db),
):
    stmt = select(Localite)
    if id_geo is not None:
        stmt = stmt.where(Localite.id_geo == id_geo)
    if q:
        stmt = stmt.where(Localite.nom_usage.ilike(f"%{q}%"))

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(
        stmt.order_by(Localite.nom_usage)
        .offset(pagination.offset)
        .limit(pagination.limit)
    ).all()

    return PaginatedOffset(
        data=[LocaliteResume.model_validate(r) for r in rows],
        pagination=pagination.to_response(total=total),
    )


@router.get(
    "/localites/{id}",
    response_model=LocaliteSchema,
    summary="Détail d'une localité",
)
def get_localite(
    id: int,
    include: Literal["metadata"] | None = Query(None),
    db: Session = Depends(get_db),
):
    loc = db.scalar(
        select(Localite)
        .where(Localite.id_localite == id)
        .options(selectinload(Localite.alias))
    )
    if loc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Localité {id} introuvable",
        )

    # Construit la réponse
    geom_centre = None
    if loc.geom_centre is not None:
        # Le champ geom_centre est une geometry PostGIS ; Pydantic attend GeoJSON
        # On utilise ST_AsGeoJSON via une requête séparée ou from_wkt
        pass

    data = LocaliteSchema(
        id_localite=loc.id_localite,
        nom_usage=loc.nom_usage,
        latitude_centre=loc.latitude_centre,
        longitude_centre=loc.longitude_centre,
        geom_centre=None,  # à compléter si besoin
        alias=[a.alias for a in loc.alias],
        metadata=loc.metadata_ if include == "metadata" else None,
    )
    return data