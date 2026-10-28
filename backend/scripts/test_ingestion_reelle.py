"""
Test d'ingestion réelle : parse + insère en base.
Usage : python /app/scripts/test_ingestion_reelle.py /app/tests/fixtures/fichier1.xlsx
"""
import sys
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
        print(f"\n{'='*70}")
        print(f"Test d'ingestion réelle : {path.name}")
        print(f"{'='*70}")

        # Crée le Fichier + IngestionRun + Feuilles
        source = db.scalar(select(Source).limit(1))
        if source is None:
            source = Source(nom="TEST", type_source="autre", actif=True)
            db.add(source)
            db.flush()

        fichier = Fichier(
            id_source=source.id_source,
            nom_fichier_original=path.name,
            chemin_stockage=str(path),
            statut="en_attente",
        )
        db.add(fichier)
        db.flush()

        # Détecte les feuilles
        feuilles_info = detecter_feuilles(chemin)
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

        # Crée le run
        run = IngestionRun(
            id_fichier=fichier.id_fichier,
            mode="complet",
            statut="en_cours",
        )
        db.add(run)
        db.flush()

        # Ingrère
        resultat = ingerer_fichier(db, fichier, run, mode="complet")
        db.commit()

        print(f"\nRésultat :")
        print(f"  Total lignes ingérées : {resultat['total_lignes']}")
        print(f"  Statut du run : {run.statut}")

        # Vérifie en base
        total = db.scalar(select(func.count()).select_from(LigneIngeree).where(
            LigneIngeree.id_run == run.id_run
        ))
        print(f"  Lignes en base : {total}")

        # Stats de coordonnées
        avec_coords = db.scalar(select(func.count()).select_from(LigneIngeree).where(
            LigneIngeree.id_run == run.id_run,
            LigneIngeree.latitude_decimal.isnot(None),
            LigneIngeree.longitude_decimal.isnot(None),
        ))
        print(f"  Avec coordonnées : {avec_coords} ({avec_coords/total*100:.1f}%)" if total else "")

        # Affiche 3 exemples
        print(f"\n  3 premiers enregistrements :")
        lignes = db.scalars(select(LigneIngeree).where(
            LigneIngeree.id_run == run.id_run
        ).limit(3)).all()
        for l in lignes:
            print(f"    - localite={l.localite_brute!r}, lat={l.latitude_decimal}, lon={l.longitude_decimal}, type={l.type_ouvrage_brut!r}")

    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python test_ingestion_reelle.py <fichier.xlsx>")
        sys.exit(1)
    test(sys.argv[1])

"""
docker compose exec backend python /app/scripts/test_ingestion_reelle.py /app/tests/fixtures/fichier1.xlsx
docker compose exec backend python /app/scripts/test_ingestion_reelle.py /app/tests/fixtures/fichier2.xlsx
"""