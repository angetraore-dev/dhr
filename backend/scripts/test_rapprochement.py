"""
Test du rapprochement des localités sur un run.
Usage : python /app/scripts/test_rapprochement.py <id_run>
"""
import sys
sys.path.insert(0, "/app")

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import LigneIngeree
from app.services.rapprochement import rapprocher_lignes_run


def main(id_run: int) -> None:
    db = SessionLocal()
    try:
        print(f"\n{'='*70}")
        print(f"Rapprochement du run {id_run}")
        print(f"{'='*70}")

        stats = rapprocher_lignes_run(db, id_run, seuil_trigram=0.6)
        db.commit()

        print(f"\nRésultat du rapprochement :")
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
        print(f"\nStatuts en base :")
        for statut, count in rows:
            print(f"  {statut} : {count}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python test_rapprochement.py <id_run>")
        sys.exit(1)
    main(int(sys.argv[1]))