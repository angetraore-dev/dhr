"""
Test du rapprochement des localités sur un run.

Usage :
    python /app/scripts/test_rapprochement.py <id_run>
    python /app/scripts/test_rapprochement.py <chemin_fichier>

Exemples :
    python /app/scripts/test_rapprochement.py 56
    python /app/scripts/test_rapprochement.py /app/tests/fixtures/fichier1.xlsx
"""
from __future__ import annotations

import sys
import traceback

sys.path.insert(0, "/app")

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Fichier, IngestionRun, LigneIngeree
from app.services.rapprochement import rapprocher_lignes_run


def main(id_run: int) -> None:
    db = SessionLocal()
    try:
        print(f"\n{'='*70}")
        print(f"Rapprochement du run {id_run}")
        print(f"{'='*70}")
        stats = rapprocher_lignes_run(db, id_run, seuil_trigram=0.6)
        db.commit()

        print("\nRésultat du rapprochement :")
        print(f"  Total lignes : {stats['total']}")
        print(f"  Exact match : {stats['exact']}")
        print(f"  Alias : {stats['alias']}")
        print(f"  Trigram : {stats['trigram']}")
        print(f"  Non résolu : {stats['non_resolu']}")
        print(f"  Vide : {stats['vide']}")

        # Stats en base
        rows = db.execute(
            select(LigneIngeree.statut_qualite, func.count())
            .where(LigneIngeree.id_run == id_run)
            .group_by(LigneIngeree.statut_qualite)
        ).all()
        print("\nStatuts en base :")
        for statut, count in rows:
            print(f"  {statut} : {count}")

    except Exception:
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def _resolve_id_run(arg: str) -> int:
    """Résout un ID de run à partir d'un entier ou d'un chemin de fichier.

    Si `arg` est un chemin de fichier (.xlsx / .xls), on récupère le dernier
    run associé à ce fichier en base.
    """
    # Cas 1 : c'est un entier → ID de run direct
    try:
        return int(arg)
    except ValueError:
        pass

    # Cas 2 : c'est un chemin de fichier → récupérer le dernier run
    if not (arg.endswith(".xlsx") or arg.endswith(".xls")):
        print(f"Erreur : '{arg}' n'est ni un ID de run ni un fichier .xlsx.")
        print("Usage: test_rapprochement.py <id_run|chemin_fichier>")
        sys.exit(1)

    nom_fichier = arg.split("/")[-1].split("\\")[-1]  # gère / et \
    db = SessionLocal()
    try:
        fichier = db.scalar(
            select(Fichier)
            .where(Fichier.nom_fichier_original == nom_fichier)
            .order_by(Fichier.id_fichier.desc())
            .limit(1)
        )
        if fichier is None:
            print(f"Fichier '{nom_fichier}' introuvable en base.")
            sys.exit(1)

        run = db.scalar(
            select(IngestionRun)
            .where(IngestionRun.id_fichier == fichier.id_fichier)
            .order_by(IngestionRun.id_run.desc())
            .limit(1)
        )
        if run is None:
            print(f"Aucun run pour le fichier '{nom_fichier}'.")
            sys.exit(1)

        print(f"Fichier '{nom_fichier}' (id={fichier.id_fichier}) → dernier run #{run.id_run}")
        return run.id_run
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: test_rapprochement.py <id_run|chemin_fichier>")
        print("Exemple: test_rapprochement.py 56")
        print("Ou    : test_rapprochement.py /app/tests/fixtures/fichier1.xlsx")
        sys.exit(1)

    id_run = _resolve_id_run(sys.argv[1])
    main(id_run)