"""
Supprime les opérations drop_table/drop_index sur les objets PostGIS
dans une migration Alembic générée.
"""
import re
import sys
from pathlib import Path

POSTGIS_TABLES = {
    "spatial_ref_sys", "layer", "topology",
    "addr", "addrfeat", "bg", "county", "county_lookup", "countysub_lookup",
    "cousub", "direction_lookup", "edges", "faces", "featnames",
    "geocode_settings", "geocode_settings_default", "loader_lookuptables",
    "loader_platform", "loader_variables", "pagc_gaz", "pagc_lex", "pagc_rules",
    "place", "place_lookup", "secondary_unit_lookup", "state", "state_lookup",
    "street_type_lookup", "tabblock", "tabblock20", "tract", "zcta5",
    "zip_lookup", "zip_lookup_all", "zip_lookup_base", "zip_state", "zip_state_loc",
}


def clean(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    cleaned = []
    removed = 0

    for line in lines:
        m = re.search(r"op\.drop_table\(['\"]([^'\"]+)['\"]", line)
        if m and m.group(1) in POSTGIS_TABLES:
            removed += 1
            continue
        if "op.drop_index(" in line and any(t in line for t in POSTGIS_TABLES):
            removed += 1
            continue
        cleaned.append(line)

    path.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
    print(f"Nettoyé : {removed} opérations supprimées dans {path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python clean_migration.py <chemin_migration.py>")
        sys.exit(1)
    clean(Path(sys.argv[1]))