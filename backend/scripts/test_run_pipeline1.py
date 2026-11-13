"""
Test ultime du pipeline complet : upload/init → ingestion → rapprochement → consolidation.
Usage : docker compose exec backend python -u /app/scripts/test_run_pipeline.py /app/tests/fixtures/fichier1.xlsx 2>&1
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

sys.path.insert(0, "/app")

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Feuille, Fichier, LigneIngeree, Ouvrage, Source
from app.services.ingestion import detecter_feuilles
from app.services.run import creer_run, executer_pipeline


def main(chemin: str, mode: str = "complet") -> None:
    db = SessionLocal()
    try:
        path = Path(chemin)
        print(f"\n{'='*70}", flush=True)
        print(f"TEST PIPELINE COMPLET : {path.name} (mode={mode})", flush=True)
        print(f"{'='*70}", flush=True)

        if not path.exists():
            print(f"[X] Fichier introuvable : {chemin}", flush=True)
            sys.exit(1)

        # 1. Source
        source = db.scalar(select(Source).limit(1))
        if source is None:
            source = Source(nom="TEST_PIPELINE", type_source="autre", actif=True)
            db.add(source)
            db.flush()
        print(f"[1] Source : {source.nom} (id={source.id_source})", flush=True)

        # 2. Fichier & feuilles
        feuilles_info = detecter_feuilles(chemin)
        fichier = Fichier(
            id_source=source.id_source,
            nom_fichier_original=path.name,
            chemin_stockage=str(path),
            statut="en_attente",
            nb_feuilles=len(feuilles_info),
        )
        db.add(fichier)
        db.flush()

        for fi in feuilles_info:
            db.add(
                Feuille(
                    id_fichier=fichier.id_fichier,
                    nom_feuille=fi.nom,
                    index_feuille=fi.index,
                    type_contenu="ouvrages",
                    nb_lignes=fi.nb_lignes,
                    statut_ingestion="en_attente",
                )
            )
        db.flush()
        print(
            f"[2] Fichier créé : id={fichier.id_fichier} ({len(feuilles_info)} feuilles)",
            flush=True,
        )

        # 3. Création du run via le service officiel
        run = creer_run(db, id_fichier=fichier.id_fichier, mode=mode)
        db.flush()
        print(f"[3] Run créé : id={run.id_run} (statut={run.statut})", flush=True)

        # 4. Exécution du pipeline complet (Ingestion -> Rapprochement -> Consolidation)
        print("[4] Lancement executer_pipeline...", flush=True)
        resultat = executer_pipeline(db, run.id_run)
        db.commit()
        print("[5] Pipeline exécuté et commité avec succès !", flush=True)

        # 5. Vérifications en base
        db.refresh(fichier)
        db.refresh(run)

        print(f"\n{'-'*70}", flush=True)
        print("BILAN DES STATUTS EN BASE :", flush=True)
        print(
            f"  Fichier #{fichier.id_fichier} : statut={fichier.statut!r}, "
            f"nb_lignes_total={fichier.nb_lignes_total}, date_ingestion={fichier.date_ingestion}",
            flush=True,
        )
        print(
            f"  Run #{run.id_run}     : statut={run.statut!r}, "
            f"nb_lignes_ingerees={run.nb_lignes_ingerees}, finished_at={run.finished_at}",
            flush=True,
        )

        print("\nDÉTAIL PAR ÉTAPE :", flush=True)
        ing = resultat["ingestion"]
        rap = resultat["rapprochement"]
        con = resultat["consolidation"]
        print(
            f"  1. Ingestion     : {ing['total_stockees']} stockées, {ing['total_rejetees']} rejetées",
            flush=True,
        )
        print(
            f"  2. Rapprochement : {rap['exact']} exact, {rap['alias']} alias, "
            f"{rap['trigram']} trigram, {rap['non_resolu']} non résolues",
            flush=True,
        )
        print(
            f"  3. Consolidation : {con['ouvrages_crees']} créés, {con['ouvrages_mis_a_jour']} mis à jour, "
            f"{con['doublons_suspects']} doublons suspects, {con['attributs_indetermines']} indéterminés",
            flush=True,
        )

        rows_qualite = db.execute(
            select(LigneIngeree.statut_qualite, func.count())
            .where(LigneIngeree.id_run == run.id_run)
            .group_by(LigneIngeree.statut_qualite)
        ).all()
        print("\nRÉPARTITION QUALITÉ (ligne_ingeree) :", flush=True)
        for statut, count in rows_qualite:
            print(f"  - {statut} : {count}", flush=True)

        total_ouvrages = db.scalar(select(func.count()).select_from(Ouvrage)) or 0
        print(f"\nTOTAL OUVRAGES EN BASE : {total_ouvrages}", flush=True)
        print(f"{'='*70}\n", flush=True)

    except Exception as e:
        print(f"\n[X] ÉCHEC DU PIPELINE : {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python test_run_pipeline.py <fichier.xlsx> [complet|echantillon]")
        sys.exit(1)
    mode_arg = sys.argv[2] if len(sys.argv) >= 3 else "complet"
    main(sys.argv[1], mode=mode_arg)
