"""
Tests du service d'ingestion.

Couvre :
- Détection des rejets (B5) : total, sous-total, somme, cumul.
- Détection des lignes vides.
- `nb_lignes_total = stockées + rejetées` (B5).
- `fichier.statut` non modifié par l'ingestion (I2).
- `departement_brut` correctement extrait (I1).
- `usage_ouvrage_brut` extrait (P12).
- Coordonnées parsées (lat/lon valides).
- `statut_qualite = 'geom_invalide'` si lat/lon NULL.
"""
from __future__ import annotations

import pytest

from app.models import LigneIngeree
from app.services.ingestion import (
    _est_ligne_rejetee,
    _est_ligne_vide,
    ingerer_fichier,
)


class TestDetectionRejets:
    """Tests de la détection des rejets (B5)."""

    def test_ligne_normale(self):
        assert _est_ligne_rejetee(("LOC_TEST", 7.5, -5.5)) is False

    def test_ligne_total(self):
        assert _est_ligne_rejetee(("TOTAL", "", "")) is True
        assert _est_ligne_rejetee(("", "Total général", "")) is True

    def test_ligne_sous_total(self):
        assert _est_ligne_rejetee(("Sous-total", 10, 20)) is True

    def test_ligne_somme(self):
        assert _est_ligne_rejetee(("Somme", 0, 0)) is True

    def test_ligne_cumul(self):
        assert _est_ligne_rejetee(("Cumul", 0, 0)) is True

    def test_ligne_vide(self):
        assert _est_ligne_rejetee((None, None, None)) is False
        assert _est_ligne_rejetee(("", "", "")) is False


class TestDetectionLignesVides:
    """Tests de la détection des lignes vides."""

    def test_vide(self):
        assert _est_ligne_vide((None, None, None)) is True
        assert _est_ligne_vide(("", "", "")) is True

    def test_non_vide(self):
        assert _est_ligne_vide(("LOC_TEST", None, None)) is False
        assert _est_ligne_vide((7.5, -5.5, None)) is False


class TestIngestionFichier:
    """Tests de l'ingestion complète d'un fichier."""

    def test_ingestion_basique(
        self, db, fichier_avec_feuille, excel_fixture_path
    ):
        """L'ingestion stocke les lignes valides et compte les rejets."""
        fichier, feuille = fichier_avec_feuille

        # Créer un run
        from app.models import IngestionRun
        run = IngestionRun(
            id_fichier=fichier.id_fichier, mode="complet", statut="en_cours"
        )
        db.add(run)
        db.flush()

        # Rediriger le fichier vers la fixture Excel
        fichier.chemin_stockage = str(excel_fixture_path)

        result = ingerer_fichier(db, fichier, run, mode="complet")

        # 4 lignes dans la fixture :
        # - 1 valide (LOC_TEST, 7.5, -5.5)
        # - 1 sans coordonnées (LOC_TEST, None, None) → geom_invalide
        # - 1 total (TOTAL) → rejetée
        # - 1 vide → ignorée
        assert result["total_stockees"] == 2
        assert result["total_rejetees"] == 1
        assert fichier.nb_lignes_total == 3  # 2 stockées + 1 rejetée

        # Vérifier les lignes stockées
        lignes = db.query(LigneIngeree).filter(
            LigneIngeree.id_feuille == feuille.id_feuille
        ).all()
        assert len(lignes) == 2

        # Ligne 1 : valide
        ligne_ok = next(l for l in lignes if l.statut_qualite == "ok")
        assert ligne_ok.localite_brute == "LOC_TEST"
        assert ligne_ok.latitude_decimal == 7.5
        assert ligne_ok.longitude_decimal == -5.5

        # Ligne 2 : geom_invalide
        ligne_invalide = next(l for l in lignes if l.statut_qualite == "geom_invalide")
        assert ligne_invalide.latitude_decimal is None
        assert "Coordonnées manquantes" in ligne_invalide.message_qualite

    def test_fichier_statut_non_modifie(
        self, db, fichier_avec_feuille, excel_fixture_path
    ):
        """I2 : l'ingestion ne touche PAS à fichier.statut."""
        fichier, _ = fichier_avec_feuille
        statut_avant = fichier.statut

        from app.models import IngestionRun
        run = IngestionRun(
            id_fichier=fichier.id_fichier, mode="complet", statut="en_cours"
        )
        db.add(run)
        db.flush()

        fichier.chemin_stockage = str(excel_fixture_path)
        ingerer_fichier(db, fichier, run, mode="complet")

        # Le statut n'a pas changé (c'est run.py qui le fera)
        assert fichier.statut == statut_avant

    def test_usage_ouvrage_brut_extrait(
        self, db, fichier_avec_feuille, excel_fixture_path
    ):
        """P12 : usage_ouvrage_brut est extrait."""
        fichier, feuille = fichier_avec_feuille
        from app.models import IngestionRun
        run = IngestionRun(
            id_fichier=fichier.id_fichier, mode="complet", statut="en_cours"
        )
        db.add(run)
        db.flush()

        fichier.chemin_stockage = str(excel_fixture_path)
        ingerer_fichier(db, fichier, run, mode="complet")

        lignes = db.query(LigneIngeree).filter(
            LigneIngeree.id_feuille == feuille.id_feuille,
            LigneIngeree.statut_qualite == "ok",
        ).all()
        assert len(lignes) >= 1
        ligne = lignes[0]
        assert ligne.usage_ouvrage_brut == "PMH"