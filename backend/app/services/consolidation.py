"""
Service de consolidation : ligne_ingeree → ouvrage.

IMPORTANT (Bible § 3.2.3) :
- `doublon_suspect` : code_ouvrage déjà vu + distance > 1 km.
- `type_ouvrage_inconnu` : après création, si nature/alim/réal tous inconnus.
- `qualite_eau` : extraite via INDICATEURS_SANITAIRES (clés normalisées + brut_*).
- `_map_nature`, `_map_alimentation`, `_map_realisation`, `_map_etat` : lisent
  `type_ouvrage_brut` et `usage_ouvrage_brut` (P12).
"""
from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import Feuille, LigneIngeree, Ouvrage
from app.services.patterns import INDICATEURS_SANITAIRES, SANITAIRE_MOTS_CLES

logger = logging.getLogger("dhr.consolidation")

# Seuil pour la détection de doublon suspect (en km)
SEUIL_DOUBLON_KM = 1.0


def _normaliser(texte: str | None) -> str:
    if texte is None:
        return ""
    texte = str(texte).strip().lower()
    texte = "".join(
        c for c in unicodedata.normalize("NFD", texte)
        if unicodedata.category(c) != "Mn"
    )
    texte = re.sub(r"[\s\-_]+", " ", texte).strip()
    return texte


# =====================================================================
# _map_* : interprétation du contenu (P11)
# =====================================================================
def _map_nature(type_ouvrage_brut: str | None, nom_feuille: str = "") -> str:
    """
    Détermine la nature : 'puits', 'forage' ou 'inconnu'.
    Priorité : type_ouvrage_brut > nom_feuille.
    """
    norm = _normaliser(type_ouvrage_brut)
    if "puits" in norm:
        return "puits"
    if "forage" in norm or "sondage" in norm:
        return "forage"
    # Fallback nom de feuille
    norm_f = _normaliser(nom_feuille)
    if "puits" in norm_f:
        return "puits"
    if "forage" in norm_f:
        return "forage"
    return "inconnu"


def _map_alimentation(
    type_ouvrage_brut: str | None,
    usage_ouvrage_brut: str | None,
    nom_feuille: str = "",
) -> str:
    """
    Détermine l'alimentation (PMH, HVA, PEA, HV, AUTRE).
    Priorité : nom_feuille > type_ouvrage_brut > usage_ouvrage_brut.
    """
    # Priorité 1 : nom de la feuille
    nom_upper = (nom_feuille or "").upper()
    if "PMH" in nom_upper:
        return "PMH"
    if "HVA" in nom_upper:
        return "HVA"
    if "PEA" in nom_upper:
        return "PEA"
    if "HV" in nom_upper:
        return "HV"

    # Priorité 2 : type_ouvrage_brut
    norm = _normaliser(type_ouvrage_brut)
    if "pmh" in norm or "motricite" in norm or "pompe" in norm:
        return "PMH"
    if "hva" in norm or "villageoise amelioree" in norm:
        return "HVA"
    if "hv" in norm or "villageoise" in norm:
        return "HV"
    if "pea" in norm or "autonome" in norm:
        return "PEA"

    # Priorité 3 : usage_ouvrage_brut
    norm_u = _normaliser(usage_ouvrage_brut)
    if "pmh" in norm_u or "motricite" in norm_u or "pompe" in norm_u:
        return "PMH"
    if "hva" in norm_u or "villageoise amelioree" in norm_u:
        return "HVA"
    if "hv" in norm_u or "villageoise" in norm_u:
        return "HV"
    if "pea" in norm_u or "autonome" in norm_u:
        return "PEA"

    return "AUTRE"


def _map_realisation(
    donnees_brutes: dict[str, Any] | None,
    type_ouvrage_brut: str | None = None,
) -> str:
    """
    Détermine la réalisation (public, prive, inconnu).
    Priorité : colonne explicite 'Type de forage' > type_ouvrage_brut.
    """
    if donnees_brutes:
        for k, v in donnees_brutes.items():
            if k and "type de forage" in k.lower():
                norm = _normaliser(str(v))
                if "public" in norm or "administratif" in norm:
                    return "public"
                if "prive" in norm:
                    return "prive"

    norm = _normaliser(type_ouvrage_brut)
    if any(w in norm for w in ("adm", "administratif", "onep", "etat")):
        return "public"
    if any(w in norm for w in ("sodeci", "prive", "ong")):
        return "prive"

    return "inconnu"


def _map_etat(etat_ouvrage_brut: str | None) -> str:
    """Détermine l'état (fonctionnel, en_panne, abandonne, inconnu)."""
    if not etat_ouvrage_brut:
        return "inconnu"
    norm = _normaliser(etat_ouvrage_brut)
    if any(w in norm for w in ("panne", "mauvais", "dysfonction", "non fonctionnel")):
        return "en_panne"
    if any(w in norm for w in ("abandon", "detruit", "inexistant")):
        return "abandonne"
    if any(w in norm for w in ("fonctionnel", "bon", "marche", "utilise", "exploite")):
        return "fonctionnel"
    return "inconnu"


# =====================================================================
# Extraction qualite_eau (B6.3)
# =====================================================================
def _extraire_qualite_eau(donnees_brutes: dict[str, Any]) -> dict[str, Any] | None:
    """
    Extrait les indicateurs sanitaires de donnees_brutes.
    Retourne None si aucun indicateur trouvé.
    """
    if not donnees_brutes:
        return None

    qualite: dict[str, Any] = {}

    for entete, valeur in donnees_brutes.items():
        if valeur is None or str(valeur).strip() == "":
            continue

        # 1. Chercher un indicateur normalisé
        matched = False
        for code, patterns in INDICATEURS_SANITAIRES.items():
            for pat in patterns:
                if pat.search(entete):
                    qualite[code] = valeur
                    matched = True
                    break
            if matched:
                break

        # 2. Chercher un mot-clé sanitaire générique
        if not matched:
            for pat in SANITAIRE_MOTS_CLES:
                if pat.search(entete):
                    matched = True
                    break

        # 3. Toujours ajouter la clé brute (traçabilité)
        if matched:
            qualite[f"brut_{entete}"] = valeur

    return qualite if qualite else None


# =====================================================================
# Dédoublonnage
# =====================================================================
def _extraire_code_ouvrage(donnees_brutes: dict[str, Any] | None) -> str | None:
    """Extrait code_ouvrage de donnees_brutes."""
    if not donnees_brutes:
        return None
    for key in ("Code ouvrage", "Code_Ouvrage", "CODE OUVRAGE", "code_ouvrage", "CODE\nOUVRAGE"):
        if key in donnees_brutes:
            return str(donnees_brutes[key])
    for k, v in donnees_brutes.items():
        if isinstance(v, str | int) and k and "code" in k.lower() and "ouvrage" in k.lower():
            return str(v)
    return None


def _distance_km(
    db: Session,
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """
    Distance géodésique (km) via ST_Distance de PostGIS.
    Retourne inf si l'un des points est NULL.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float("inf")

    query = text("""
        SELECT ST_Distance(
            geom_from_latlon(:lat1, :lon1)::geography,
            geom_from_latlon(:lat2, :lon2)::geography
        ) / 1000.0 AS distance_km
    """)
    row = db.execute(query, {"lat1": lat1, "lon1": lon1, "lat2": lat2, "lon2": lon2}).first()
    return row[0] if row else float("inf")


def _trouver_ouvrage_existant(
    db: Session,
    ligne: LigneIngeree,
    nature_ouvrage: str,
    type_alimentation: str,
) -> Ouvrage | None:
    """Cherche un ouvrage existant pour dédoublonnage (code_ouvrage puis tuple)."""
    code = _extraire_code_ouvrage(ligne.donnees_brutes)
    if code:
        existing = db.scalar(select(Ouvrage).where(Ouvrage.code_ouvrage == code))
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


# =====================================================================
# Consolidation d'une ligne
# =====================================================================
def _consolider_ligne(
    db: Session,
    ligne: LigneIngeree,
    nom_feuille: str,
) -> Ouvrage | None:
    """
    Consolide une ligne en ouvrage.
    Retourne l'ouvrage créé/mis à jour, ou None si ignoré.
    Met à jour ligne.statut_qualite si besoin (doublon_suspect, type_ouvrage_inconnu).
    """
    # Filtres d'entrée
    if ligne.statut_qualite != "ok":
        return None
    if ligne.id_localite is None:
        return None
    if ligne.latitude_decimal is None or ligne.longitude_decimal is None:
        return None

    # Calcul des attributs normalisés
    nature = _map_nature(ligne.type_ouvrage_brut, nom_feuille)
    alimentation = _map_alimentation(
        ligne.type_ouvrage_brut, ligne.usage_ouvrage_brut, nom_feuille
    )
    realisation = _map_realisation(ligne.donnees_brutes, ligne.type_ouvrage_brut)
    etat = _map_etat(ligne.etat_ouvrage_brut)

    # --- Détection doublon_suspect (B6.1) ---
    code = _extraire_code_ouvrage(ligne.donnees_brutes)
    if code:
        existing_by_code = db.scalar(select(Ouvrage).where(Ouvrage.code_ouvrage == code))
        if existing_by_code is not None:
            distance = _distance_km(
                db,
                ligne.latitude_decimal, ligne.longitude_decimal,
                existing_by_code.latitude_decimal, existing_by_code.longitude_decimal,
            )
            if distance > SEUIL_DOUBLON_KM:
                ligne.statut_qualite = "doublon_suspect"
                ligne.message_qualite = (
                    f"Code ouvrage {code} déjà utilisé à {distance:.1f} km"
                )
                return None

    # --- Chercher un ouvrage existant (dédoublonnage) ---
    existing = _trouver_ouvrage_existant(db, ligne, nature, alimentation)

    if existing is not None:
        # Mise à jour des champs vides
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

        # Fusion metadata
        if ligne.donnees_brutes:
            meta = existing.metadata_ or {}
            for k, v in ligne.donnees_brutes.items():
                if k not in meta and v is not None:
                    meta[f"brut_{k}"] = v
            existing.metadata_ = meta

        # Fusion qualite_eau (B6.3)
        qe = _extraire_qualite_eau(ligne.donnees_brutes)
        if qe:
            existing.qualite_eau = {**(existing.qualite_eau or {}), **qe}

        return existing

    # --- Création ---
    metadata = {}
    if ligne.donnees_brutes:
        for k, v in ligne.donnees_brutes.items():
            if v is not None:
                metadata[f"brut_{k}"] = v

    qualite_eau = _extraire_qualite_eau(ligne.donnees_brutes)

    ouvrage = Ouvrage(
        code_ouvrage=code,
        id_localite=ligne.id_localite,
        nature_ouvrage=nature,
        type_alimentation=alimentation,
        realisation_par=realisation,
        etat=etat,
        annee_realisation=ligne.annee_projet,
        latitude_decimal=ligne.latitude_decimal,
        longitude_decimal=ligne.longitude_decimal,
        metadata_=metadata,
        qualite_eau=qualite_eau,
    )
    db.add(ouvrage)
    db.flush()

    # --- Écriture type_ouvrage_inconnu (B6.2) ---
    if nature == "inconnu" and alimentation == "AUTRE" and realisation == "inconnu":
        ligne.statut_qualite = "type_ouvrage_inconnu"
        ligne.message_qualite = (
            "Attributs métier indéterminés (nature, alimentation, réalisation)"
        )

    return ouvrage


# =====================================================================
# Consolidation d'un run
# =====================================================================
def consolider_lignes_run(db: Session, id_run: int) -> dict[str, Any]:
    """Consolide toutes les lignes du run en ouvrages."""
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
        return (
            "localite" in norm
            or "village" in norm
            or "campement" in norm
        )

    stats = {
        "total_lignes": len(lignes),
        "ouvrages_crees": 0,
        "ouvrages_mis_a_jour": 0,
        "lignes_ignorees": 0,
        "lignes_localites_ignorees": 0,
        "doublons_suspects": 0,
        "attributs_indetermines": 0,
        "erreurs": 0,
    }

    for ligne in lignes:
        try:
            nom_feuille = feuilles_cache.get(ligne.id_feuille, "")
            if _est_feuille_localites(nom_feuille):
                stats["lignes_localites_ignorees"] += 1
                stats["lignes_ignorees"] += 1
                continue

            # Compter les états avant consolidation
            nature_before = _map_nature(ligne.type_ouvrage_brut, nom_feuille)
            alim_before = _map_alimentation(
                ligne.type_ouvrage_brut, ligne.usage_ouvrage_brut, nom_feuille
            )
            existing_before = _trouver_ouvrage_existant(
                db, ligne, nature_before, alim_before
            )

            ouvrage = _consolider_ligne(db, ligne, nom_feuille)

            if ouvrage is not None:
                ligne.id_ouvrage_consolide = ouvrage.id_ouvrage
                if existing_before is not None:
                    stats["ouvrages_mis_a_jour"] += 1
                else:
                    stats["ouvrages_crees"] += 1

                # Compter les cas particuliers
                if ligne.statut_qualite == "type_ouvrage_inconnu":
                    stats["attributs_indetermines"] += 1
            else:
                if ligne.statut_qualite == "doublon_suspect":
                    stats["doublons_suspects"] += 1
                else:
                    stats["lignes_ignorees"] += 1

        except Exception as e:
            logger.error("Erreur consolidation ligne %s : %s", ligne.id_ligne, e)
            stats["erreurs"] += 1

    db.flush()
    return stats
