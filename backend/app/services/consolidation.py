"""
Service de consolidation : ligne_ingeree → ouvrage.

Pour chaque ligne_ingeree avec statut_qualite='ok' et id_localite rempli :
1. Détermine le type d'ouvrage (priorité : nom de la feuille > type_ouvrage_brut)
2. Cherche un ouvrage existant (dédoublonnage)
3. Si trouvé : met à jour (complète les champs vides)
4. Sinon : crée un ouvrage
5. Marque ligne_ingeree.id_ouvrage_consolide
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Feuille,
    LigneIngeree,
    Ouvrage,
    TypeOuvrage,
)

logger = logging.getLogger("dhr.consolidation")


# =====================================================================
# Helpers de normalisation
# =====================================================================
def _normaliser(texte: str | None) -> str:
    if texte is None:
        return ""
    import re
    import unicodedata
    texte = str(texte).strip().lower()
    texte = "".join(
        c for c in unicodedata.normalize("NFD", texte)
        if unicodedata.category(c) != "Mn"
    )
    texte = re.sub(r"[\s\-_]+", " ", texte).strip()
    return texte


def _get_type_ouvrage(db: Session, code: str) -> TypeOuvrage:
    t = db.scalar(select(TypeOuvrage).where(TypeOuvrage.code == code))
    if t is None:
        raise ValueError(f"TypeOuvrage '{code}' introuvable")
    return t


# =====================================================================
# Mapping type d'ouvrage (priorité : nom de feuille)
# =====================================================================
def _map_type_ouvrage_avec_feuille(
    type_brut: str | None,
    nom_feuille: str,
    db: Session,
) -> TypeOuvrage:
    """
    Détermine le TypeOuvrage.
    Priorité 1 : nom de la feuille (PMH, HVA, PEA, HV).
    Priorité 2 : type_ouvrage_brut (mots-clés).
    """
    nom_upper = nom_feuille.upper()

    if "PMH" in nom_upper:
        return _get_type_ouvrage(db, "PMH")
    if "HVA" in nom_upper:
        return _get_type_ouvrage(db, "HVA")
    if "PEA" in nom_upper:
        return _get_type_ouvrage(db, "PEA")
    if "HV" in nom_upper:
        return _get_type_ouvrage(db, "HV")

    # Fallback : type_ouvrage_brut
    if not type_brut:
        return _get_type_ouvrage(db, "AUTRE")

    norm = _normaliser(type_brut)

    if "pmh" in norm or "motricite" in norm or "pompe" in norm:
        return _get_type_ouvrage(db, "PMH")
    if "hva" in norm or "villageoise amelioree" in norm:
        return _get_type_ouvrage(db, "HVA")
    if "hv" in norm or "villageoise" in norm:
        return _get_type_ouvrage(db, "HV")
    if "pea" in norm or "autonome" in norm:
        return _get_type_ouvrage(db, "PEA")
    if "forage" in norm:
        return _get_type_ouvrage(db, "PMH")
    if "puits" in norm:
        return _get_type_ouvrage(db, "AUTRE")

    return _get_type_ouvrage(db, "AUTRE")


# =====================================================================
# Mapping état
# =====================================================================
def _map_etat(etat_brut: str | None) -> str:
    if not etat_brut:
        return "inconnu"
    norm = _normaliser(etat_brut)

    if any(w in norm for w in ("fonctionnel", "bon", "marche", "utilise", "exploite")):
        return "fonctionnel"
    if any(w in norm for w in ("panne", "mauvais", "dysfonction", "non fonctionnel")):
        return "en_panne"
    if any(w in norm for w in ("abandon", "detruit", "inexistant")):
        return "abandonne"

    return "inconnu"


# =====================================================================
# Recherche d'un ouvrage existant (dédoublonnage)
# =====================================================================
def _trouver_ouvrage_existant(
    db: Session,
    ligne: LigneIngeree,
    id_type_ouvrage: int,
) -> Ouvrage | None:
    """
    Cherche un ouvrage existant.
    Priorité 1 : code_ouvrage
    Priorité 2 : (id_localite, id_type_ouvrage, annee_realisation)
    """
    code = None
    if ligne.donnees_brutes:
        for key in (
            "Code ouvrage", "Code_Ouvrage", "CODE OUVRAGE",
            "code_ouvrage", "CODE\nOUVRAGE",
        ):
            if key in ligne.donnees_brutes:
                code = ligne.donnees_brutes[key]
                break
        if not code:
            for k, v in ligne.donnees_brutes.items():
                if isinstance(v, (str, int)) and k and "code" in k.lower() and "ouvrage" in k.lower():
                    code = v
                    break

    if code:
        existing = db.scalar(
            select(Ouvrage).where(Ouvrage.code_ouvrage == str(code))
        )
        if existing is not None:
            return existing

    if ligne.id_localite is not None and ligne.annee_projet is not None:
        existing = db.scalar(
            select(Ouvrage).where(
                Ouvrage.id_localite == ligne.id_localite,
                Ouvrage.id_type_ouvrage == id_type_ouvrage,
                Ouvrage.annee_realisation == ligne.annee_projet,
            )
        )
        if existing is not None:
            return existing

    return None


# =====================================================================
# Consolidation d'une ligne
# =====================================================================
def _consolider_ligne(
    db: Session,
    ligne: LigneIngeree,
    nom_feuille: str,
) -> Ouvrage | None:
    """Consolide une ligne_ingeree en ouvrage."""
    if ligne.statut_qualite != "ok":
        return None
    if ligne.id_localite is None:
        return None
    if ligne.latitude_decimal is None or ligne.longitude_decimal is None:
        return None

    type_ouvrage = _map_type_ouvrage_avec_feuille(ligne.type_ouvrage_brut, nom_feuille, db)
    etat = _map_etat(ligne.etat_ouvrage_brut)

    existing = _trouver_ouvrage_existant(db, ligne, type_ouvrage.id_type_ouvrage)

    if existing is not None:
        if existing.annee_realisation is None and ligne.annee_projet is not None:
            existing.annee_realisation = ligne.annee_projet
        if existing.latitude_decimal is None:
            existing.latitude_decimal = ligne.latitude_decimal
        if existing.longitude_decimal is None:
            existing.longitude_decimal = ligne.longitude_decimal
        if existing.etat == "inconnu" and etat != "inconnu":
            existing.etat = etat
        if ligne.donnees_brutes:
            meta = existing.metadata_ or {}
            for k, v in ligne.donnees_brutes.items():
                if k not in meta and v is not None:
                    meta[f"brut_{k}"] = v
            existing.metadata_ = meta
        return existing

    metadata = {}
    if ligne.donnees_brutes:
        for k, v in ligne.donnees_brutes.items():
            if v is not None:
                metadata[f"brut_{k}"] = v

    code_ouvrage = None
    if ligne.donnees_brutes:
        for key in ("Code ouvrage", "Code_Ouvrage", "CODE OUVRAGE", "code_ouvrage"):
            if key in ligne.donnees_brutes:
                code_ouvrage = str(ligne.donnees_brutes[key])
                break

    ouvrage = Ouvrage(
        code_ouvrage=code_ouvrage,
        id_localite=ligne.id_localite,
        id_type_ouvrage=type_ouvrage.id_type_ouvrage,
        etat=etat,
        annee_realisation=ligne.annee_projet,
        latitude_decimal=ligne.latitude_decimal,
        longitude_decimal=ligne.longitude_decimal,
        metadata_=metadata,
    )
    db.add(ouvrage)
    db.flush()
    return ouvrage


# =====================================================================
# Consolidation d'un run
# =====================================================================
def consolider_lignes_run(
    db: Session,
    id_run: int,
) -> dict[str, Any]:
    """Consolide toutes les lignes d'un run en ouvrages."""
    lignes = db.scalars(
        select(LigneIngeree).where(
            LigneIngeree.id_run == id_run,
            LigneIngeree.statut_qualite == "ok",
            LigneIngeree.id_localite.isnot(None),
        )
    ).all()

    # Charge les noms de feuilles en cache
    feuilles_cache: dict[int, str] = {}
    for f in db.scalars(select(Feuille)).all():
        feuilles_cache[f.id_feuille] = f.nom_feuille

    stats = {
        "total_lignes": len(lignes),
        "ouvrages_crees": 0,
        "ouvrages_mis_a_jour": 0,
        "lignes_ignorees": 0,
        "erreurs": 0,
    }

    for ligne in lignes:
        try:
            nom_feuille = feuilles_cache.get(ligne.id_feuille, "")

            type_ouvrage = _map_type_ouvrage_avec_feuille(ligne.type_ouvrage_brut, nom_feuille, db)
            existing_before = _trouver_ouvrage_existant(db, ligne, type_ouvrage.id_type_ouvrage)

            ouvrage = _consolider_ligne(db, ligne, nom_feuille)

            if ouvrage is not None:
                ligne.id_ouvrage_consolide = ouvrage.id_ouvrage
                if existing_before is not None:
                    stats["ouvrages_mis_a_jour"] += 1
                else:
                    stats["ouvrages_crees"] += 1
            else:
                stats["lignes_ignorees"] += 1

        except Exception as e:
            logger.error("Erreur consolidation ligne %s : %s", ligne.id_ligne, e)
            stats["erreurs"] += 1

    db.flush()
    return stats