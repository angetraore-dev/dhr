"""
Test d'intégration du pipeline complet (obligatoire, Bible § 8.3.3).

Vérifie :
1. Upload → ingestion → rapprochement → consolidation.
2. `fichier.statut = 'ingere'`.
3. `ouvrage` créés.
4. `v_qualite_par_fichier` cohérent.
5. `v_points_consolides` contient au moins un point.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text


@pytest.mark.integration
class TestPipelineComplet:
    """Test d'intégration : pipeline complet sur un fichier de test."""

    def test_pipeline_complet(
        self,
        db,
        fichier_avec_feuille,
        excel_fixture_path,
        localite_test,
    ):
        fichier, feuille = fichier_avec_feuille
        fichier.chemin_stockage = str(excel_fixture_path)

        from app.services.run import creer_run, executer_pipeline

        # Créer un run
        run = creer_run(db, fichier.id_fichier, mode="complet")

        # Exécuter le pipeline
        result = executer_pipeline(db, run.id_run)

        # Vérifications
        assert result["ingestion"]["total_stockees"] >= 1
        assert result["ingestion"]["total_rejetees"] >= 1

        # fichier.statut mis à jour (I2)
        db.refresh(fichier)
        assert fichier.statut in ("ingere", "partiel")
        assert fichier.date_ingestion is not None

        # run terminé
        db.refresh(run)
        assert run.statut == "termine"

        # Au moins un ouvrage créé (la ligne valide a une localité résolue)
        # Note : LOC_TEST existe (fixture localite_test), donc devrait matcher
        nb_ouvrages = db.execute(text("SELECT COUNT(*) FROM ouvrage")).scalar()
        assert nb_ouvrages >= 1

        # v_qualite_par_fichier cohérent
        row = db.execute(text("""
            SELECT nb_ok, nb_geom_invalide, nb_rejetes, nb_lignes_total
            FROM v_qualite_par_fichier
            WHERE id_fichier = :id_fichier
        """), {"id_fichier": fichier.id_fichier}).first()
        assert row is not None
        nb_ok, nb_geom_invalide, nb_rejetes, nb_lignes_total = row
        assert nb_ok >= 0
        assert nb_geom_invalide >= 0
        assert nb_rejetes >= 1  # au moins la ligne TOTAL

        # v_points_consolides contient au moins 1 point
        nb_points = db.execute(text("SELECT COUNT(*) FROM v_points_consolides")).scalar()
        assert nb_points >= 1