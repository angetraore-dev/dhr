"""
Service de consolidation : ligne_ingeree → ouvrage.

IMPORTANT (Bible § 3.2.3) :
- `doublon_suspect` : code_ouvrage déjà vu + distance > 1 km.
- `type_ouvrage_inconnu` : après création, si nature/alim/réal tous inconnus.
- `qualite_eau` : extraite via mapping validé + INDICATEURS_SANITAIRES (clés normalisées + brut_*).
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

from app.models import Feuille, LigneIngeree, MappingFeuille, Ouvrage
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
    m_feuille = re.search(r"\b(PMH|HVA|PEA|HV)\b", nom_feuille or "", re.I)
    if m_feuille:
        return m_feuille.group(1).upper()

    norm = _normaliser(type_ouvrage_brut)
    if re.search(r"\bpmh\b", norm) or "motricite" in norm or "pompe" in norm:
        return "PMH"
    if re.search(r"\bhva\b", norm) or "villageoise amelioree" in norm:
        return "HVA"
    if re.search(r"\bhv\b", norm) or "villageoise" in norm:
        return "HV"
    if re.search(r"\bpea\b", norm) or "autonome" in norm:
        return "PEA"

    norm_u = _normaliser(usage_ouvrage_brut)
    if re.search(r"\bpmh\b", norm_u) or "motricite" in norm_u or "pompe" in norm_u:
        return "PMH"
    if re.search(r"\bhva\b", norm_u) or "villageoise amelioree" in norm_u:
        return "HVA"
    if re.search(r"\bhv\b", norm_u) or "villageoise" in norm_u:
        return "HV"
    if re.search(r"\bpea\b", norm_u) or "autonome" in norm_u:
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
# Extraction qualite_eau (B6.3 + mapping explicite metadata.qualite_eau.*)
# =====================================================================
def _extraire_qualite_eau(
    donnees_brutes: dict[str, Any] | None,
    mapping_colonnes: dict[str, str | None] | None = None,
) -> dict[str, Any] | None:
    """
    Construit le dict JSONB ouvrage.qualite_eau depuis :
    1. Les colonnes explicitement mappées sur 'qualite_eau' ou 'metadata.qualite_eau.<cle>'
    2. Les indicateurs sanitaires connus (INDICATEURS_SANITAIRES & SANITAIRE_MOTS_CLES)
    Conserve systématiquement `brut_<entete>` pour la traçabilité.
    """
    if not donnees_brutes:
        return None

    qualite: dict[str, Any] = {}

    # 1. Via mapping explicite de la feuille (prioritaire)
    if mapping_colonnes:
        for entete_brut, cible in mapping_colonnes.items():
            if not cible:
                continue
            val = donnees_brutes.get(entete_brut)
            if val is None or str(val).strip() == "":
                continue
            val_clean = str(val).strip() if isinstance(val, str) else val
            if cible == "qualite_eau":
                qualite["qualite_eau"] = val_clean
                qualite[f"brut_{entete_brut}"] = val
            elif cible.startswith("metadata.qualite_eau."):
                cle = cible.split(".", 2)[2]
                qualite[cle] = val_clean
                qualite[f"brut_{entete_brut}"] = val

    # 2. Fallback par patterns sanitaires sur toutes les colonnes de donnees_brutes
    for entete, valeur in donnees_brutes.items():
        if valeur is None or str(valeur).strip() == "":
            continue

        matched = False
        for code, patterns in INDICATEURS_SANITAIRES.items():
            for pat in patterns:
                if pat.search(entete):
                    if code not in qualite:
                        qualite[code] = valeur
                    matched = True
                    break
            if matched:
                break

        if not matched:
            for pat in SANITAIRE_MOTS_CLES:
                if pat.search(entete):
                    matched = True
                    break

        if matched and f"brut_{entete}" not in qualite:
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
    """Distance géodésique (km) via ST_Distance de PostGIS."""
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
    """
    Cherche un ouvrage existant pour dédoublonnage (idempotence) :
    1. Par code_ouvrage exact
    2. Par tuple (id_localite, nature_ouvrage, type_alimentation, annee_realisation)
    3. Par proximité GPS (< 20 mètres) dans la même localité avec même nature et alimentation
    """
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

    if (
        ligne.id_localite is not None
        and ligne.latitude_decimal is not None
        and ligne.longitude_decimal is not None
    ):
        candidats = db.scalars(
            select(Ouvrage).where(
                Ouvrage.id_localite == ligne.id_localite,
                Ouvrage.nature_ouvrage == nature_ouvrage,
                Ouvrage.type_alimentation == type_alimentation,
                Ouvrage.latitude_decimal.isnot(None),
                Ouvrage.longitude_decimal.isnot(None),
            )
        ).all()
        for cand in candidats:
            dist_km = _distance_km(
                db,
                ligne.latitude_decimal,
                ligne.longitude_decimal,
                cand.latitude_decimal,
                cand.longitude_decimal,
            )
            if dist_km <= 0.02:
                return cand
    return None

# =====================================================================
# Consolidation d'une ligne
# =====================================================================

def _consolider_ligne(
    db: Session,
    ligne: LigneIngeree,
    nom_feuille: str,
    mapping_colonnes: dict[str, str | None] | None = None,
) -> Ouvrage | None:
    """
    Consolide une ligne en ouvrage.
    Retourne l'ouvrage créé/mis à jour, ou None si ignoré.
    """
    if ligne.statut_qualite != "ok":
        return None
    if ligne.id_localite is None:
        return None
    if ligne.latitude_decimal is None or ligne.longitude_decimal is None:
        return None

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
        if (
            existing_by_code is not None
            and existing_by_code.latitude_decimal is not None
            and existing_by_code.longitude_decimal is not None
        ):
            distance = _distance_km(
                db,
                ligne.latitude_decimal,
                ligne.longitude_decimal,
                existing_by_code.latitude_decimal,
                existing_by_code.longitude_decimal,
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

        qe = _extraire_qualite_eau(ligne.donnees_brutes, mapping_colonnes)
        if qe:
            existing.qualite_eau = {**(existing.qualite_eau or {}), **qe}

        return existing

    # --- Création ---
    metadata = {}
    if ligne.donnees_brutes:
        for k, v in ligne.donnees_brutes.items():
            if v is not None:
                metadata[f"brut_{k}"] = v

    qualite_eau = _extraire_qualite_eau(ligne.donnees_brutes, mapping_colonnes)

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

    # Cache des mappings validés par feuille (pour metadata.qualite_eau.*)
    mappings_cache: dict[int, dict[str, str | None]] = {}
    for m in db.scalars(
        select(MappingFeuille).where(MappingFeuille.valide_par_utilisateur.is_(True))
    ).all():
        mappings_cache.setdefault(m.id_feuille, {})[m.entete_brut] = m.champ_cible

    def _est_feuille_localites(nom_feuille: str) -> bool:
        norm = _normaliser(nom_feuille)
        mots_localite = ("localite", "village", "campement")
        mots_ouvrage = ("ouvrage", "forage", "puits", "pmh", "hva", "pea", "hv")
        return any(m in norm for m in mots_localite) and not any(
            m in norm for m in mots_ouvrage
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

            nature_before = _map_nature(ligne.type_ouvrage_brut, nom_feuille)
            alim_before = _map_alimentation(
                ligne.type_ouvrage_brut, ligne.usage_ouvrage_brut, nom_feuille
            )
            existing_before = _trouver_ouvrage_existant(
                db, ligne, nature_before, alim_before
            )

            mapping_colonnes = mappings_cache.get(ligne.id_feuille)
            ouvrage = _consolider_ligne(db, ligne, nom_feuille, mapping_colonnes)

            if ouvrage is not None:
                ligne.id_ouvrage_consolide = ouvrage.id_ouvrage
                if existing_before is not None:
                    stats["ouvrages_mis_a_jour"] += 1
                else:
                    stats["ouvrages_crees"] += 1

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
