"""
Patterns regex pour la détection des colonnes Excel → champs normalisés.

Ce fichier est partagé par :
- services/ingestion.py (mapping auto à l'ingestion)
- services/mapping.py (proposition de mapping pour l'UI)

Il ne dépend d'aucun autre service (pas d'import circulaire).
"""
from __future__ import annotations

import re


COLUMN_PATTERNS: dict[str, list[re.Pattern]] = {
    # --- Contexte administratif ---
    "region_brute": [
        re.compile(r"^r[ée]gion$", re.I),
        re.compile(r"q1\.2\.\s*r[ée]gion", re.I),
    ],
    "departement_brute": [
        re.compile(r"^d[ée]partement$", re.I),
        re.compile(r"q1\.3\.\s*d[ée]partement", re.I),
    ],
    "sous_prefecture_brute": [
        re.compile(r"^sous[_\s-]?pr[ée]fecture", re.I),
        re.compile(r"commune\s*/\s*sous[_\s-]?pr[ée]fecture", re.I),
        re.compile(r"q1\.4\.", re.I),
    ],
    "type_localite_brut": [
        re.compile(r"^type[_\s]localit[ée]", re.I),
        re.compile(r"^localit[ée][_\s]ou[_\s]campement$", re.I),
    ],
    "localite_brute": [
        re.compile(r"^localit[ée]$", re.I),
        re.compile(r"^village$", re.I),
        re.compile(r"^nom[_\s]village$", re.I),
        re.compile(r"q1\.5\.", re.I),
        re.compile(r"q1\.6\.", re.I),
    ],
    # --- Coordonnées ---
    "latitude_decimal": [
        re.compile(r"^latitude$", re.I),
        re.compile(r"^latitude\s*ouvrage$", re.I),
        re.compile(r"^lat$", re.I),
        re.compile(r"^y$", re.I),
    ],
    "longitude_decimal": [
        re.compile(r"^longitude$", re.I),
        re.compile(r"^longitude\s*ouvrage$", re.I),
        re.compile(r"^lon(g)?$", re.I),
        re.compile(r"^x$", re.I),
    ],
    # --- Ouvrage ---
    "type_ouvrage_brut": [
        re.compile(r"^type[_\s]ouvrage$", re.I),
        re.compile(r"^type_?\s*ouvrage$", re.I),
        re.compile(r"q3\.1\.\d+[a-z]?\.\s*type\s*d.?ouvrage", re.I),
    ],
    "etat_ouvrage_brut": [
        re.compile(r"^etat(_ouvrage)?$", re.I),
        re.compile(r"^etat\s*ouvrage$", re.I),
        re.compile(r"^état(_ouvrage)?$", re.I),
        re.compile(r"^etat[_\s]forage$", re.I),
        re.compile(r"q3\.1\.\d+[a-z]?\.\s*[ée]tat\s*du\s*forage", re.I),
    ],
    "annee_projet": [
        re.compile(r"^ann[ée]e", re.I),
        re.compile(r"date[_\s]fin", re.I),
        re.compile(r"date[_\s]r[ée]alisation", re.I),
    ],
    "bailleur_brut": [
        re.compile(r"^bailleur", re.I),
        re.compile(r"^projet$", re.I),
        re.compile(r"^financeur", re.I),
    ],
    "type_financement_brut": [
        re.compile(r"^type[_\s]financement", re.I),
    ],
    "a_cgpe": [
        re.compile(r"^a[_\s]cgpe$", re.I),
        re.compile(r"existence[_\s]cgpe", re.I),
        re.compile(r"^nb[_\s]comite$", re.I),
        re.compile(r"^organe\s*gestion$", re.I),
    ],
}