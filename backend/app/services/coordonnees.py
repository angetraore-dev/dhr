"""
Conversion des coordonnées géographiques en décimal WGS84.

Formats supportés :
- Décimal : 6.3658183, -7.527405
- Décimal avec virgule : 6,3658183
- DMS compact : 075225 (= 07°52'25")
- DMS explicite : 7°52'25"N, 7°52'25.5"S
- Direction : 6.3658183 N, 7.527405 W
- Degrés-minutes décimales : 7 52.416 N

Retourne (lat_decimal, lon_decimal) ou (None, None) si invalide.
"""
from __future__ import annotations

import re
from typing import Any


# Bornes WGS84
LAT_MIN, LAT_MAX = -90.0, 90.0
LON_MIN, LON_MAX = -180.0, 180.0


def _to_float(s: str) -> float | None:
    """Convertit une chaîne en float, gère la virgule."""
    try:
        return float(s.replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None


def _dms_to_decimal(deg: float, min_: float, sec: float, direction: str | None = None) -> float:
    """Convertit DMS en décimal. Direction : N/S (lat), E/W (lon)."""
    decimal = deg + min_ / 60.0 + sec / 3600.0
    if direction:
        d = direction.upper()
        if d in ("S", "W"):
            decimal = -decimal
    return decimal


def _is_valid_lat(val: float | None) -> bool:
    return val is not None and LAT_MIN <= val <= LAT_MAX


def _is_valid_lon(val: float | None) -> bool:
    return val is not None and LON_MIN <= val <= LON_MAX


def parser_une_coordonnee(brut: Any, est_latitude: bool) -> float | None:
    """
    Parse une coordonnée brute (lat ou lon).
    Retourne le décimal ou None.
    """
    if brut is None or brut == "":
        return None

    # Si c'est déjà un float
    if isinstance(brut, (int, float)):
        val = float(brut)
        if est_latitude and _is_valid_lat(val):
            return val
        if not est_latitude and _is_valid_lon(val):
            return val
        return None

    s = str(brut).strip()
    if not s:
        return None

    # --- Cas 1 : DMS compact (6 chiffres : 075225 = 07°52'25") ---
    if re.fullmatch(r"\d{6}", s):
        deg = int(s[0:2])
        min_ = int(s[2:4])
        sec = int(s[4:6])
        if min_ < 60 and sec < 60:
            val = _dms_to_decimal(deg, min_, sec)
            return val if (est_latitude and _is_valid_lat(val)) or (not est_latitude and _is_valid_lon(val)) else None
        return None

    # --- Cas 2 : DMS explicite (7°52'25"N / 7° 52' 25.5" S / 8°2'20,93"W) ---
    m = re.match(
        r"^\s*(-?\d+)[°\s]+(\d+)[\'\s]+([\d.,]+)[\"\s]*([NSEW])?\s*$",
        s, re.IGNORECASE,
    )
    if m:
        try:
            deg = float(m.group(1))
            min_ = float(m.group(2))
            sec = float(m.group(3).replace(",", "."))  # ← virgule → point
            direction = m.group(4)
            if min_ >= 60 or sec >= 60:
                return None
            val = _dms_to_decimal(abs(deg), min_, sec, direction)
            if deg < 0:
                val = -val
            return val if (est_latitude and _is_valid_lat(val)) or (not est_latitude and _is_valid_lon(val)) else None
        except (ValueError, TypeError):
            return None

    # --- Cas 3 : Direction + décimal (6.3658183 N) ---
    m = re.match(r"^\s*(-?[\d.,]+)\s*([NSEW])\s*$", s, re.IGNORECASE)
    if m:
        val = _to_float(m.group(1))
        direction = m.group(2).upper()
        if val is None:
            return None
        if direction in ("S", "W"):
            val = -abs(val)
        return val if (est_latitude and _is_valid_lat(val)) or (not est_latitude and _is_valid_lon(val)) else None

    # --- Cas 4 : Décimal simple (6.3658183 ou 6,3658183) ---
    val = _to_float(s)
    if val is not None:
        return val if (est_latitude and _is_valid_lat(val)) or (not est_latitude and _is_valid_lon(val)) else None

    return None


def parser_coordonnees(
    lat_brut: Any,
    lon_brut: Any,
) -> tuple[float | None, float | None]:
    """
    Parse un couple (lat, lon).
    Détecte automatiquement si l'ordre est inversé (lat/lon vs lon/lat)
    en se basant sur les bornes WGS84 et la position de la Côte d'Ivoire.
    """
    lat = parser_une_coordonnee(lat_brut, est_latitude=True)
    lon = parser_une_coordonnee(lon_brut, est_latitude=False)

    # Cas normal : lat valide, lon valide
    if lat is not None and lon is not None:
        # Détection d'inversion : en Côte d'Ivoire, lat ∈ [4, 11], lon ∈ [-9, -2]
        # Si lat < 0 et lon > 0, c'est probablement inversé
        if lat < 0 and lon > 0:
            lat, lon = lon, lat
        return lat, lon

    # Cas inverse : essayer lon/lat
    lat2 = parser_une_coordonnee(lon_brut, est_latitude=True)
    lon2 = parser_une_coordonnee(lat_brut, est_latitude=False)
    if lat2 is not None and lon2 is not None:
        return lat2, lon2

    return None, None