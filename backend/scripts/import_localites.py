"""
Import des localités depuis fichier1.xlsx (feuille 'Localités').
Usage : python /app/scripts/import_localites.py /app/tests/fixtures/fichier1.xlsx
"""
import sys
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

        print(f"\nRésultat :")
        print(f"  Lignes traitées : {stats['nb_lignes']}")
        print(f"  Localités créées : {stats['nb_localites_creees']}")
        print(f"  Localités existantes : {stats['nb_localites_existantes']}")
        print(f"  Erreurs : {stats['nb_erreurs']}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python import_localites.py <fichier.xlsx>")
        sys.exit(1)
    main(sys.argv[1])