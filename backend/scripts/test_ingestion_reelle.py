"""
Test d'ingestion réelle : parse + insère en base.
Usage : docker compose exec backend python -u /app/scripts/test_ingestion_reelle.py /app/tests/fixtures/fichier1.xlsx 2>&1
"""
import sys
import traceback
from pathlib import Path

sys.path.insert(0, "/app")

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Feuille, Fichier, IngestionRun, LigneIngeree, Source
from app.services.ingestion import detecter_feuilles, ingerer_fichier


def test(chemin: str) -> None:
    db = SessionLocal()
    try:
        path = Path(chemin)
        print(f"\n{'='*70}", flush=True)
        print(f"Test d'ingestion réelle : {path.name}", flush=True)
        print(f"{'='*70}", flush=True)

        if not path.exists():
            print(f"[X] Fichier introuvable : {chemin}", flush=True)
            return

        # --- Source ---
        source = db.scalar(select(Source).limit(1))
        if source is None:
            source = Source(nom="TEST", type_source="autre", actif=True)
            db.add(source)
            db.flush()
        print(f"[1] Source : {source.nom}", flush=True)

        # --- Fichier ---
        fichier = Fichier(
            id_source=source.id_source,
            nom_fichier_original=path.name,
            chemin_stockage=str(path),
            statut="en_attente",
        )
        db.add(fichier)
        db.flush()
        print(f"[2] Fichier créé : id={fichier.id_fichier}", flush=True)

        # --- Détection des feuilles ---
        feuilles_info = detecter_feuilles(chemin)
        print(f"[3] {len(feuilles_info)} feuilles détectées", flush=True)
        for fi in feuilles_info:
            print(f"    - '{fi.nom}' ({fi.nb_lignes} lignes, header_row={fi.header_row})", flush=True)

        for fi in feuilles_info:
            feuille = Feuille(
                id_fichier=fichier.id_fichier,
                nom_feuille=fi.nom,
                index_feuille=fi.index,
                type_contenu="ouvrages",
                nb_lignes=fi.nb_lignes,
                statut_ingestion="en_attente",
            )
            db.add(feuille)
        db.flush()
        print(f"[4] {len(feuilles_info)} feuilles insérées en base", flush=True)

        # --- Run ---
        run = IngestionRun(
            id_fichier=fichier.id_fichier,
            mode="complet",
            statut="en_cours",
        )
        db.add(run)
        db.flush()
        print(f"[5] Run créé : id={run.id_run}", flush=True)

        # --- Ingestion ---
        print(f"[6] Lancement ingerer_fichier...", flush=True)
        resultat = ingerer_fichier(db, fichier, run, mode="complet")
        print(f"[7] Ingestion terminée : {resultat}", flush=True)

        # --- Commit ---
        db.commit()
        print(f"[8] Commit OK", flush=True)

        # --- Vérifications ---
        total = db.scalar(select(func.count()).select_from(LigneIngeree).where(
            LigneIngeree.id_run == run.id_run
        ))
        print(f"\n[9] Total lignes en base (run {run.id_run}) : {total}", flush=True)

        avec_coords = db.scalar(select(func.count()).select_from(LigneIngeree).where(
            LigneIngeree.id_run == run.id_run,
            LigneIngeree.latitude_decimal.isnot(None),
            LigneIngeree.longitude_decimal.isnot(None),
        ))
        if total:
            print(f"[10] Avec coordonnées : {avec_coords} ({avec_coords/total*100:.1f}%)", flush=True)

        # 3 exemples
        print(f"\n[11] 3 premiers enregistrements :", flush=True)
        lignes = db.scalars(select(LigneIngeree).where(
            LigneIngeree.id_run == run.id_run
        ).limit(3)).all()
        for l in lignes:
            print(f"    - localite={l.localite_brute!r}, lat={l.latitude_decimal}, lon={l.longitude_decimal}, type={l.type_ouvrage_brut!r}", flush=True)

    except Exception as e:
        print(f"\n[X] EXCEPTION : {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python test_ingestion_reelle.py <fichier.xlsx>")
        sys.exit(1)
    test(sys.argv[1])