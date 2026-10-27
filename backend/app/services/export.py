"""
Service d'export Excel/CSV streamé.

Contraintes :
- Streaming obligatoire (jamais de chargement complet en RAM)
- Limite MAX_EXPORT_ROWS (413 au-delà)
- Mêmes filtres que GET /ouvrages
- Colonnes standard + colonnes dynamiques depuis metadata (si include=metadata)
"""
from __future__ import annotations

import csv
import io
from collections.abc import Generator
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font
from sqlalchemy import func, select
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
# Colonnes standard
# =====================================================================
STANDARD_COLUMNS: list[tuple[str, str]] = [
    ("id_ouvrage", "ID ouvrage"),
    ("code_ouvrage", "Code ouvrage"),
    ("type_ouvrage", "Type d'ouvrage"),
    ("etat", "État"),
    ("annee_realisation", "Année de réalisation"),
    ("district", "District"),
    ("region", "Région"),
    ("departement", "Département"),
    ("sous_prefecture", "Sous-préfecture"),
    ("localite", "Localité"),
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
    """
    Récupère la chaîne administrative (district, region, departement,
    sous_prefecture) pour une localité donnée.
    """
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
    """Concatène les financements : 'Projet A (BAD, principal); Projet B (ETAT_CI, co_financement)'."""
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
) -> dict[str, Any]:
    """Construit un dict {clé: valeur} pour un ouvrage."""
    ref_geo = _get_ref_geo_chain(db, o.id_localite)

    # CGPE (premier trouvé)
    cgpe_existe = ""
    cgpe_statut = ""
    if o.cgpes:
        c = o.cgpes[0]
        cgpe_existe = "oui" if c.existe else "non"
        cgpe_statut = c.statut or ""

    row = {
        "id_ouvrage": o.id_ouvrage,
        "code_ouvrage": o.code_ouvrage or "",
        "type_ouvrage": o.type_ouvrage.code if o.type_ouvrage else "",
        "etat": o.etat,
        "annee_realisation": o.annee_realisation or "",
        "district": ref_geo.get("district", ""),
        "region": ref_geo.get("region", ""),
        "departement": ref_geo.get("departement", ""),
        "sous_prefecture": ref_geo.get("sous_prefecture", ""),
        "localite": o.localite.nom_usage if o.localite else "",
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
    """
    Itère sur les ouvrages par chunks de chunk_size.
    Évite de tout charger en RAM.
    """
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

    # Filtres
    if filters.get("type_ouvrage"):
        stmt = stmt.join(TypeOuvrage).where(
            TypeOuvrage.code == filters["type_ouvrage"]
        )
    if filters.get("etat"):
        stmt = stmt.where(Ouvrage.etat == filters["etat"])
    if filters.get("annee_min") is not None:
        stmt = stmt.where(Ouvrage.annee_realisation >= filters["annee_min"])
    if filters.get("annee_max") is not None:
        stmt = stmt.where(Ouvrage.annee_realisation <= filters["annee_max"])

    # Streaming
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
    """Compte le nombre d'ouvrages correspondant aux filtres."""
    stmt = select(func.count()).select_from(Ouvrage)

    if filters.get("type_ouvrage"):
        stmt = stmt.join(TypeOuvrage).where(
            TypeOuvrage.code == filters["type_ouvrage"]
        )
    if filters.get("etat"):
        stmt = stmt.where(Ouvrage.etat == filters["etat"])
    if filters.get("annee_min") is not None:
        stmt = stmt.where(Ouvrage.annee_realisation >= filters["annee_min"])
    if filters.get("annee_max") is not None:
        stmt = stmt.where(Ouvrage.annee_realisation <= filters["annee_max"])

    return db.scalar(stmt) or 0


def _check_export_limit(db: Session, filters: dict[str, Any]) -> None:
    """Vérifie que le nombre d'ouvrages ne dépasse pas MAX_EXPORT_ROWS."""
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
    """Génère un nom de fichier daté."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"ouvrages_{today}.{extension}"


# =====================================================================
# Export Excel (streamé)
# =====================================================================
def export_ouvrages_xlsx(
    db: Session,
    filters: dict[str, Any],
    include_metadata: bool = False,
) -> Generator[bytes, None, None]:
    """
    Génère un fichier Excel (xlsx) streamé.
    Utilise openpyxl en mode write_only pour ne pas charger tout en RAM.
    """
    _check_export_limit(db, filters)

    wb = Workbook(write_only=True)
    ws = wb.create_sheet(title="Ouvrages")

    # En-têtes (figés)
    headers = [label for _, label in STANDARD_COLUMNS]

    # Colonnes metadata dynamiques (on les découvre au premier chunk)
    metadata_columns: list[str] = []

    # Ligne d'en-tête (écrite après découverte des metadata_columns,
    # donc on la garde en mémoire)
    header_written = False

    for chunk in _iter_ouvrages(db, filters):
        for o in chunk:
            row = _build_row(o, db, include_metadata)

            # Au premier ouvrage, on découvre les colonnes metadata
            if not header_written:
                if include_metadata:
                    metadata_columns = sorted(
                        k for k in row.keys() if k.startswith("metadata_")
                    )
                    headers.extend(metadata_columns)

                # Écrit la ligne d'en-tête
                header_cells = []
                for label in headers:
                    cell = WriteOnlyCell(ws, value=label)
                    cell.font = Font(bold=True)
                    header_cells.append(cell)
                ws.append(header_cells)
                header_written = True

            # Écrit la ligne de données
            values = []
            for key, _ in STANDARD_COLUMNS:
                values.append(row.get(key, ""))
            for mkey in metadata_columns:
                values.append(row.get(mkey, ""))
            ws.append(values)

    # Si aucun ouvrage, on écrit quand même l'en-tête standard
    if not header_written:
        header_cells = []
        for label in headers:
            cell = WriteOnlyCell(ws, value=label)
            cell.font = Font(bold=True)
            header_cells.append(cell)
        ws.append(header_cells)

    # Streaming via un buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    yield buffer.read()


# =====================================================================
# Export CSV (streamé)
# =====================================================================
def export_ouvrages_csv(
    db: Session,
    filters: dict[str, Any],
    include_metadata: bool = False,
) -> Generator[str, None, None]:
    """
    Génère un fichier CSV (UTF-8, séparateur ';') streamé.
    """
    _check_export_limit(db, filters)

    headers = [label for _, label in STANDARD_COLUMNS]
    metadata_columns: list[str] = []
    header_written = False

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_MINIMAL)

    for chunk in _iter_ouvrages(db, filters):
        for o in chunk:
            row = _build_row(o, db, include_metadata)

            if not header_written:
                if include_metadata:
                    metadata_columns = sorted(
                        k for k in row.keys() if k.startswith("metadata_")
                    )
                    headers.extend(metadata_columns)
                writer.writerow(headers)
                header_written = True

            values = []
            for key, _ in STANDARD_COLUMNS:
                values.append(row.get(key, ""))
            for mkey in metadata_columns:
                values.append(row.get(mkey, ""))
            writer.writerow(values)

            # Flush toutes les 100 lignes
            if buffer.tell() > 10_000:
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

    if not header_written:
        writer.writerow(headers)

    # Flush final
    if buffer.tell() > 0:
        yield buffer.getvalue()


def filename_xlsx() -> str:
    return _filename("xlsx")


def filename_csv() -> str:
    return _filename("csv")