"""
Service d'export Excel/CSV streamé.

- Excel : XlsxWriter en mode in_memory (export borné à MAX_EXPORT_ROWS)
- CSV  : module csv stdlib, streaming
- Colonne N° incrémentale
- Feuille Synthèse avec KPI (optionnelle, XlsxWriter gère le merge)
- Limite MAX_EXPORT_ROWS (413 au-delà)

Aligné sur la Bible § 4.3.4 et § 5.4.4 :
- Pas de `type_ouvrage` legacy.
- 3 champs distincts : nature_ouvrage, type_alimentation, realisation_par.
- Filtres : region, departement, sous_prefecture, localite, bailleur,
  annee_min, annee_max, nature_ouvrage, type_alimentation, realisation_par, etat.
- Pas de filtre `district` (réforme territoriale).
- KPI `par_district` conservé dans la Synthèse (information utile DHR).
"""
from __future__ import annotations

import csv
import io
from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any

import xlsxwriter
from fastapi import HTTPException, status
from sqlalchemy import exists, func, select, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session, aliased, selectinload

from app.config import get_settings
from app.models import (
    CGPE,
    Localite,
    Ouvrage,
    OuvrageProjet,
    ProjetFinancement,
    RefGeoAdmin,
    Source,
)

settings = get_settings()


# =====================================================================
# Colonnes standard
# =====================================================================
STANDARD_COLUMNS: list[tuple[str, str]] = [
    ("n", "N°"),
    ("region", "Région"),
    ("departement", "Département"),
    ("sous_prefecture", "Sous-préfecture"),
    ("localite", "Localité"),
    ("id_ouvrage", "ID ouvrage"),
    ("code_ouvrage", "Code ouvrage"),
    ("nature_ouvrage", "Nature (Puits/Forage)"),
    ("type_alimentation", "Alimentation (PMH/HVA/PEA/HV)"),
    ("realisation_par", "Réalisation (Public/Privé)"),
    ("etat", "État"),
    ("annee_realisation", "Année de réalisation"),
    ("latitude", "Latitude"),
    ("longitude", "Longitude"),
    ("cgpe_existe", "CGPE existe"),
    ("cgpe_statut", "CGPE statut"),
    ("financements", "Financements"),
]


# =====================================================================
# Helpers
# =====================================================================
def _get_ref_geo_chain(db: Session, id_localite: int) -> dict[str, str]:
    """Remonte la hiérarchie administrative depuis une localité."""
    localite = db.get(Localite, id_localite)
    if localite is None:
        return {}
    result: dict[str, str] = {}
    current = db.get(RefGeoAdmin, localite.id_geo)
    while current is not None:
        if current.niveau == "sous_prefecture":
            result["sous_prefecture"] = current.nom
        elif current.niveau == "departement":
            result["departement"] = current.nom
        elif current.niveau == "region":
            result["region"] = current.nom
        elif current.niveau == "district":
            result["district"] = current.nom
        if current.parent_id is None:
            break
        current = db.get(RefGeoAdmin, current.parent_id)
    return result


def _format_financements(financements: list[OuvrageProjet]) -> str:
    parts = []
    for op in financements:
        if op.projet is None:
            continue
        bailleur = op.projet.financeur.nom if op.projet.financeur else "?"
        parts.append(f"{op.projet.nom_projet} ({bailleur}, {op.role_financement})")
    return "; ".join(parts)


def _build_row(
    o: Ouvrage,
    db: Session,
    include_metadata: bool,
    index: int,
    geo_cache: dict[int, dict[str, str]],
) -> dict[str, Any]:
    """Construit une ligne d'export à partir d'un ouvrage avec cache géographique."""
    if o.id_localite not in geo_cache:
        geo_cache[o.id_localite] = _get_ref_geo_chain(db, o.id_localite)
    ref_geo = geo_cache[o.id_localite]

    cgpe_existe = ""
    cgpe_statut = ""
    if o.cgpes:
        c = o.cgpes[0]
        cgpe_existe = "oui" if c.existe else "non"
        cgpe_statut = c.statut or ""

    row = {
        "n": index,
        "region": ref_geo.get("region", ""),
        "departement": ref_geo.get("departement", ""),
        "sous_prefecture": ref_geo.get("sous_prefecture", ""),
        "localite": o.localite.nom_usage if o.localite else "",
        "id_ouvrage": o.id_ouvrage,
        "code_ouvrage": o.code_ouvrage or "",
        "nature_ouvrage": o.nature_ouvrage or "",
        "type_alimentation": o.type_alimentation or "",
        "realisation_par": o.realisation_par or "",
        "etat": o.etat,
        "annee_realisation": o.annee_realisation or "",
        "latitude": o.latitude_decimal if o.latitude_decimal is not None else "",
        "longitude": o.longitude_decimal if o.longitude_decimal is not None else "",
        "cgpe_existe": cgpe_existe,
        "cgpe_statut": cgpe_statut,
        "financements": _format_financements(o.financements),
    }
    if include_metadata and o.metadata_:
        for k, v in o.metadata_.items():
            row[f"metadata_{k}"] = v
    return row


# =====================================================================
# Filtres communs
# =====================================================================
def _apply_common_filters(stmt, filters: dict[str, Any]):
    """Applique tous les filtres (métier, année, géo, bailleur) conformes à Bible § 4.3.4."""
    if filters.get("nature_ouvrage"):
        stmt = stmt.where(Ouvrage.nature_ouvrage == filters["nature_ouvrage"])
    if filters.get("type_alimentation"):
        stmt = stmt.where(Ouvrage.type_alimentation == filters["type_alimentation"])
    if filters.get("realisation_par"):
        stmt = stmt.where(Ouvrage.realisation_par == filters["realisation_par"])
    if filters.get("etat"):
        stmt = stmt.where(Ouvrage.etat == filters["etat"])
    if filters.get("annee_min") is not None:
        stmt = stmt.where(Ouvrage.annee_realisation >= filters["annee_min"])
    if filters.get("annee_max") is not None:
        stmt = stmt.where(Ouvrage.annee_realisation <= filters["annee_max"])

    # Filtres géographiques
    if any(filters.get(k) for k in ("region", "departement", "sous_prefecture", "localite")):
        rg_loc = aliased(RefGeoAdmin)
        rg_sp = aliased(RefGeoAdmin)
        rg_dep = aliased(RefGeoAdmin)
        rg_reg = aliased(RefGeoAdmin)

        stmt = (
            stmt.join(Localite, Ouvrage.id_localite == Localite.id_localite)
            .join(rg_loc, Localite.id_geo == rg_loc.id_geo)
            .outerjoin(rg_sp, rg_loc.parent_id == rg_sp.id_geo)
            .outerjoin(rg_dep, rg_sp.parent_id == rg_dep.id_geo)
            .outerjoin(rg_reg, rg_dep.parent_id == rg_reg.id_geo)
        )
        if filters.get("region"):
            stmt = stmt.where(rg_reg.nom == filters["region"])
        if filters.get("departement"):
            stmt = stmt.where(rg_dep.nom == filters["departement"])
        if filters.get("sous_prefecture"):
            stmt = stmt.where(rg_sp.nom == filters["sous_prefecture"])
        if filters.get("localite"):
            stmt = stmt.where(
                func.unaccent(Localite.nom_usage).ilike(func.unaccent(f"%{filters['localite']}%"))
            )

    # Filtre bailleur via EXISTS (évite les doublons)
    if filters.get("bailleur"):
        stmt = stmt.where(
            exists(
                select(OuvrageProjet.id_ouvrage)
                .join(ProjetFinancement, ProjetFinancement.id_projet == OuvrageProjet.id_projet)
                .join(Source, Source.id_source == ProjetFinancement.id_source_financeur)
                .where(OuvrageProjet.id_ouvrage == Ouvrage.id_ouvrage)
                .where(Source.nom == filters["bailleur"])
            )
        )

    return stmt


def _get_metadata_columns(db: Session, filters: dict[str, Any]) -> list[str]:
    """Récupère exhaustivement toutes les clés JSONB metadata sur les ouvrages filtrés."""
    stmt = (
        select(func.jsonb_object_keys(Ouvrage.metadata_))
        .select_from(Ouvrage)
        .distinct()
    )
    stmt = _apply_common_filters(stmt, filters)
    keys = db.scalars(stmt).all()
    return sorted(f"metadata_{k}" for k in keys)


# =====================================================================
# Itération / comptage
# =====================================================================
def _iter_ouvrages(
    db: Session,
    filters: dict[str, Any],
    chunk_size: int = 5000,
) -> Generator[list[Ouvrage], None, None]:
    stmt = (
        select(Ouvrage)
        .options(
            selectinload(Ouvrage.localite),
            selectinload(Ouvrage.cgpes),
            selectinload(Ouvrage.financements)
            .selectinload(OuvrageProjet.projet)
            .selectinload(ProjetFinancement.financeur),
        )
        .order_by(Ouvrage.id_ouvrage)
    )
    stmt = _apply_common_filters(stmt, filters)

    result = db.execute(stmt).yield_per(chunk_size)
    chunk: list[Ouvrage] = []
    for row in result:
        chunk.append(row[0])
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def _count_ouvrages(db: Session, filters: dict[str, Any]) -> int:
    stmt = select(func.count()).select_from(Ouvrage)
    stmt = _apply_common_filters(stmt, filters)
    return db.scalar(stmt) or 0


def _check_export_limit(db: Session, filters: dict[str, Any]) -> None:
    total = _count_ouvrages(db, filters)
    if total > settings.max_export_rows:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Trop de lignes à exporter ({total} > {settings.max_export_rows}). "
                "Affinez vos filtres."
            ),
        )


def _filename(extension: str) -> str:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    return f"ouvrages_{today}.{extension}"


# =====================================================================
# KPI (Synthèse)
# =====================================================================
def _compute_kpis(db: Session, filters: dict[str, Any]) -> dict[str, Any]:
    kpis: dict[str, Any] = {}
    kpis["total"] = _count_ouvrages(db, filters)

    # --- Par nature (remplace par_type_ouvrage) ---
    stmt = select(Ouvrage.nature_ouvrage, func.count()).select_from(Ouvrage)
    stmt = _apply_common_filters(stmt, filters)
    stmt = stmt.group_by(Ouvrage.nature_ouvrage).order_by(func.count().desc())
    kpis["par_nature"] = dict(db.execute(stmt).all())

    # --- Par alimentation ---
    stmt = select(Ouvrage.type_alimentation, func.count()).select_from(Ouvrage)
    stmt = _apply_common_filters(stmt, filters)
    stmt = stmt.group_by(Ouvrage.type_alimentation).order_by(func.count().desc())
    kpis["par_alimentation"] = dict(db.execute(stmt).all())

    # --- Par réalisation ---
    stmt = select(Ouvrage.realisation_par, func.count()).select_from(Ouvrage)
    stmt = _apply_common_filters(stmt, filters)
    stmt = stmt.group_by(Ouvrage.realisation_par).order_by(func.count().desc())
    kpis["par_realisation"] = dict(db.execute(stmt).all())

    # --- Par état ---
    stmt = select(Ouvrage.etat, func.count()).select_from(Ouvrage)
    stmt = _apply_common_filters(stmt, filters)
    stmt = stmt.group_by(Ouvrage.etat).order_by(func.count().desc())
    kpis["par_etat"] = dict(db.execute(stmt).all())

    # --- Par bailleur ---
    stmt = (
        select(Source.nom, func.count(func.distinct(Ouvrage.id_ouvrage)))
        .select_from(Ouvrage)
        .join(OuvrageProjet, OuvrageProjet.id_ouvrage == Ouvrage.id_ouvrage)
        .join(ProjetFinancement, ProjetFinancement.id_projet == OuvrageProjet.id_projet)
        .join(Source, Source.id_source == ProjetFinancement.id_source_financeur)
    )
    stmt = _apply_common_filters(stmt, filters)
    stmt = stmt.group_by(Source.nom).order_by(
        func.count(func.distinct(Ouvrage.id_ouvrage)).desc()
    )
    kpis["par_bailleur"] = dict(db.execute(stmt).all())

    # --- Par district (KPI conservé, pas un filtre UI) ---
    filtered_ouvrages_subq = _apply_common_filters(
        select(Ouvrage.id_ouvrage, Ouvrage.id_localite), filters
    ).subquery("filtered_o")

    district_of_sql = """
        WITH RECURSIVE district_of AS (
            SELECT id_geo, id_geo AS district_id
            FROM ref_geo_admin WHERE niveau = 'district'
            UNION ALL
            SELECT r.id_geo, d.district_id
            FROM ref_geo_admin r
            JOIN district_of d ON r.parent_id = d.id_geo
        )
        SELECT r.nom AS district, COUNT(*) AS nb
        FROM ({filtered_sql}) o
        JOIN localite l ON l.id_localite = o.id_localite
        JOIN district_of d ON d.id_geo = l.id_geo
        JOIN ref_geo_admin r ON r.id_geo = d.district_id
        GROUP BY r.nom
        ORDER BY nb DESC
    """
    compiled = filtered_ouvrages_subq.compile(dialect=postgresql.dialect())
    final_sql = district_of_sql.format(filtered_sql=str(compiled))
    rows = db.execute(text(final_sql), compiled.params).all()
    kpis["par_district"] = {r[0]: r[1] for r in rows}

    # --- Années ---
    stmt = select(
        func.min(Ouvrage.annee_realisation),
        func.max(Ouvrage.annee_realisation),
        func.avg(Ouvrage.annee_realisation),
    ).select_from(Ouvrage)
    stmt = _apply_common_filters(stmt, filters)
    row = db.execute(stmt).first()
    kpis["annee_min"] = row[0] if row else None
    kpis["annee_max"] = row[1] if row else None
    kpis["annee_moy"] = round(row[2], 1) if row and row[2] is not None else None

    # --- Géolocalisation ---
    stmt = (
        select(
            func.count().filter(text("ouvrage.geom IS NOT NULL")),
            func.count(),
        )
        .select_from(Ouvrage)
    )
    stmt = _apply_common_filters(stmt, filters)
    row = db.execute(stmt).first()
    kpis["geo_avec"] = row[0] if row else 0
    kpis["geo_total"] = row[1] if row else 0
    kpis["taux_geo"] = round(
        (row[0] / row[1]) if row and row[1] > 0 else 0.0, 3
    )

    # --- CGPE (correction is_(True)) ---
    stmt = (
        select(
            func.count().filter(CGPE.existe.is_(True), CGPE.statut == "fonctionnel"),
            func.count(CGPE.id_cgpe),
        )
        .select_from(CGPE)
        .join(Ouvrage, Ouvrage.id_ouvrage == CGPE.id_ouvrage)
    )
    stmt = _apply_common_filters(stmt, filters)
    row = db.execute(stmt).first()
    kpis["cgpe_fonctionnel"] = row[0] if row else 0
    kpis["cgpe_total"] = row[1] if row else 0
    kpis["taux_cgpe"] = round(
        (row[0] / row[1]) if row and row[1] > 0 else 0.0, 3
    )

    kpis["filtres"] = {k: v for k, v in filters.items() if v is not None}
    return kpis


def _format_filters(filters: dict[str, Any]) -> str:
    if not filters or all(v is None for v in filters.values()):
        return "Aucun filtre (tous les ouvrages)"
    labels = {
        "nature_ouvrage": "Nature",
        "type_alimentation": "Alimentation",
        "realisation_par": "Réalisation",
        "etat": "État",
        "region": "Région",
        "departement": "Département",
        "sous_prefecture": "Sous-préfecture",
        "localite": "Localité",
        "bailleur": "Bailleur",
        "annee_min": "Année ≥",
        "annee_max": "Année ≤",
    }
    parts = []
    for key, val in filters.items():
        if val is None:
            continue
        parts.append(f"{labels.get(key, key)}: {val}")
    return " ; ".join(parts)


# =====================================================================
# Feuille Synthèse (XlsxWriter)
# =====================================================================
def _write_synthese_sheet(workbook: xlsxwriter.Workbook, kpis: dict[str, Any]) -> None:
    ws = workbook.add_worksheet("Synthèse")

    fmt_title = workbook.add_format({
        "bold": True, "font_size": 14, "font_color": "#FFFFFF",
        "bg_color": "#2C3E50", "align": "center", "valign": "vcenter",
    })
    fmt_section = workbook.add_format({
        "bold": True, "font_size": 11, "font_color": "#2C3E50",
        "bg_color": "#D5DBDB",
    })
    fmt_header = workbook.add_format({
        "bold": True, "font_size": 10, "bg_color": "#EBF5FB", "border": 1,
    })
    fmt_label = workbook.add_format({"font_size": 10})
    fmt_value = workbook.add_format({"bold": True, "font_size": 10})

    row = 0

    ws.merge_range(row, 0, row, 3, "Export des ouvrages hydrauliques ruraux", fmt_title)
    ws.set_row(row, 24)
    row += 1

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    ws.write(row, 0, f"Date d'export : {now}", fmt_label)
    row += 1
    ws.write(row, 0, f"Filtres : {_format_filters(kpis['filtres'])}", fmt_label)
    row += 2

    # Vue d'ensemble
    ws.merge_range(row, 0, row, 3, "Vue d'ensemble", fmt_section)
    row += 1
    overview = [
        ("Nombre total d'ouvrages", kpis["total"]),
        ("Année min", kpis["annee_min"] if kpis["annee_min"] is not None else "—"),
        ("Année max", kpis["annee_max"] if kpis["annee_max"] is not None else "—"),
        ("Année moyenne", kpis["annee_moy"] if kpis["annee_moy"] is not None else "—"),
        ("Taux de géolocalisation",
         f"{kpis['taux_geo']*100:.1f} % ({kpis['geo_avec']}/{kpis['geo_total']})"),
        ("Taux de CGPE fonctionnel",
         f"{kpis['taux_cgpe']*100:.1f} % ({kpis['cgpe_fonctionnel']}/{kpis['cgpe_total']})"),
    ]
    for label, value in overview:
        ws.write(row, 0, label, fmt_label)
        ws.write(row, 1, value, fmt_value)
        row += 1
    row += 1

    # Par nature
    ws.merge_range(row, 0, row, 1, "Répartition par nature", fmt_section)
    row += 1
    ws.write(row, 0, "Nature", fmt_header)
    ws.write(row, 1, "Nombre", fmt_header)
    row += 1
    for nature, count in kpis["par_nature"].items():
        ws.write(row, 0, nature or "Inconnu", fmt_label)
        ws.write(row, 1, count, fmt_label)
        row += 1
    row += 1

    # Par alimentation
    ws.merge_range(row, 0, row, 1, "Répartition par alimentation", fmt_section)
    row += 1
    ws.write(row, 0, "Alimentation", fmt_header)
    ws.write(row, 1, "Nombre", fmt_header)
    row += 1
    for code, count in kpis["par_alimentation"].items():
        ws.write(row, 0, code or "Inconnu", fmt_label)
        ws.write(row, 1, count, fmt_label)
        row += 1
    row += 1

    # Par réalisation
    ws.merge_range(row, 0, row, 1, "Répartition par réalisation", fmt_section)
    row += 1
    ws.write(row, 0, "Réalisation", fmt_header)
    ws.write(row, 1, "Nombre", fmt_header)
    row += 1
    for realisation, count in kpis["par_realisation"].items():
        ws.write(row, 0, realisation or "Inconnu", fmt_label)
        ws.write(row, 1, count, fmt_label)
        row += 1
    row += 1

    # Par état
    ws.merge_range(row, 0, row, 1, "Répartition par état", fmt_section)
    row += 1
    ws.write(row, 0, "État", fmt_header)
    ws.write(row, 1, "Nombre", fmt_header)
    row += 1
    for etat, count in kpis["par_etat"].items():
        ws.write(row, 0, etat, fmt_label)
        ws.write(row, 1, count, fmt_label)
        row += 1
    row += 1

    # Par bailleur
    if kpis["par_bailleur"]:
        ws.merge_range(row, 0, row, 1, "Répartition par bailleur", fmt_section)
        row += 1
        ws.write(row, 0, "Bailleur", fmt_header)
        ws.write(row, 1, "Nombre d'ouvrages", fmt_header)
        row += 1
        for bailleur, count in kpis["par_bailleur"].items():
            ws.write(row, 0, bailleur, fmt_label)
            ws.write(row, 1, count, fmt_label)
            row += 1
        row += 1

    # Par district (KPI conservé)
    if kpis["par_district"]:
        ws.merge_range(row, 0, row, 1, "Répartition par district", fmt_section)
        row += 1
        ws.write(row, 0, "District", fmt_header)
        ws.write(row, 1, "Nombre d'ouvrages", fmt_header)
        row += 1
        for district, count in kpis["par_district"].items():
            ws.write(row, 0, district, fmt_label)
            ws.write(row, 1, count, fmt_label)
            row += 1

    ws.set_column(0, 0, 35)
    ws.set_column(1, 1, 25)



# =====================================================================
# Export Excel
# =====================================================================
def export_ouvrages_xlsx(
    db: Session,
    filters: dict[str, Any],
    include_metadata: bool = False,
    with_summary: bool = True,
) -> Generator[bytes, None, None]:
    _check_export_limit(db, filters)

    metadata_columns = _get_metadata_columns(db, filters) if include_metadata else []
    geo_cache: dict[int, dict[str, str]] = {}

    buffer = io.BytesIO()
    wb = xlsxwriter.Workbook(buffer, {"in_memory": True})

    if with_summary:
        kpis = _compute_kpis(db, filters)
        _write_synthese_sheet(wb, kpis)

    ws = wb.add_worksheet("Ouvrages")
    fmt_header = wb.add_format({"bold": True, "bg_color": "#EBF5FB", "border": 1})

    headers = [label for _, label in STANDARD_COLUMNS]
    if include_metadata:
        headers.extend(metadata_columns)

    ws.write_row(0, 0, headers, fmt_header)
    ws.set_column(0, 0, 6)
    ws.set_column(1, len(headers) - 1, 20)

    index = 0
    row_idx = 1
    for chunk in _iter_ouvrages(db, filters):
        for o in chunk:
            index += 1
            row = _build_row(o, db, include_metadata, index, geo_cache)
            values = [row.get(key, "") for key, _ in STANDARD_COLUMNS]
            if include_metadata:
                values.extend(row.get(mkey, "") for mkey in metadata_columns)
            ws.write_row(row_idx, 0, values)
            row_idx += 1

    wb.close()
    buffer.seek(0)
    yield buffer.read()


# =====================================================================
# Export CSV
# =====================================================================
def export_ouvrages_csv(
    db: Session,
    filters: dict[str, Any],
    include_metadata: bool = False,
) -> Generator[str, None, None]:
    _check_export_limit(db, filters)

    metadata_columns = _get_metadata_columns(db, filters) if include_metadata else []
    geo_cache: dict[int, dict[str, str]] = {}

    headers = [label for _, label in STANDARD_COLUMNS]
    if include_metadata:
        headers.extend(metadata_columns)

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)

    index = 0
    for chunk in _iter_ouvrages(db, filters):
        for o in chunk:
            index += 1
            row = _build_row(o, db, include_metadata, index, geo_cache)
            values = [row.get(key, "") for key, _ in STANDARD_COLUMNS]
            if include_metadata:
                values.extend(row.get(mkey, "") for mkey in metadata_columns)
            writer.writerow(values)
            if buffer.tell() > 10_000:
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

    if buffer.tell() > 0:
        yield buffer.getvalue()


def filename_xlsx() -> str:
    return _filename("xlsx")


def filename_csv() -> str:
    return _filename("csv")
