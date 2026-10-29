
---

# Handoff — Projet DHR (v2.3)

**Date** : 2026-10-29
**Version** : 2.3 (Phase 1, 2, 3, 5 terminées ; Phase 4 en cours)
**Objet** : Centralisation des ouvrages hydrauliques ruraux pour la Direction de l'Hydraulique Rurale (DHR)
**Repo** : `C:\Users\hp\PhpstormProjects\dhr` (Windows, PowerShell)

---

## 1. Contexte métier

La DHR reçoit des fichiers Excel hétérogènes (ONEP, SODECI, UNICEF, BAD, LONACI, État) contenant des données sur les ouvrages hydrauliques ruraux, les CGPE et les financements. Elle veut centraliser ces données dans une base PostgreSQL/PostGIS et disposer d'une UI cartographique (vue satellite) et d'un export Excel/CSV.

**MVP** : lecture + ingestion + carto + export. L'écriture manuelle et l'analytique avancée sont hors scope.

---

## 2. État d'avancement

### ✅ Terminé

| Phase | Contenu | Statut |
|---|---|---|
| **Conception** | MCDR, MLDR, UML, `schema.sql`, `openapi.yaml`, conventions metadata | ✅ |
| **Phase 1 — Infrastructure** | Docker Compose (Postgres/PostGIS + FastAPI + Vite), config, db, entrypoint | ✅ |
| **Phase 2 — Modèles + migration** | 13 tables SQLAlchemy, migration Alembic `a3187e43649b` complétée | ✅ |
| **Phase 3 — API lecture** | 18 endpoints (référentiels, fichiers, ouvrages, CGPE, carto, qualité) | ✅ |
| **Phase 5 — Export** | Excel XlsxWriter + Synthèse KPI + CSV, colonne N°, limite 413 (20 endpoints) | ✅ |

### 🔄 En cours — Phase 4 (Ingestion)

| Étape | Contenu | Statut |
|---|---|---|
| **4.1a — Service coordonnées** | `services/coordonnees.py` (décimal, DMS compact, DMS explicite) | ✅ |
| **4.1b — Service ingestion** | `services/ingestion.py` (parsing, mapping, extraction) | ✅ |
| **4.1c — Test fichier1** | 3 511 lignes, 100 % coordonnées | ✅ |
| **4.1d — Test fichier2** | 1 307 lignes, 100 % coordonnées (DMS compact) | ✅ |
| **4.1e — Test fichier3** | 2 357 lignes, **3,1 % coordonnées** (❌ bug) | 🔄 |
| **4.2 — Rapprochement localités** | `services/rapprochement.py` | ⏳ |
| **4.3 — Routers upload + runs** | `POST /fichiers`, `POST /fichiers/{id}/runs`, `GET /runs/{id}` | ⏳ |
| **4.4 — Routers lignes + tests** | `GET /feuilles/{id}/lignes`, `GET /runs/{id}/lignes`, `GET /lignes/{id}` | ⏳ |

### ⏳ À faire

| Phase | Contenu |
|---|---|
| **Phase 6 — Front** | React + Vite + Leaflet + pages Fichiers/Carte/Liste/Qualité + **UI de mapping** |
| **Phase 7 — Tests** | Tests d'API, d'ingestion, d'export |

---

## 3. Architecture

### 3.1 Stack

| Couche | Technologie | Version |
|---|---|---|
| Base de données | PostgreSQL + PostGIS | 16 + 3.4 |
| Back-end | Python + FastAPI | 3.12 + 0.115 |
| ORM | SQLAlchemy + GeoAlchemy2 | 2.0 + 0.16 |
| Validation | Pydantic | 2.9 |
| Migrations | Alembic | 1.13 |
| Parsing Excel | openpyxl | 3.1 |
| Export Excel | XlsxWriter | 3.2 |
| Auth | python-jose (JWT) + API key | — |
| Front-end | React + Vite + TypeScript | 18 + 5.4 |
| UI | Tailwind + shadcn/ui | 3.4 |
| Carto | Leaflet + Esri World Imagery | 1.9 |
| État API | TanStack Query | 5.59 |
| Tableaux | TanStack Table | 8.20 |
| Conteneurs | Docker Compose | — |

### 3.2 Arborescence actuelle

```
dhr/
├── docker-compose.yml                (3 services + volumes scripts/tests montés)
├── .env.example
├── .gitignore
├── docs/
│   ├── mcdr.puml
│   ├── mldr.md                       (v1.2)
│   ├── mcd.puml
│   ├── openapi.yaml                  (v1.2, 25 endpoints)
│   ├── metadata_conventions.md
│   └── HANDOFF.md                    (ce doc)
├── sql/
│   └── schema.sql                    (documentation, non monté)
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh                 (attente DB + alembic upgrade + uvicorn)
│   ├── pyproject.toml                (+ xlsxwriter)
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py                    (filtre NOS_TABLES strict)
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── a3187e43649b_initial_schema.py    (complétée manuellement)
│   └── app/
│       ├── main.py                   (ORJSONResponse utf-8 + 5 routers)
│       ├── config.py
│       ├── db.py
│       ├── models.py                 (13 tables)
│       ├── auth.py                   (API key + JWT)
│       ├── deps.py                   (OffsetPagination, CursorPagination, OuvrageFilters)
│       ├── schemas/
│       │   ├── common.py, geo.py, referentiels.py, fichiers.py, ingestion.py, ouvrages.py
│       ├── routers/
│       │   ├── referentiels.py       (6 endpoints)
│       │   ├── fichiers.py           (3 endpoints)
│       │   ├── ouvrages.py           (2 + 2 export, réordonné)
│       │   ├── carto.py              (3 GeoJSON, découplé)
│       │   └── qualite.py            (1)
│       └── services/
│           ├── coordonnees.py        (parser lat/lon)
│           ├── ingestion.py          (parsing Excel)
│           └── export.py             (XlsxWriter + CSV)
├── scripts/
│   ├── inventaire_fichiers.py
│   ├── test_ingestion.py
│   └── test_ingestion_reelle.py
└── tests/
    └── fixtures/
        ├── fichier1.xlsx             (1,6 Mo, 5 feuilles, 3511 lignes)
        ├── fichier2.xlsx             (272 Ko, 1 feuille, 1307 lignes)
        └── fichier3.xlsx             (786 Ko, 1 feuille, 2357 lignes, header_row=7)
```

### 3.3 Modèle de données (13 tables)

**Référentiels** : `source`, `type_ouvrage`, `ref_geo_admin` (hiérarchique), `localite`, `localite_alias`
**Ingestion** : `fichier`, `feuille`, `ingestion_run`, `ligne_ingeree`
**Métier** : `ouvrage`, `cgpe`, `projet_financement`, `ouvrage_projet`

**Contrainte** : `UNIQUE (id_feuille, id_run, num_ligne_source)` sur `ligne_ingeree` (migration `xxxx_fix_uq_ligne_run_num_add_id_feuille` à créer si pas déjà fait).

### 3.4 Décisions de conception figées

| Décision | Raison |
|---|---|
| `hash_sha256` **non unique** | Réingestion légitime |
| `code_ouvrage` **nullable, non unique** | Pas d'identifiant métier stable |
| `UNIQUE (id_feuille, id_run, num_ligne_source)` | Plusieurs feuilles + plusieurs runs |
| `metadata JSONB` sur `localite`, `ouvrage`, `cgpe` | Colonnes non mappées |
| `donnees_brutes JSONB` sur `ligne_ingeree` | Source brute immuable |
| Colonnes générées `geom` | Via `geom_from_latlon` STORED |
| `geom_from_latlon` STRICT + rejet (0,0) | Éviter coordonnées aberrantes |
| Extensions : `postgis`, `fuzzystrmatch`, `unaccent`, `pg_trgm` | Pas `postgis_topology` |
| Auth : API key (lecture) + JWT (écriture) | Séparation lecture/écriture |
| Pagination : offset (petites listes) / cursor (lignes, ouvrages) | Adapter au volume |
| Export : XlsxWriter + Synthèse KPI + colonne N° | Meilleur que openpyxl write_only |
| **Mapping automatique + UI de validation** | Fichiers futurs imprévisibles |
| **Option A validée** : MVP simple, UI de mapping en Phase 6 | Priorité à l'ingestion |

---

## 4. Contrat d'API (25 endpoints)

Base : `http://localhost:8000/v1`

| Méthode | Endpoint | Auth | Statut |
|---|---|---|---|
| GET | `/sources`, `/types-ouvrage`, `/ref-geo`, `/ref-geo/{id}/chemin`, `/localites`, `/localites/{id}` | API key | ✅ |
| GET | `/fichiers`, `/fichiers/{id}`, `/fichiers/{id}/feuilles` | API key | ✅ |
| GET | `/ouvrages`, `/ouvrages/{id}`, `/cgpe/{id}` | API key | ✅ |
| GET | `/ouvrages/export`, `/ouvrages/export.csv` | API key | ✅ |
| GET | `/carto/fichiers/{id}/points`, `/carto/tous/points`, `/carto/fichiers/{id}/points.geojson` | API key | ✅ |
| GET | `/qualite/fichiers/{id}` | API key | ✅ |
| **POST** | **`/fichiers`** (upload) | JWT | ⏳ Phase 4.3 |
| **POST** | **`/fichiers/{id}/runs`** | JWT | ⏳ Phase 4.3 |
| **GET** | **`/fichiers/{id}/runs`**, **`/runs/{id}`** | API key | ⏳ Phase 4.3 |
| **GET** | **`/feuilles/{id}/lignes`**, **`/runs/{id}/lignes`**, **`/lignes/{id}`** | API key | ⏳ Phase 4.4 |

**Détail complet** dans `docs/openapi.yaml`.

---

## 5. Démarrage

### 5.1 Première installation

```powershell
git clone <url> dhr
cd dhr
Copy-Item .env.example .env
docker compose up -d --build
docker compose ps   # 3 services healthy
curl.exe http://localhost:8000/health   # {"status":"ok","db":true}
```

### 5.2 Commandes utiles

```powershell
# Logs
docker compose logs -f backend
docker compose logs --tail 50 backend

# Shell
docker compose exec backend bash
docker compose exec db psql -U dhr -d dhr

# Redémarrer
docker compose restart backend
docker compose up -d --force-recreate backend

# Reset DB (⚠️ perte de données)
docker compose down -v
docker compose up -d

# Alembic
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
docker compose exec backend alembic revision -m "description"
```

### 5.3 Tests d'API

```powershell
$apiKey = "dhr_dev_read_key_change_me"

# Sources (6 seedées)
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/sources

# Types d'ouvrage (5 seedés)
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/types-ouvrage

# Ouvrages
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/ouvrages

# Export Excel
curl.exe -H "X-API-Key: $apiKey" -o test.xlsx http://localhost:8000/v1/ouvrages/export

# Export CSV
curl.exe -H "X-API-Key: $apiKey" -o test.csv http://localhost:8000/v1/ouvrages/export.csv

# Test 401 (sans clé)
curl.exe -i http://localhost:8000/v1/sources
```

---

## 6. Point de blocage actuel — Fichier3

### 6.1 Symptôme

Après ingestion de `fichier3.xlsx` (2 357 lignes), seules **72 lignes (3,1 %)** ont des coordonnées. Les 2 285 autres ont `latitude_decimal = NULL` et `longitude_decimal = NULL`.

### 6.2 Cause identifiée

Les clés dans `donnees_brutes` pour fichier3 sont **`LATITUDE\nOUVRAGE`** (avec `\n` littéral, pas un espace). Vérifié par :

```sql
SELECT DISTINCT k FROM ligne_ingeree, jsonb_object_keys(donnees_brutes) AS k 
WHERE id_feuille = 3 AND k ILIKE '%LAT%';
-- Résultat : 'LATITUDE  +  OUVRAGE' (avec \n)
```

Or, dans `_extraire_lignes`, on écrit `brut[mapping.entetes[col_idx]] = val` — donc la clé est `LATITUDE\nOUVRAGE`.

**Mais** la valeur lue par openpyxl pour cette colonne est probablement **vide** (ou mal lue), car `lat_brut` est `None` dans `parser_coordonnees`.

### 6.3 Hypothèse

Le problème est dans **la lecture de la ligne** : soit le mapping de colonne est faux (index décalé), soit openpyxl lit mal les cellules avec `\n` dans l'entête.

### 6.4 Test à faire

```powershell
# Voir les valeurs brutes des 3 premières lignes de fichier3
docker compose exec backend python -c "
import sys; sys.path.insert(0, '/app')
import openpyxl
wb = openpyxl.load_workbook('/app/tests/fixtures/fichier3.xlsx', read_only=True, data_only=True)
ws = wb.active
for i, row in enumerate(ws.iter_rows(min_row=7, max_row=10, values_only=True), start=7):
    print(f'Ligne {i}: [24]={row[24]!r}, [25]={row[25]!r}')
wb.close()
"
```

**Attendu** : voir les valeurs réelles de `LONGITUDE\nOUVRAGE` (col 24) et `LATITUDE\nOUVRAGE` (col 25).

### 6.5 Pistes de correction

1. **Vérifier que `_extraire_lignes` lit bien les colonnes 24 et 25** pour chaque ligne.
2. **Vérifier que `parser_coordonnees` reçoit bien les valeurs** (ajouter des `print` de debug).
3. **Adapter `parser_une_coordonnee`** si les valeurs sont dans un format non prévu (ex. `7 1 21 N` sans symboles).
4. **Vérifier `_analyser_entetes`** : `pat.search(_normaliser(entete))` doit matcher `latitude ouvrage` (avec espace, après normalisation de `\n`).

### 6.6 Note importante

La valeur `7°1'21.29.20"N` (ligne 1190) est **corrompue** (DMS invalide, sec > 60). Elle sera `None` après correction. C'est **normal** et attendu (1 ligne sur 2 357).

---

## 7. Dette technique / points ouverts

| # | Point | Impact | À traiter |
|---|---|---|---|
| 1 | **Fichier3 : 3,1 % coordonnées** | Ingestion | **En cours** |
| 2 | **UI de mapping** (Option A validée) | Frontend | Phase 6 |
| 3 | **Table `mapping_feuille`** | Backend | Option B (après MVP) |
| 4 | Déploiement prod (VPS vs cloud) | Infra | V2 |
| 5 | Nom de domaine réel | Config | Prod |
| 6 | Politique de rétention fichiers | Stockage | V2 |
| 7 | Gestion utilisateurs (table vs config) | Auth | Config MVP |
| 8 | Rapprochement localités (trigram) | Ingestion | Phase 4.2 |
| 9 | `localite.metadata_` vs `metadata` | Schémas | Résolu via `loc.metadata_` |
| 10 | `Localite.geom_centre` non sérialisé | Schémas | V2 |

---

## 8. Historique des versions

| Version | Date | Changement |
|---|---|---|
| 1.0 | 2026-10-23 | Conception initiale (23 endpoints) |
| 1.1 | 2026-10-23 | Ajout `metadata` (23 endpoints) |
| 1.2 | 2026-10-26 | Vue liste + export (25 endpoints) |
| 2.0 | 2026-10-27 | Phase 1-2 terminées |
| 2.1 | 2026-10-27 | Phase 3 terminée (18 endpoints) |
| 2.2 | 2026-10-28 | Phase 5 terminée (20 endpoints) |
| 2.3 | 2026-10-29 | Phase 4 en cours (ingestion fichier1 ✅, fichier2 ✅, fichier3 🔄) |

---

## 9. Prochaine action immédiate

**Débloquer fichier3** :

1. Exécuter le test de la section 6.4 pour voir les valeurs brutes des colonnes 24 et 25.
2. Identifier pourquoi `parser_coordonnees` retourne `None` (mapping ? lecture ? format ?).
3. Corriger `_extraire_lignes` ou `parser_une_coordonnee`.
4. Relancer `test_ingestion_reelle.py` sur fichier3.
5. Valider : `SELECT COUNT(*) FILTER (WHERE latitude_decimal IS NULL) FROM ligne_ingeree WHERE id_feuille = 3;` → doit être ≈ 1 (la ligne 1190).

**Puis** :
- **Phase 4.2** : `services/rapprochement.py` (trigram + unaccent + alias)
- **Phase 4.3** : `routers/fichiers.py` (upload) + `routers/ingestion.py` (runs)
- **Phase 4.4** : `routers/ingestion.py` (lignes) + tests
- **Phase 6** : Frontend (avec UI de mapping)

---

## 10. Commandes de reprise dans une nouvelle conversation

Pour reprendre, dire :

> « Je reprends le projet DHR. Voici le handoff (coller ce document). Nous en étions à la Phase 4.1e : fichier3 ingéré mais seulement 3,1 % de coordonnées. Aide-moi à débloquer. »

Le nouvel assistant aura tout le contexte pour continuer.

---

*Handoff rédigé le 2026-10-29. Toute modification du contrat d'API ou du schéma doit être répercutée dans les 5 livrables de conception (`mcdr.puml`, `mldr.md`, `mcd.puml`, `openapi.yaml`, `metadata_conventions.md`) avant implémentation.*