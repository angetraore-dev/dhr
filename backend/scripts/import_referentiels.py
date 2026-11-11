"""
Import des localités depuis fichier1.xlsx (feuille 'Localités').
Usage : docker compose exec backend python -u /app/scripts/import_referentiels.py /app/tests/fixtures/fichier1.xlsx
"""
from __future__ import annotations

import sys
import traceback

sys.path.insert(0, "/app")

from app.db import SessionLocal
from app.services.import_localites import importer_localites


def main(chemin: str) -> None:
    db = SessionLocal()
    try:
        print(f"\n{'='*70}")
        print(f"Import des localités depuis {chemin}")
        print(f"{'='*70}")

        stats = importer_localites(db, chemin, nom_feuille="Localités", header_row=1)
        db.commit()

        print("\nRésultat :")
        print(f"  Lignes traitées : {stats['nb_lignes']}")
        print(f"  Localités créées : {stats['nb_localites_creees']}")
        print(f"  Localités existantes : {stats['nb_localites_existantes']}")
        print(f"  Erreurs : {stats['nb_erreurs']}")

    except Exception:
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python import_localites.py <fichier.xlsx>")
        sys.exit(1)
    main(sys.argv[1])
