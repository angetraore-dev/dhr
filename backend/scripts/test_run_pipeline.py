"""
Script de validation de bout en bout du pipeline d'ingestion DHR.

Rôle :
    Orchestre en une seule commande les trois étapes métier du pipeline via les
    services officiels (`creer_run` puis `executer_pipeline`) :
      1. Ingestion     (`app.services.ingestion.ingerer_fichier`)     : parsing Excel,
         détection des entêtes, filtrage des lignes vides et rejet des totaux.
      2. Rapprochement (`app.services.rapprochement.rapprocher_lignes_run`) : résolution
         des localités (exact -> alias -> trigrammes pg_trgm).
      3. Consolidation (`app.services.consolidation.consolider_lignes_run`) : dédoublonnage,
         normalisation métier (nature, alimentation, réalisation, état) et création
         ou mise à jour des ouvrages en base.
      4. Clôture       (`app.services.run.executer_pipeline`)         : mise à jour des
         statuts finaux (`run.statut = 'termine'`, `fichier.statut = 'ingere'`) et
         horodatages (`finished_at`, `date_ingestion`).

Cas d'usage supportés (mutuellement exclusifs) :
    - `--id-fichier <ID>` : lance un nouveau run sur un fichier déjà enregistré en base
      (utilise le mapping validé s'il existe, sinon le mapping automatique).
    - `--fichier <chemin>` : crée l'entrée `Fichier` et ses `Feuille` associées en base
      à partir d'un fichier `.xlsx`/`.xls` sur disque avant de lancer le pipeline.

Options disponibles :
    --id-fichier INT              ID d'un fichier existant dans la table `fichier`.
    --fichier PATH                Chemin absolu/relatif vers un fichier Excel sur disque.
    --id-feuille INT              Cible une seule feuille du fichier (optionnel).
    --mode {complet,echantillon,plage}
                                  Mode d'exécution du run (défaut : `complet`).
    --limite INT                  Nombre max de lignes à ingérer (requis si `--mode echantillon`).
    --debut INT                   Numéro de ligne Excel de début (requis si `--mode plage`, >= 1).
    --fin INT                     Numéro de ligne Excel de fin (requis si `--mode plage`, >= `--debut`).

Exemples de commandes (via Docker) :
    # 1. Exécuter le pipeline complet sur un fichier déjà en base (ex. ID 23) :
    docker compose exec backend python -u /app/scripts/test_run_pipeline.py --id-fichier 23

    # 2. Ingérer un nouveau fichier Excel de bout en bout en mode complet :
    docker compose exec backend python -u /app/scripts/test_run_pipeline.py --fichier /app/tests/fixtures/fichier1.xlsx

    # 3. Tester un échantillon de 50 lignes sur une feuille précise :
    docker compose exec backend python -u /app/scripts/test_run_pipeline.py --id-fichier 23 --id-feuille 45 --mode echantillon --limite 50

    # 4. Tester une plage de lignes (lignes 10 à 100) :
    docker compose exec backend python -u /app/scripts/test_run_pipeline.py --fichier /app/tests/fixtures/fichier1.xlsx --mode plage --debut 10 --fin 100

Effets en base de données :
    - Insère un enregistrement dans `ingestion_run` et les lignes dans `ligne_ingeree`.
    - Crée ou enrichit les enregistrements dans `ouvrage`.
    - Effectue un `commit()` en cas de succès ou un `rollback()` complet en cas d'erreur.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

sys.path.insert(0, "/app")

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Feuille, Fichier, LigneIngeree, Ouvrage, Source
from app.services.ingestion import _hash_fichier, detecter_feuilles
from app.services.run import creer_run, executer_pipeline


def _preparer_fichier_depuis_chemin(db, chemin: str, force: bool = False) -> Fichier:
    path = Path(chemin)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")

    sha256 = _hash_fichier(path)
    taille = path.stat().st_size

    existant = db.scalar(select(Fichier).where(Fichier.hash_sha256 == sha256))
    if existant is not None and not force:
        raise ValueError(
            f"Conflit (409) : ce fichier existe déjà en base "
            f"(id_fichier={existant.id_fichier}, nom={existant.nom_fichier_original!r}). "
            f"Utilisez --id-fichier {existant.id_fichier} ou ajoutez --force."
        )

    source = db.scalar(select(Source).limit(1))
    if source is None:
        source = Source(nom="TEST_PIPELINE", type_source="autre", actif=True)
        db.add(source)
        db.flush()

    feuilles_info = detecter_feuilles(chemin)
    fichier = Fichier(
        id_source=source.id_source,
        nom_fichier_original=path.name,
        chemin_stockage=str(path),
        hash_sha256=sha256,
        taille_octets=taille,
        statut="en_attente",
        nb_feuilles=len(feuilles_info),
        est_reingestion=existant is not None,
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
    return fichier


def main() -> None:
    parser = argparse.ArgumentParser(description="Test complet du pipeline DHR.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id-fichier", type=int, help="ID d'un fichier déjà présent en base")
    group.add_argument("--fichier", type=str, help="Chemin vers un fichier .xlsx à insérer et tester")

    parser.add_argument("--id-feuille", type=int, default=None, help="ID d'une feuille spécifique (optionnel)")
    parser.add_argument(
        "--mode",
        choices=["complet", "echantillon", "plage"],
        default="complet",
        help="Mode d'ingestion (défaut: complet)",
    )
    parser.add_argument("--limite", type=int, default=None, help="Nombre de lignes (requis pour --mode echantillon)")
    parser.add_argument("--debut", type=int, default=None, help="Ligne de début (requis pour --mode plage)")
    parser.add_argument("--fin", type=int, default=None, help="Ligne de fin (requis pour --mode plage)")

    args = parser.parse_args()

    # Validation des paramètres selon le mode (alignée sur chk_run_mode_params)
    if args.mode == "echantillon" and (args.limite is None or args.limite <= 0):
        parser.error("--mode echantillon exige --limite > 0")
    if args.mode == "plage" and (args.debut is None or args.fin is None or args.debut < 1 or args.fin < args.debut):
        parser.error("--mode plage exige --debut >= 1 et --fin >= --debut")

    db = SessionLocal()
    try:
        print(f"\n{'='*70}", flush=True)
        print(f"TEST PIPELINE COMPLET (mode={args.mode})", flush=True)
        print(f"{'='*70}", flush=True)

        if args.id_fichier is not None:
            fichier = db.get(Fichier, args.id_fichier)
            if fichier is None:
                print(f"[X] Fichier id={args.id_fichier} introuvable en base.", flush=True)
                sys.exit(1)
            print(f"[1] Fichier existant récupéré : id={fichier.id_fichier} ({fichier.nom_fichier_original})", flush=True)
        else:
            fichier = _preparer_fichier_depuis_chemin(db, args.fichier)
            print(f"[1] Fichier créé depuis disque : id={fichier.id_fichier} ({fichier.nom_fichier_original})", flush=True)

        # Création du run
        run = creer_run(
            db,
            id_fichier=fichier.id_fichier,
            id_feuille=args.id_feuille,
            mode=args.mode,
            limite_lignes=args.limite,
            ligne_debut=args.debut,
            ligne_fin=args.fin,
        )
        db.flush()
        print(f"[2] Run créé : id={run.id_run} (id_feuille={args.id_feuille}, statut={run.statut})", flush=True)

        # Exécution des 3 étapes (Ingestion -> Rapprochement -> Consolidation)
        print("[3] Lancement executer_pipeline...", flush=True)
        resultat = executer_pipeline(db, run.id_run)
        db.commit()
        print("[4] Pipeline terminé et commité !", flush=True)

        # Vérification des statuts finaux
        db.refresh(fichier)
        db.refresh(run)

        print(f"\n{'-'*70}", flush=True)
        print("STATUTS FINAUX EN BASE :", flush=True)
        print(f"  Fichier #{fichier.id_fichier} : statut={fichier.statut!r} | nb_lignes_total={fichier.nb_lignes_total}", flush=True)
        print(f"  Run #{run.id_run}     : statut={run.statut!r} | nb_lignes_ingerees={run.nb_lignes_ingerees} | finished_at={run.finished_at}", flush=True)

        ing = resultat["ingestion"]
        rap = resultat["rapprochement"]
        con = resultat["consolidation"]
        print("\nRÉSULTATS PAR ÉTAPE :", flush=True)
        print(f"  1. Ingestion     : {ing['total_stockees']} stockées, {ing['total_rejetees']} rejetées", flush=True)
        print(f"  2. Rapprochement : {rap['exact']} exact, {rap['alias']} alias, {rap['trigram']} trigram, {rap['non_resolu']} non résolues", flush=True)
        print(f"  3. Consolidation : {con['ouvrages_crees']} créés, {con['ouvrages_mis_a_jour']} mis à jour, {con['doublons_suspects']} doublons suspects", flush=True)

        rows_qualite = db.execute(
            select(LigneIngeree.statut_qualite, func.count())
            .where(LigneIngeree.id_run == run.id_run)
            .group_by(LigneIngeree.statut_qualite)
        ).all()
        print("\nQUALITÉ (ligne_ingeree) :", flush=True)
        for statut, count in rows_qualite:
            print(f"  - {statut} : {count}", flush=True)

        total_ouvrages = db.scalar(select(func.count()).select_from(Ouvrage)) or 0
        print(f"\nTOTAL OUVRAGES CONSOLIDÉS EN BASE : {total_ouvrages}", flush=True)
        print(f"{'='*70}\n", flush=True)

    except Exception as e:
        print(f"\n[X] ÉCHEC : {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
