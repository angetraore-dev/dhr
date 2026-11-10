"""
Tests du service de rapprochement.

Couvre :
- Match exact (LOC_TEST → localité LOC_TEST).
- Match trigram (LOC_TES → localité LOC_TEST).
- Localité non résolue (INCONNU → localite_non_resolue).
- Format strict du message_qualite (I3).
"""
from __future__ import annotations

import pytest

from app.models import IngestionRun, LigneIngeree
from app.services.rapprochement import rapprocher_lignes_run


def _creer_ligne(db, id_feuille, id_run, localite_brute, statut="ok"):
    ligne = LigneIngeree(
        id_feuille=id_feuille,
        id_run=id_run,
        num_ligne_source=1,
        donnees_brutes={"Localité": localite_brute},
        localite_brute=localite_brute,
        latitude_decimal=7.5,
        longitude_decimal=-5.5,
        statut_qualite=statut,
    )
    db.add(ligne)
    db.flush()
    return ligne


class TestRapprochement:
    """Tests du rapprochement."""

    def test_match_exact(
        self, db, localite_test, fichier_avec_feuille
    ):
        fichier, feuille = fichier_avec_feuille
        run = IngestionRun(
            id_fichier=fichier.id_fichier, mode="complet", statut="en_cours"
        )
        db.add(run)
        db.flush()

        ligne = _creer_ligne(db, feuille.id_feuille, run.id_run, "LOC_TEST")

        stats = rapprocher_lignes_run(db, run.id_run)

        assert stats["exact"] == 1
        assert ligne.id_localite == localite_test.id_localite
        assert ligne.statut_qualite == "ok"

    def test_localite_non_resolue(
        self, db, localite_test, fichier_avec_feuille
    ):
        fichier, feuille = fichier_avec_feuille
        run = IngestionRun(
            id_fichier=fichier.id_fichier, mode="complet", statut="en_cours"
        )
        db.add(run)
        db.flush()

        ligne = _creer_ligne(
            db, feuille.id_feuille, run.id_run, "INCONNU_XYZ_123"
        )

        stats = rapprocher_lignes_run(db, run.id_run)

        assert stats["non_resolu"] == 1
        assert ligne.id_localite is None
        assert ligne.statut_qualite == "localite_non_resolue"

    def test_message_qualite_strict(
        self, db, localite_test, fichier_avec_feuille
    ):
        """I3 : message_qualite format strict, sans suffixe debug."""
        fichier, feuille = fichier_avec_feuille
        run = IngestionRun(
            id_fichier=fichier.id_fichier, mode="complet", statut="en_cours"
        )
        db.add(run)
        db.flush()

        ligne = _creer_ligne(
            db, feuille.id_feuille, run.id_run, "INCONNU_XYZ_123"
        )

        rapprocher_lignes_run(db, run.id_run)

        # Format strict, sans "(méthode: ...)"
        assert "Localité non résolue" in ligne.message_qualite
        assert "(méthode:" not in ligne.message_qualite

    def test_ligne_geom_invalide_ignoree(
        self, db, localite_test, fichier_avec_feuille
    ):
        """Les lignes geom_invalide ne sont pas rapprochées."""
        fichier, feuille = fichier_avec_feuille
        run = IngestionRun(
            id_fichier=fichier.id_fichier, mode="complet", statut="en_cours"
        )
        db.add(run)
        db.flush()

        ligne = _creer_ligne(
            db, feuille.id_feuille, run.id_run, "LOC_TEST", statut="geom_invalide"
        )

        stats = rapprocher_lignes_run(db, run.id_run)

        assert stats["total"] == 0  # pas traitée
        assert ligne.id_localite is None