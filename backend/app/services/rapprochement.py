"""
Service de rapprochement des localités.

Pour chaque ligne_ingeree avec statut_qualite='ok' et id_localite NULL :
1. Normalise localite_brute
2. Cherche un exact match sur localite.nom_usage (normalisé)
3. Sinon, cherche dans localite_alias
4. Sinon, utilise pg_trgm (similarity > seuil)
5. Met à jour id_localite et statut_qualite
"""
from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models import Localite, LocaliteAlias, LigneIngeree

logger = logging.getLogger("dhr.rapprochement")


# =====================================================================
# Helpers
# =====================================================================
def _normaliser(texte: str | None) -> str:
    """Normalise un texte (minuscules, sans accents, espaces compactés)."""
    if texte is None:
        return ""
    texte = str(texte).strip().lower()
    texte = "".join(
        c for c in unicodedata.normalize("NFD", texte)
        if unicodedata.category(c) != "Mn"
    )
    texte = re.sub(r"[\s\-_]+", " ", texte).strip()
    return texte


def _resoudre_localite(
    db: Session,
    localite_brute: str,
    sous_prefecture_brute: str | None = None,
    seuil_trigram: float = 0.6,
) -> tuple[int | None, str]:
    """
    Résout une localité brute en id_localite.
    Retourne (id_localite, methode) où methode ∈ {'exact', 'alias', 'trigram', 'non_resolu'}.
    """
    if not localite_brute:
        return None, "vide"

    nom_norm = _normaliser(localite_brute)
    sous_pref_norm = _normaliser(sous_prefecture_brute) if sous_prefecture_brute else None

    # 1. Exact match sur nom_usage (via normalisation SQL)
    # On utilise unaccent + lower + regexp_replace
    exact_query = text("""
        SELECT id_localite
        FROM localite
        WHERE unaccent(lower(regexp_replace(nom_usage, '[\\s\\-_]+', ' ', 'g'))) = :nom_norm
        LIMIT 1
    """)
    row = db.execute(exact_query, {"nom_norm": nom_norm}).first()
    if row is not None:
        return row[0], "exact"

    # 2. Alias exact
    alias_query = text("""
        SELECT la.id_localite
        FROM localite_alias la
        WHERE unaccent(lower(regexp_replace(la.alias, '[\\s\\-_]+', ' ', 'g'))) = :nom_norm
        LIMIT 1
    """)
    row = db.execute(alias_query, {"nom_norm": nom_norm}).first()
    if row is not None:
        return row[0], "alias"

    # 3. Trigram similarity
    trigram_query = text("""
        SELECT id_localite, similarity(unaccent(lower(nom_usage)), :nom_norm) AS score
        FROM localite
        WHERE similarity(unaccent(lower(nom_usage)), :nom_norm) > :seuil
        ORDER BY score DESC
        LIMIT 1
    """)
    row = db.execute(
        trigram_query, {"nom_norm": nom_norm, "seuil": seuil_trigram}
    ).first()
    if row is not None:
        return row[0], "trigram"

    # 4. Pas de match
    return None, "non_resolu"


# =====================================================================
# Rapprochement principal
# =====================================================================
def rapprocher_lignes_run(
    db: Session,
    id_run: int,
    seuil_trigram: float = 0.6,
) -> dict[str, Any]:
    """
    Rapproche toutes les lignes du run.
    Met à jour id_localite et statut_qualite.
    """
    lignes = db.scalars(
        select(LigneIngeree).where(
            LigneIngeree.id_run == id_run,
            LigneIngeree.statut_qualite == "ok",
            LigneIngeree.id_localite.is_(None),
        )
    ).all()

    stats = {
        "total": len(lignes),
        "exact": 0,
        "alias": 0,
        "trigram": 0,
        "non_resolu": 0,
        "vide": 0,
    }

    for ligne in lignes:
        id_localite, methode = _resoudre_localite(
            db,
            localite_brute=ligne.localite_brute or "",
            sous_prefecture_brute=ligne.sous_prefecture_brute,
            seuil_trigram=seuil_trigram,
        )

        if id_localite is not None:
            ligne.id_localite = id_localite
            stats[methode] += 1
        else:
            # Marque comme non résolue
            ligne.statut_qualite = "localite_non_resolue"
            ligne.message_qualite = f"Localité non résolue : {ligne.localite_brute!r} (méthode: {methode})"
            stats[methode] += 1

    db.flush()
    return stats