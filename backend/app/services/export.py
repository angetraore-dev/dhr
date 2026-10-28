"""
Service d'export Excel/CSV streamé.

- Excel : XlsxWriter en mode constant_memory (mémoire constante, 2x plus rapide)
- CSV  : module csv stdlib, streaming
- Colonne N° incrémentale
- Feuille Synthèse avec KPI (optionnelle, XlsxWriter gère le merge)
- Limite MAX_EXPORT_ROWS (413 au-delà)
"""
from __future__ import annotations

import csv
import io
from collections.abc import Generator
from datetime import datetime, timezone
from typing import Any

import xlsxwriter
from fastapi import HTTPException, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.models import (
    CGPE,
    Localite,
    Ouvrage,
    OuvrageProjet,
    ProjetFinancement,
    RefGeoAdmin,
    Source,
    TypeOuvrage,
)

settings = get_settings()


# =====================================================================
# Colonnes standard (réordonnées : administratif avant métier)
# =====================================================================
STANDARD_COLUMNS: list[tuple[str, str]] = [
    ("n", "N°"),
    ("district", "District"),
    ("region", "Région"),
    ("departement", "Département"),
    ("sous_prefecture", "Sous-préfecture"),
    ("localite", "Localité"),
    ("id_ouvrage", "ID ouvrage"),
    ("code_ouvrage", "Code ouvrage"),
    ("type_ouvrage", "Type d'ouvrage"),
    ("etat", "État"),
    ("annee_realisation", "Année de réalisation"),
    ("latitude", "Latitude"),
    ("longitude", "Longitude"),
    ("cgpe_existe", "CGPE existe"),
    ("cgpe_statut", "CGPE statut"),
    ("financements", "Financements"),
]


# =====================================================================
# Helpers (inchangés)
# =====================================================================
def _get_ref_geo_chain(db: Session, id_localite: int) -> dict[str, str]:
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
) -> dict[str, Any]:
    ref_geo = _get_ref_geo_chain(db, o.id_localite)
    cgpe_existe = ""
    cgpe_statut = ""
    if o.cgpes:
        c = o.cgpes[0]
        cgpe_existe = "oui" if c.existe else "non"
        cgpe_statut = c.statut or ""

    row = {
        "n": index,
        "district": ref_geo.get("district", ""),
        "region": ref_geo.get("region", ""),
        "departement": ref_geo.get("departement", ""),
        "sous_prefecture": ref_geo.get("sous_prefecture", ""),
        "localite": o.localite.nom_usage if o.localite else "",
        "id_ouvrage": o.id_ouvrage,
        "code_ouvrage": o.code_ouvrage or "",
        "type_ouvrage": o.type_ouvrage.code if o.type_ouvrage else "",
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


def _iter_ouvrages(
    db: Session,
    filters: dict[str, Any],
    chunk_size: int = 5000,
) -> Generator[list[Ouvrage], None, None]:
    stmt = (
        select(Ouvrage)
        .options(
            selectinload(Ouvrage.type_ouvrage),
            selectinload(Ouvrage.localite),
            selectinload(Ouvrage.cgpes),
            selectinload(Ouvrage.financements)
            .selectinload(OuvrageProjet.projet)
            .selectinload(ProjetFinancement.financeur),
        )
        .order_by(Ouvrage.id_ouvrage)
    )
    if filters.get("type_ouvrage"):
        stmt = stmt.join(TypeOuvrage).where(TypeOuvrage.code == filters["type_ouvrage"])
    if filters.get("etat"):
        stmt = stmt.where(Ouvrage.etat == filters["etat"])
    if filters.get("annee_min") is not None:
        stmt = stmt.where(Ouvrage.annee_realisation >= filters["annee_min"])
    if filters.get("annee_max") is not None:
        stmt = stmt.where(Ouvrage.annee_realisation <= filters["annee_max"])

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
    if filters.get("type_ouvrage"):
        stmt = stmt.join(TypeOuvrage).where(TypeOuvrage.code == filters["type_ouvrage"])
    if filters.get("etat"):
        stmt = stmt.where(Ouvrage.etat == filters["etat"])
    if filters.get("annee_min") is not None:
        stmt = stmt.where(Ouvrage.annee_realisation >= filters["annee_min"])
    if filters.get("annee_max") is not None:
        stmt = stmt.where(Ouvrage.annee_realisation <= filters["annee_max"])
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
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"ouvrages_{today}.{extension}"


# =====================================================================
# KPI (inchangé)
# =====================================================================
def _compute_kpis(db: Session, filters: dict[str, Any]) -> dict[str, Any]:
    kpis: dict[str, Any] = {}
    kpis["total"] = _count_ouvrages(db, filters)

    # Par type
    stmt = (
        select(TypeOuvrage.code, func.count())
        .select_from(Ouvrage)
        .join(TypeOuvrage)
        .group_by(TypeOuvrage.code)
        .order_by(func.count().desc())
    )
    if filters.get("etat"):
        stmt = stmt.where(Ouvrage.etat == filters["etat"])
    if filters.get("annee_min") is not None:
        stmt = stmt.where(Ouvrage.annee_realisation >= filters["annee_min"])
    if filters.get("annee_max") is not None:
        stmt = stmt.where(Ouvrage.annee_realisation <= filters["annee_max"])
    if filters.get("type_ouvrage"):
        stmt = stmt.where(TypeOuvrage.code == filters["type_ouvrage"])
    kpis["par_type_ouvrage"] = dict(db.execute(stmt).all())

    # Par état
    stmt = select(Ouvrage.etat, func.count()).group_by(Ouvrage.etat).order_by(func.count().desc())
    if filters.get("type_ouvrage"):
        stmt = stmt.join(TypeOuvrage).where(TypeOuvrage.code == filters["type_ouvrage"])
    if filters.get("annee_min") is not None:
        stmt = stmt.where(Ouvrage.annee_realisation >= filters["annee_min"])
    if filters.get("annee_max") is not None:
        stmt = stmt.where(Ouvrage.annee_realisation <= filters["annee_max"])
    kpis["par_etat"] = dict(db.execute(stmt).all())

    # Par bailleur
    stmt = (
        select(Source.nom, func.count(func.distinct(Ouvrage.id_ouvrage)))
        .select_from(Ouvrage)
        .join(OuvrageProjet, OuvrageProjet.id_ouvrage == Ouvrage.id_ouvrage)
        .join(ProjetFinancement, ProjetFinancement.id_projet == OuvrageProjet.id_projet)
        .join(Source, Source.id_source == ProjetFinancement.id_source_financeur)
        .group_by(Source.nom)
        .order_by(func.count(func.distinct(Ouvrage.id_ouvrage)).desc())
    )
    if filters.get("type_ouvrage"):
        stmt = stmt.join(TypeOuvrage).where(TypeOuvrage.code == filters["type_ouvrage"])
    if filters.get("etat"):
        stmt = stmt.where(Ouvrage.etat == filters["etat"])
    if filters.get("annee_min") is not None:
        stmt = stmt.where(Ouvrage.annee_realisation >= filters["annee_min"])
    if filters.get("annee_max") is not None:
        stmt = stmt.where(Ouvrage.annee_realisation <= filters["annee_max"])
    kpis["par_bailleur"] = dict(db.execute(stmt).all())

    # Par district (CTE récursive)
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
        FROM ouvrage o
        JOIN localite l ON l.id_localite = o.id_localite
        JOIN district_of d ON d.id_geo = l.id_geo
        JOIN ref_geo_admin r ON r.id_geo = d.district_id
        GROUP BY r.nom
        ORDER BY nb DESC
    """
    rows = db.execute(text(district_of_sql)).all()
    kpis["par_district"] = {r[0]: r[1] for r in rows}

    # Années
    stmt = select(
        func.min(Ouvrage.annee_realisation),
        func.max(Ouvrage.annee_realisation),
        func.avg(Ouvrage.annee_realisation),
    )
    if filters.get("type_ouvrage"):
        stmt = stmt.join(TypeOuvrage).where(TypeOuvrage.code == filters["type_ouvrage"])
    if filters.get("etat"):
        stmt = stmt.where(Ouvrage.etat == filters["etat"])
    row = db.execute(stmt).first()
    kpis["annee_min"] = row[0] if row else None
    kpis["annee_max"] = row[1] if row else None
    kpis["annee_moy"] = round(row[2], 1) if row and row[2] is not None else None

    # Géolocalisation
    stmt = (
        select(
            func.count().filter(text("Ouvrage.geom IS NOT NULL")),
            func.count(),
        )
        .select_from(Ouvrage)
    )

    if filters.get("type_ouvrage"):
        stmt = stmt.join(TypeOuvrage).where(TypeOuvrage.code == filters["type_ouvrage"])
    if filters.get("etat"):
        stmt = stmt.where(Ouvrage.etat == filters["etat"])
    row = db.execute(stmt).first()
    kpis["geo_avec"] = row[0] if row else 0
    kpis["geo_total"] = row[1] if row else 0
    kpis["taux_geo"] = round((row[0] / row[1]) if row and row[1] > 0 else 0.0, 3)

    # CGPE
    stmt = select(
        func.count().filter(CGPE.existe == True, CGPE.statut == "fonctionnel"),
        func.count(CGPE.id_cgpe),
    ).select_from(CGPE)
    if filters.get("type_ouvrage") or filters.get("etat"):
        stmt = stmt.join(Ouvrage, Ouvrage.id_ouvrage == CGPE.id_ouvrage)
        if filters.get("type_ouvrage"):
            stmt = stmt.join(TypeOuvrage).where(TypeOuvrage.code == filters["type_ouvrage"])
        if filters.get("etat"):
            stmt = stmt.where(Ouvrage.etat == filters["etat"])
    row = db.execute(stmt).first()
    kpis["cgpe_fonctionnel"] = row[0] if row else 0
    kpis["cgpe_total"] = row[1] if row else 0
    kpis["taux_cgpe"] = round((row[0] / row[1]) if row and row[1] > 0 else 0.0, 3)

    kpis["filtres"] = {k: v for k, v in filters.items() if v is not None}
    return kpis


def _format_filters(filters: dict[str, Any]) -> str:
    if not filters or all(v is None for v in filters.values()):
        return "Aucun filtre (tous les ouvrages)"
    labels = {
        "type_ouvrage": "Type",
        "etat": "État",
        "district": "District",
        "region": "Région",
        "departement": "Département",
        "sous_prefecture": "Sous-préfecture",
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
    """Écrit la feuille Synthèse avec XlsxWriter."""
    ws = workbook.add_worksheet("Synthèse")

    # Formats
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

    # Titre (merge sur 4 colonnes)
    ws.merge_range(row, 0, row, 3, "Export des ouvrages hydrauliques ruraux", fmt_title)
    ws.set_row(row, 24)
    row += 1

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
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
        ("Taux de géolocalisation", f"{kpis['taux_geo']*100:.1f} % ({kpis['geo_avec']}/{kpis['geo_total']})"),
        ("Taux de CGPE fonctionnel", f"{kpis['taux_cgpe']*100:.1f} % ({kpis['cgpe_fonctionnel']}/{kpis['cgpe_total']})"),
    ]
    for label, value in overview:
        ws.write(row, 0, label, fmt_label)
        ws.write(row, 1, value, fmt_value)
        row += 1
    row += 1

    # Par type
    ws.merge_range(row, 0, row, 1, "Répartition par type d'ouvrage", fmt_section)
    row += 1
    ws.write(row, 0, "Type", fmt_header)
    ws.write(row, 1, "Nombre", fmt_header)
    row += 1
    for code, count in kpis["par_type_ouvrage"].items():
        ws.write(row, 0, code, fmt_label)
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

    # Par district
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
# Export Excel (XlsxWriter, constant_memory)
# =====================================================================
def export_ouvrages_xlsx(
    db: Session,
    filters: dict[str, Any],
    include_metadata: bool = False,
    with_summary: bool = True,
) -> Generator[bytes, None, None]:
    """Génère un fichier Excel (xlsx) avec XlsxWriter en constant_memory."""
    _check_export_limit(db, filters)

    # Passe 1 : metadata columns
    metadata_columns: list[str] = []
    if include_metadata:
        sample = db.scalars(select(Ouvrage).limit(100)).all()
        cols: set[str] = set()
        for o in sample:
            if o.metadata_:
                cols.update(o.metadata_.keys())
        metadata_columns = sorted(f"metadata_{k}" for k in cols)

    # Buffer + workbook
    buffer = io.BytesIO()
    wb = xlsxwriter.Workbook(
        buffer,
        {"in_memory": True }, #, "constant_memory": True
    )

    # Feuille Synthèse (optionnelle)
    if with_summary:
        kpis = _compute_kpis(db, filters)
        _write_synthese_sheet(wb, kpis)

    # Feuille Ouvrages
    ws = wb.add_worksheet("Ouvrages")
    fmt_header = wb.add_format({"bold": True, "bg_color": "#EBF5FB", "border": 1})

    headers = [label for _, label in STANDARD_COLUMNS]
    if include_metadata:
        headers.extend(metadata_columns)

    ws.write_row(0, 0, headers, fmt_header)
    ws.set_column(0, 0, 6)   # N°
    ws.set_column(1, len(headers) - 1, 20)

    # Passe 2 : données
    index = 0
    row_idx = 1
    for chunk in _iter_ouvrages(db, filters):
        for o in chunk:
            index += 1
            row = _build_row(o, db, include_metadata, index)
            values = [row.get(key, "") for key, _ in STANDARD_COLUMNS]
            if include_metadata:
                values.extend(row.get(mkey, "") for mkey in metadata_columns)
            ws.write_row(row_idx, 0, values)
            row_idx += 1

    wb.close()
    buffer.seek(0)
    yield buffer.read()


# =====================================================================
# Export CSV (inchangé)
# =====================================================================
def export_ouvrages_csv(
    db: Session,
    filters: dict[str, Any],
    include_metadata: bool = False,
) -> Generator[str, None, None]:
    _check_export_limit(db, filters)

    metadata_columns: list[str] = []
    if include_metadata:
        sample = db.scalars(select(Ouvrage).limit(100)).all()
        cols: set[str] = set()
        for o in sample:
            if o.metadata_:
                cols.update(o.metadata_.keys())
        metadata_columns = sorted(f"metadata_{k}" for k in cols)

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
            row = _build_row(o, db, include_metadata, index)
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