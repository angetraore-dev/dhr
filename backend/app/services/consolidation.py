"""
Service de consolidation : ligne_ingeree → ouvrage.

Pour chaque ligne_ingeree avec statut_qualite='ok' et id_localite rempli :
1. Détermine la nature (puits/forage), l'alimentation (PMH/HVA...) et la réalisation (public/privé).
2. Cherche un ouvrage existant (dédoublonnage).
3. Si trouvé : met à jour (complète les champs vides).
4. Sinon : crée un ouvrage.
5. Marque ligne_ingeree.id_ouvrage_consolide.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Feuille, LigneIngeree, Ouvrage
from app.services.patterns import INDICATEURS_SANITAIRES, SANITAIRE_MOTS_CLES

logger = logging.getLogger("dhr.consolidation")


# =====================================================================
# Tokens pour la réalisation (question 1 — "Forage ADM" → public)
# =====================================================================
# On normalise la valeur avant de chercher ces tokens (minuscules, sans
# accents, espaces compactés). Attention : "adm" est court et pourrait
# matcher par substring des mots non pertinents — on l'inclut car il est
# fréquent dans les fichiers DHR, mais on le garde en dernier recours
# (voir ordre des tests ci-dessous).
_PUBLIC_TOKENS = (
    "public",
    "administratif",
    "admin",
    "adm",
    "etat",
    "onep",
)
_PRIVE_TOKENS = (
    "prive",
    "priv",        # couvre "privé" normalisé en "prive" et "priv" en abrégé
    "sodeci",
)


# =====================================================================
# Helpers de mapping
# =====================================================================
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


def _map_nature(type_brut: str | None) -> str:
    """Détermine la nature : 'puits', 'forage' ou 'inconnu'."""
    norm = _normaliser(type_brut)
    if "puits" in norm:
        return "puits"
    if "forage" in norm:
        return "forage"
    return "inconnu"


def _map_alimentation(type_brut: str | None, nom_feuille: str) -> str:
    """Détermine l'alimentation (PMH, HVA, PEA, HV, AUTRE). Priorité au nom de feuille."""
    nom_upper = (nom_feuille or "").upper()
    if "PMH" in nom_upper:
        return "PMH"
    if "HVA" in nom_upper:
        return "HVA"
    if "PEA" in nom_upper:
        return "PEA"
    if "HV" in nom_upper:
        return "HV"

    # Fallback sur le type brut
    norm = _normaliser(type_brut)
    if "pmh" in norm or "motricite" in norm or "pompe" in norm:
        return "PMH"
    if "hva" in norm or "amelioree" in norm:  # villageoise
        return "HVA"
    # PEA testé AVANT HV (sinon "villageoise" matcherait PEA si son libellé
    # contenait le mot, ce qui n'est pas le cas aujourd'hui mais fragile).
    if "pea" in norm or "autonome" in norm:
        return "PEA"
    if "hv" in norm or "villageoise" in norm:
        return "HV"

    return "AUTRE"


def _map_realisation(
    donnees_brutes: dict[str, Any] | None,
    type_ouvrage_brut: str | None = None,
    nom_feuille: str | None = None,
) -> str:
    """Détermine la réalisation (public, prive, inconnu).

    Ordre de priorité :
    1. Colonne explicite "type de forage" dans donnees_brutes
       (ex. Q3.1.1h. Type de forage = "Administratif")
    2. type_ouvrage_brut (ex. "Forage ADM")
    3. nom de feuille (ex. "Forages ADM")

    Question 1 du client : "Forage ADM" doit donner realisation_par="public".
    """
    # 1. Colonne explicite dans donnees_brutes
    if donnees_brutes:
        for k, v in donnees_brutes.items():
            if not k:
                continue
            if "type de forage" in _normaliser(k):
                norm = _normaliser(str(v))
                if any(t in norm for t in _PUBLIC_TOKENS):
                    return "public"
                if any(t in norm for t in _PRIVE_TOKENS):
                    return "prive"

    # 2. type_ouvrage_brut (ex. "Forage ADM")
    if type_ouvrage_brut:
        norm = _normaliser(type_ouvrage_brut)
        if any(t in norm for t in _PUBLIC_TOKENS):
            return "public"
        if any(t in norm for t in _PRIVE_TOKENS):
            return "prive"

    # 3. nom de feuille
    if nom_feuille:
        norm = _normaliser(nom_feuille)
        if any(t in norm for t in _PUBLIC_TOKENS):
            return "public"
        if any(t in norm for t in _PRIVE_TOKENS):
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
    # BUG CORRIGÉ : avant, `any(w for w in (...))` itérait sur des chaînes
    # non vides → toujours True → tout devenait "abandonne".
    if any(w in norm for w in ("abandon", "detruit", "inexistant")):
        return "abandonne"

    return "inconnu"


# =====================================================================
# Recherche d'un ouvrage existant
# =====================================================================
def _trouver_ouvrage_existant(
    db: Session,
    ligne: LigneIngeree,
    nature_ouvrage: str,
    type_alimentation: str,
) -> Ouvrage | None:
    """
    Cherche un ouvrage existant.
    Priorité 1 : code_ouvrage
    Priorité 2 : (id_localite, nature_ouvrage, type_alimentation, annee_realisation)
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
                if (
                    isinstance(v, (str, int))
                    and k
                    and "code" in k.lower()
                    and "ouvrage" in k.lower()
                ):
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
                Ouvrage.nature_ouvrage == nature_ouvrage,
                Ouvrage.type_alimentation == type_alimentation,
                Ouvrage.annee_realisation == ligne.annee_projet,
            )
        )
        if existing is not None:
            return existing

    return None


# =====================================================================
# Extraction qualite_eau
# =====================================================================
def _extraire_qualite_eau(
    donnees_brutes: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Extrait les indicateurs sanitaires de donnees_brutes.

    Retourne None si aucune donnée sanitaire n'est trouvée (le champ
    qualite_eau reste NULL en DB). Sinon, retourne un dict qui contient :
    - les indicateurs normalisés (onchocercose, vers_de_guinee, ...)
    - systématiquement les valeurs brutes sous `brut_<entete>`
    """
    if not donnees_brutes:
        return None

    result: dict[str, Any] = {}

    for k, v in donnees_brutes.items():
        if not k or v is None:
            continue
        k_norm = _normaliser(k)

        # 1. Matching sur un indicateur précis
        matched = None
        for code, patterns in INDICATEURS_SANITAIRES.items():
            for pat in patterns:
                if pat.search(k_norm):
                    matched = code
                    break
            if matched:
                break

        if matched:
            result[matched] = v
            result[f"brut_{k}"] = v
            continue

        # 2. Fallback : mot-clé générique
        for pat in SANITAIRE_MOTS_CLES:
            if pat.search(k_norm):
                result[f"brut_{k}"] = v
                break

    return result or None


# =====================================================================
# Consolidation d'une ligne
# =====================================================================
def _extract_code_ouvrage(donnees_brutes: dict[str, Any] | None) -> str | None:
    if not donnees_brutes:
        return None
    for key in (
        "Code ouvrage", "Code_Ouvrage", "CODE OUVRAGE",
        "code_ouvrage", "CODE\nOUVRAGE",
    ):
        if key in donnees_brutes and donnees_brutes[key] is not None:
            return str(donnees_brutes[key])
    return None


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

    # Mappings
    nature = _map_nature(ligne.type_ouvrage_brut)
    alimentation = _map_alimentation(ligne.type_ouvrage_brut, nom_feuille)
    realisation = _map_realisation(
        ligne.donnees_brutes,
        type_ouvrage_brut=ligne.type_ouvrage_brut,
        nom_feuille=nom_feuille,
    )
    etat = _map_etat(ligne.etat_ouvrage_brut)

    # Recherche d'un doublon
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
        if existing.nature_ouvrage in (None, "inconnu") and nature != "inconnu":
            existing.nature_ouvrage = nature
        if existing.type_alimentation in (None, "AUTRE") and alimentation != "AUTRE":
            existing.type_alimentation = alimentation
        if existing.realisation_par in (None, "inconnu") and realisation != "inconnu":
            existing.realisation_par = realisation

        # Fusion metadata : copie du dict pour garantir la détection du
        # changement par SQLAlchemy (JSONB sans MutableDict).
        if ligne.donnees_brutes:
            meta = dict(existing.metadata_ or {})
            for k, v in ligne.donnees_brutes.items():
                if k not in meta and v is not None:
                    meta[f"brut_{k}"] = v
            existing.metadata_ = meta

        # Fusion qualite_eau : on garde les clés existantes, on complète
        # avec les nouvelles (priorité à l'existant si déjà rempli).
        if ligne.donnees_brutes:
            new_eau = _extraire_qualite_eau(ligne.donnees_brutes)
            if new_eau:
                current_eau = dict(existing.qualite_eau or {})
                for k, v in new_eau.items():
                    if k not in current_eau:
                        current_eau[k] = v
                existing.qualite_eau = current_eau

        return existing

    # Création
    metadata: dict[str, Any] = {}
    if ligne.donnees_brutes:
        for k, v in ligne.donnees_brutes.items():
            if v is not None:
                metadata[f"brut_{k}"] = v

    qualite_eau = _extraire_qualite_eau(ligne.donnees_brutes)

    ouvrage = Ouvrage(
        code_ouvrage=_extract_code_ouvrage(ligne.donnees_brutes),
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

            # Ignore les localités
            if _est_feuille_localites(nom_feuille):
                stats["lignes_localites_ignorees"] += 1
                continue

            # Mappings pour vérifier l'existant
            nature = _map_nature(ligne.type_ouvrage_brut)
            alimentation = _map_alimentation(ligne.type_ouvrage_brut, nom_feuille)
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