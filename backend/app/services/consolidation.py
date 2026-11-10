"""
Service de consolidation : ligne_ingeree → ouvrage.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Feuille, LigneIngeree, Ouvrage

logger = logging.getLogger("dhr.consolidation")


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


def _map_nature(nature_brut: str | None) -> str:
    """Détermine la nature : 'puits', 'forage' ou 'inconnu'."""
    norm = _normaliser(nature_brut)
    if "puits" in norm:
        return "puits"
    if "forage" in norm:
        return "forage"
    return "inconnu"


def _map_alimentation(type_brut: str | None, nom_feuille: str) -> str:
    """Détermine l'alimentation (PMH, HVA, PEA, HV, AUTRE)."""
    # Priorité 1 : le nom de la feuille
    nom_upper = (nom_feuille or "").upper()
    if "PMH" in nom_upper: return "PMH"
    if "HVA" in nom_upper: return "HVA"
    if "PEA" in nom_upper: return "PEA"
    if "HV" in nom_upper: return "HV"

    # Priorité 2 : la valeur brute (ex: "Hydraulique Villageoise Améliorée")
    norm = _normaliser(type_brut)
    if "pmh" in norm or "motricite" in norm or "pompe" in norm: return "PMH"
    if "hva" in norm or "villageoise amelioree" in norm: return "HVA"
    if "hv" in norm or "villageoise" in norm: return "HV"
    if "pea" in norm or "autonome" in norm: return "PEA"

    return "AUTRE"


def _map_realisation(donnees_brutes: dict[str, Any] | None) -> str:
    """Détermine la réalisation (public, prive, inconnu)."""
    if not donnees_brutes:
        return "inconnu"
    for k, v in donnees_brutes.items():
        if k and "type de forage" in k.lower():
            norm = _normaliser(str(v))
            if "public" in norm or "administratif" in norm:
                return "public"
            if "prive" in norm or "privé" in norm:
                return "prive"
    return "inconnu"


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


def _trouver_ouvrage_existant(
    db: Session,
    ligne: LigneIngeree,
    nature_ouvrage: str,
    type_alimentation: str,
) -> Ouvrage | None:
    """Cherche un ouvrage existant pour dédoublonnage."""
    code = None
    if ligne.donnees_brutes:
        for key in ("Code ouvrage", "Code_Ouvrage", "CODE OUVRAGE", "code_ouvrage", "CODE\nOUVRAGE"):
            if key in ligne.donnees_brutes:
                code = ligne.donnees_brutes[key]
                break
        if not code:
            for k, v in ligne.donnees_brutes.items():
                if isinstance(v, (str, int)) and k and "code" in k.lower() and "ouvrage" in k.lower():
                    code = v
                    break

    if code:
        existing = db.scalar(select(Ouvrage).where(Ouvrage.code_ouvrage == str(code)))
        if existing is not None:
            return existing

    if ligne.id_localite is not None and ligne.annee_projet is not None:
        existing = db.scalar(
            select(Ouvrage).where(
                Ouvrage.id_localite == ligne.id_localite,
                Ouvrage.nature_ouvrage == nature_ouvrage,
                Ouvrage.type_alimentation == type_alimentation,
                Ouvrage.annee_realisation == ligne.annee_projet,
            )
        )
        if existing is not None:
            return existing

    return None


def _consolider_ligne(
    db: Session,
    ligne: LigneIngeree,
    nom_feuille: str,
) -> Ouvrage | None:
    if ligne.statut_qualite != "ok":
        return None
    if ligne.id_localite is None:
        return None
    if ligne.latitude_decimal is None or ligne.longitude_decimal is None:
        return None

    nature = _map_nature(ligne.nature_ouvrage_brut)
    alimentation = _map_alimentation(ligne.type_alimentation_brut, nom_feuille)
    realisation = _map_realisation(ligne.donnees_brutes)
    etat = _map_etat(ligne.etat_ouvrage_brut)

    existing = _trouver_ouvrage_existant(db, ligne, nature, alimentation)

    if existing is not None:
        if existing.annee_realisation is None and ligne.annee_projet is not None:
            existing.annee_realisation = ligne.annee_projet
        if existing.latitude_decimal is None:
            existing.latitude_decimal = ligne.latitude_decimal
        if existing.longitude_decimal is None:
            existing.longitude_decimal = ligne.longitude_decimal
        if existing.etat == "inconnu" and etat != "inconnu":
            existing.etat = etat
        if existing.nature_ouvrage == "inconnu" and nature != "inconnu":
            existing.nature_ouvrage = nature
        if existing.type_alimentation == "AUTRE" and alimentation != "AUTRE":
            existing.type_alimentation = alimentation
        if existing.realisation_par == "inconnu" and realisation != "inconnu":
            existing.realisation_par = realisation

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
        nature_ouvrage=nature,
        type_alimentation=alimentation,
        realisation_par=realisation,
        etat=etat,
        annee_realisation=ligne.annee_projet,
        latitude_decimal=ligne.latitude_decimal,
        longitude_decimal=ligne.longitude_decimal,
        metadata_=metadata,
    )
    db.add(ouvrage)
    db.flush()
    return ouvrage


def consolider_lignes_run(
    db: Session,
    id_run: int,
) -> dict[str, Any]:
    lignes = db.scalars(
        select(LigneIngeree).where(
            LigneIngeree.id_run == id_run,
            LigneIngeree.statut_qualite == "ok",
            LigneIngeree.id_localite.isnot(None),
        )
    ).all()

    feuilles_cache: dict[int, str] = {}
    for f in db.scalars(select(Feuille)).all():
        feuilles_cache[f.id_feuille] = f.nom_feuille

    def _est_feuille_localites(nom_feuille: str) -> bool:
        norm = _normaliser(nom_feuille)
        return "localite" in norm or "village" in norm or "campement" in norm

    stats = {
        "total_lignes": len(lignes),
        "ouvrages_crees": 0,
        "ouvrages_mis_a_jour": 0,
        "lignes_ignorees": 0,
        "lignes_localites_ignorees": 0,
        "erreurs": 0,
    }

    for ligne in lignes:
        try:
            nom_feuille = feuilles_cache.get(ligne.id_feuille, "")
            if _est_feuille_localites(nom_feuille):
                stats["lignes_localites_ignorees"] += 1
                continue

            nature = _map_nature(ligne.nature_ouvrage_brut)
            alimentation = _map_alimentation(ligne.type_alimentation_brut, nom_feuille)
            existing_before = _trouver_ouvrage_existant(db, ligne, nature, alimentation)

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