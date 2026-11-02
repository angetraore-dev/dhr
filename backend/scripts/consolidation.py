"""
Consolidation : ligne_ingeree -> ouvrage.
Usage : python /app/scripts/consolidation.py <id_run>
docker compose exec backend python -u /app/scripts/consolidation.py 1 2>&1
"""
import sys
sys.path.insert(0, "/app")

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import LigneIngeree, Ouvrage
from app.services.consolidation import consolider_lignes_run


def main(id_run: int) -> None:
    db = SessionLocal()
    try:
        print(f"\n{'='*70}")
        print(f"Consolidation du run {id_run}")
        print(f"{'='*70}")

        stats = consolider_lignes_run(db, id_run)
        db.commit()

        print(f"\nRésultat :")
        print(f"  Lignes traitées : {stats['total_lignes']}")
        print(f"  Ouvrages créés : {stats['ouvrages_crees']}")
        print(f"  Ouvrages mis à jour : {stats['ouvrages_mis_a_jour']}")
        print(f"  Lignes ignorées : {stats['lignes_ignorees']}")
        print(f"  Erreurs : {stats['erreurs']}")

        # Stats en base
        total_ouvrages = db.scalar(select(func.count()).select_from(Ouvrage))
        total_lignes_consolidees = db.scalar(
            select(func.count()).select_from(LigneIngeree).where(
                LigneIngeree.id_run == id_run,
                LigneIngeree.id_ouvrage_consolide.isnot(None),
            )
        )
        print(f"\nEn base :")
        print(f"  Total ouvrages : {total_ouvrages}")
        print(f"  Lignes consolidées (run {id_run}) : {total_lignes_consolidees}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python consolidation.py <id_run>")
        sys.exit(1)
    main(int(sys.argv[1]))