"""
Test manuel d'ingestion : parse un fichier Excel sans passer par l'API.
Usage : python /app/scripts/test_ingestion.py /app/tests/fixtures/fichier1.xlsx [header_row]
"""
import sys
from pathlib import Path

# Ajouter /app au PYTHONPATH (pour import app.*)
sys.path.insert(0, "/app")

from app.services.ingestion import detecter_feuilles, _analyser_entetes


def test(chemin: str, header_row_force: int | None = None) -> None:
    path = Path(chemin)
    print(f"\n{'='*70}")
    print(f"Test : {path.name}")
    print(f"{'='*70}")

    feuilles = detecter_feuilles(chemin, header_row_force)
    for f in feuilles:
        print(f"\n  Feuille '{f.nom}' (header_row={f.header_row}, {f.nb_lignes} lignes)")

        mapping = _analyser_entetes(f.entetes, f.index, f.header_row)
        print(f"    Colonnes mappées ({len(mapping.colonnes_mappees)}) :")
        for idx, champ in sorted(mapping.colonnes_mappees.items()):
            entete = f.entetes[idx] if idx < len(f.entetes) else "?"
            print(f"      [{idx}] {entete[:50]!r} → {champ}")

        print(f"    Colonnes non mappées ({len(mapping.colonnes_non_mappees)}) :")
        for h in mapping.colonnes_non_mappees[:5]:
            print(f"      {h[:70]!r}")
        if len(mapping.colonnes_non_mappees) > 5:
            print(f"      ... et {len(mapping.colonnes_non_mappees) - 5} autres")

    print("\n  → Mapping OK pour toutes les feuilles")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python test_ingestion.py <fichier.xlsx> [header_row]")
        sys.exit(1)
    h = int(sys.argv[2]) if len(sys.argv) > 2 else None
    test(sys.argv[1], h)