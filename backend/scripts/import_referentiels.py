"""
Import des localités depuis un fichier Excel (feuille et entêtes auto-détectés).
Usage :
  docker compose exec backend python -u /app/scripts/import_referentiels.py /app/tests/fixtures/Forage.xlsx
  docker compose exec backend python -u /app/scripts/import_referentiels.py /app/tests/fixtures/fichier1.xlsx --feuille Localités
"""
from __future__ import annotations

import argparse
import sys
import traceback

sys.path.insert(0, "/app")

from app.db import SessionLocal
from app.services.import_localites import importer_localites


def main() -> None:
    parser = argparse.ArgumentParser(description="Import des localités dans le référentiel DHR.")
    parser.add_argument("chemin", type=str, help="Chemin vers le fichier Excel")
    parser.add_argument("--feuille", type=str, default=None, help="Nom de la feuille (auto-détecté si omis)")
    parser.add_argument("--header-row", type=int, default=None, help="Ligne d'entête (auto-détectée si omise)")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        print(f"\n{'='*70}")
        print(f"Import des localités depuis {args.chemin}")
        print(f"{'='*70}")

        stats = importer_localites(
            db,
            args.chemin,
            nom_feuille=args.feuille,
            header_row=args.header_row,
        )
        db.commit()

        print("\nRésultat :")
        print(f"  Feuille lue          : {stats['feuille']}")
        print(f"  Lignes traitées      : {stats['nb_lignes']}")
        print(f"  Localités créées     : {stats['nb_localites_creees']}")
        print(f"  Localités existantes : {stats['nb_localites_existantes']}")
        print(f"  Erreurs              : {stats['nb_erreurs']}")

    except Exception:
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
