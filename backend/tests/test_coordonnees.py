"""
Tests du service de coordonnées.

Couvre les formats :
- Décimal anglo-saxon (7.5)
- Décimal français (7,5)
- DMS compact (075225)
- DMS explicite (7°52'25"N)
- Direction (7.5 N)
- Inversion lat/lon
- (0, 0)
- Hors bornes
- NULL
"""
from __future__ import annotations

import pytest

from app.services.coordonnees import parser_coordonnees, parser_une_coordonnee


class TestParserUneCoordonnee:
    """Tests de `parser_une_coordonnee` (une seule coordonnée)."""

    def test_decimal_anglo_saxon(self):
        assert parser_une_coordonnee("7.5", est_latitude=True) == 7.5
        assert parser_une_coordonnee("-5.5", est_latitude=False) == -5.5

    def test_decimal_francais(self):
        assert parser_une_coordonnee("7,5", est_latitude=True) == 7.5
        assert parser_une_coordonnee("-5,5", est_latitude=False) == -5.5

    def test_float_natif(self):
        assert parser_une_coordonnee(7.5, est_latitude=True) == 7.5
        assert parser_une_coordonnee(-5.5, est_latitude=False) == -5.5

    def test_dms_compact(self):
        # 075225 = 07°52'25" (mais signe forcé par _corriger_ci)
        assert parser_une_coordonnee("075225", est_latitude=True) == pytest.approx(7.8736, abs=1e-3)

    def test_dms_explicite(self):
        assert parser_une_coordonnee("7°52'25\"N", est_latitude=True) == pytest.approx(7.8736, abs=1e-3)
        assert parser_une_coordonnee("5°30'0\"W", est_latitude=False) == pytest.approx(-5.5, abs=1e-3)

    def test_direction(self):
        assert parser_une_coordonnee("7.5 N", est_latitude=True) == 7.5
        assert parser_une_coordonnee("5.5 W", est_latitude=False) == -5.5

    def test_null(self):
        assert parser_une_coordonnee(None, est_latitude=True) is None
        assert parser_une_coordonnee("", est_latitude=True) is None

    def test_hors_bornes(self):
        assert parser_une_coordonnee(100, est_latitude=True) is None
        assert parser_une_coordonnee(-200, est_latitude=False) is None

    def test_invalide(self):
        assert parser_une_coordonnee("abc", est_latitude=True) is None


class TestParserCoordonnees:
    """Tests de `parser_coordonnees` (couple lat/lon)."""

    def test_couple_valide(self):
        lat, lon = parser_coordonnees(7.5, -5.5)
        assert lat == 7.5
        assert lon == -5.5

    def test_inversion_lat_lon(self):
        # (lat=-5.5, lon=7.5) → inversé
        lat, lon = parser_coordonnees(-5.5, 7.5)
        assert lat == 7.5
        assert lon == -5.5

    def test_signe_force_ci(self):
        # (7.5, 5.5) → lon doit être forcée à -5.5 (Côte d'Ivoire)
        lat, lon = parser_coordonnees(7.5, 5.5)
        assert lat == 7.5
        assert lon == -5.5

    def test_zero_zero(self):
        lat, lon = parser_coordonnees(0, 0)
        assert lat is None
        assert lon is None

    def test_null(self):
        lat, lon = parser_coordonnees(None, None)
        assert lat is None
        assert lon is None

    def test_lat_manquante(self):
        lat, lon = parser_coordonnees(None, -5.5)
        assert lat is None
        assert lon is None

    def test_dms_couple(self):
        lat, lon = parser_coordonnees("075225", "055225")
        assert lat == pytest.approx(7.8736, abs=1e-3)
        assert lon == pytest.approx(-5.8736, abs=1e-3)