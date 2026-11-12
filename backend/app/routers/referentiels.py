"""
Router des référentiels : sources, référentiel géo, localités.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload

from app.auth import require_api_key
from app.db import get_db
from app.deps import OffsetPagination
from app.models import Localite, RefGeoAdmin, Source
from app.schemas.common import PaginatedOffset
from app.schemas.referentiels import (
    Localite as LocaliteSchema,
)
from app.schemas.referentiels import (
    LocaliteResume,
)
from app.schemas.referentiels import (
    RefGeoAdmin as RefGeoAdminSchema,
)
from app.schemas.referentiels import (
    Source as SourceSchema,
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
) -> PaginatedOffset[SourceSchema]:
    total = db.scalar(select(func.count()).select_from(Source))
    rows = db.scalars(
        select(Source).order_by(Source.nom).offset(pagination.offset).limit(pagination.limit)
    ).all()
    return PaginatedOffset(
        data=[SourceSchema.model_validate(r) for r in rows],
        pagination=pagination.to_response(total=total),
    )


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
) -> PaginatedOffset[RefGeoAdminSchema]:
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

    # Chargement groupé des parents (évite le N+1)
    parent_ids = {r.parent_id for r in rows if r.parent_id is not None}
    parents_map: dict[int, RefGeoAdmin] = {}
    if parent_ids:
        parents = db.scalars(
            select(RefGeoAdmin).where(RefGeoAdmin.id_geo.in_(parent_ids))
        ).all()
        parents_map = {p.id_geo: p for p in parents}

    result = []
    for r in rows:
        parent = None
        if r.parent_id is not None and r.parent_id in parents_map:
            p = parents_map[r.parent_id]
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
def get_ref_geo_chemin(id: int, db: Session = Depends(get_db)) -> list[RefGeoAdminSchema]:
    """Remonte la hiérarchie en une seule requête (CTE récursive).

    Remplace l'ancienne boucle `while db.get(...)` qui faisait N requêtes
    (une par niveau). La CTE fait 1 requête, quel que soit le nombre de niveaux.
    """
    # CTE récursive : on part du nœud cible, on remonte jusqu'au district.
    # L'ordre final est district → localité (depth décroissant).
    sql = text("""
        WITH RECURSIVE chain AS (
            SELECT id_geo, niveau, nom, parent_id, code_officiel, type_localite,
                   0 AS depth
            FROM ref_geo_admin
            WHERE id_geo = :id_geo

            UNION ALL

            SELECT p.id_geo, p.niveau, p.nom, p.parent_id,
                   p.code_officiel, p.type_localite,
                   c.depth + 1
            FROM ref_geo_admin p
            JOIN chain c ON c.parent_id = p.id_geo
        )
        SELECT id_geo, niveau, nom, parent_id, code_officiel, type_localite
        FROM chain
        ORDER BY depth DESC
    """)

    rows = db.execute(sql, {"id_geo": id}).all()
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ref_geo_admin {id} introuvable",
        )

    return [
        RefGeoAdminSchema(
            id_geo=r.id_geo,
            niveau=r.niveau,
            nom=r.nom,
            code_officiel=r.code_officiel,
            type_localite=r.type_localite,
            parent=None,
        )
        for r in rows
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
) -> PaginatedOffset[LocaliteResume]:
    stmt = select(Localite)
    if id_geo is not None:
        stmt = stmt.where(Localite.id_geo == id_geo)
    if q:
        stmt = stmt.where(
            func.unaccent(Localite.nom_usage).ilike(func.unaccent(f"%{q}%"))
        )

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
) -> LocaliteSchema:
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

    geom_centre = None
    if loc.latitude_centre is not None and loc.longitude_centre is not None:
        geom_centre = {
            "type": "Point",
            "coordinates": [loc.longitude_centre, loc.latitude_centre],
        }

    return LocaliteSchema(
        id_localite=loc.id_localite,
        nom_usage=loc.nom_usage,
        latitude_centre=loc.latitude_centre,
        longitude_centre=loc.longitude_centre,
        geom_centre=geom_centre,
        alias=[a.alias for a in loc.alias],
        metadata=loc.metadata_ if include == "metadata" else None,
    )
