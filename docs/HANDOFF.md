Voici la requête corrigée (l'erreur est due à `ORDER BY f.index_feuille` qui n'est pas dans le `GROUP BY`) :

```powershell
docker compose exec db psql -U dhr -d dhr -c "SELECT f.nom_feuille, f.index_feuille, COUNT(*) FROM ligne_ingeree l JOIN feuille f ON f.id_feuille = l.id_feuille WHERE f.id_fichier = 1 GROUP BY f.nom_feuille, f.index_feuille ORDER BY f.index_feuille;"
```

**Attendu** :
```
 nom_feuille       | index_feuille | count
-------------------+---------------+-------
 Localités         |             1 |  1132
 PMH               |             2 |  2103
 HVA               |             3 |    86
 PEA               |             4 |   172
 Autres_ouvrages   |             5 |    18
```

---

## Handoff — Projet DHR (v3.1)

**Date** : 2026-11-02
**Version** : 3.1 (Phase 4.1 ✅, Phase 4.2b ✅, Phase 4.2c ✅, Phase 4.2d ✅, Bug carto ✅)
**Objet** : Centralisation des ouvrages hydrauliques ruraux pour la Direction de l'Hydraulique Rurale (DHR)

---

## 1. Contexte métier

La DHR reçoit des fichiers Excel hétérogènes (ONEP, SODECI, UNICEF, BAD, LONACI, État) contenant des données sur les ouvrages hydrauliques ruraux, les CGPE et les financements. Elle veut centraliser ces données dans une base PostgreSQL/PostGIS et disposer d'une UI cartographique (vue satellite) et d'un export Excel/CSV.

**MVP** : lecture + ingestion + carto + export. L'écriture manuelle et l'analytique avancée sont hors scope.

---

## 2. État d'avancement

### ✅ Terminé

| Phase                             | Contenu                                                                                                                         | Statut |
|-----------------------------------|---------------------------------------------------------------------------------------------------------------------------------|--------|
| **Conception**                    | MCDR, MLDR, UML, `schema.sql`, `openapi.yaml`, conventions metadata                                                             | ✅      |
| **Phase 1 — Infrastructure**      | Docker Compose (Postgres/PostGIS + FastAPI + Vite), config, db, entrypoint                                                      | ✅      |
| **Phase 2 — Modèles + migration** | 13 tables SQLAlchemy, migrations Alembic (dont `mapping_feuille`)                                                               | ✅      |
| **Phase 3 — API lecture**         | 18 endpoints (référentiels, fichiers, ouvrages, CGPE, carto, qualité)                                                           | ✅      |
| **Phase 5 — Export**              | Excel XlsxWriter + Synthèse KPI + CSV, colonne N°, limite 413                                                                   | ✅      |
| **Phase 4.1 — Ingestion**         | `services/coordonnees.py`, `services/ingestion.py`, 3 fichiers testés (7 175 lignes)                                            | ✅      |
| **Phase 4.2a — Import localités** | `services/import_localites.py` (891 localités)                                                                                  | ✅      |
| **Phase 4.2b — Mapping UI**       | Table `mapping_feuille`, endpoints `GET /mapping-proposal` / `PUT /mapping`, import circulaire corrigé (`services/patterns.py`) | ✅      |
| **Phase 4.2c — Rapprochement**    | `services/rapprochement.py` (exact + alias + trigram) — 3 504 exact + 7 trigram = 3 511 résolues                                | ✅      |
| **Phase 4.2d — Statut qualité**   | `localite_non_resolue` si non résolu                                                                                            | ✅      |
| **Bug carto**                     | `ST_AsGeoJSON` au lieu de `to_shape` (colonne générée non ORM)                                                                  | ✅      |

### ⏳ À faire

| Phase                                 | Contenu                                                                       |
|---------------------------------------|-------------------------------------------------------------------------------|
| **Phase 4.3 — Consolidation**         | `ligne_ingeree` → `ouvrage` (dédoublonnage, création des ouvrages consolidés) |
| **Phase 4.4 — Routers upload + runs** | `POST /fichiers`, `POST /fichiers/{id}/runs`, `GET /runs/{id}`                |
| **Phase 4.5 — Routers lignes**        | `GET /feuilles/{id}/lignes`, `GET /runs/{id}/lignes`, `GET /lignes/{id}`      |
| **Phase 6 — Front**                   | React + Vite + Leaflet + pages Fichiers/Carte/Liste/Qualité + UI de mapping   |
| **Phase 7 — Tests**                   | Tests d'API, d'ingestion, d'export                                            |

---

## 3. Architecture

### 3.1 Stack

| Couche          | Technologie                  | Version      |
|-----------------|------------------------------|--------------|
| Base de données | PostgreSQL + PostGIS         | 16 + 3.4     |
| Back-end        | Python + FastAPI             | 3.12 + 0.115 |
| ORM             | SQLAlchemy + GeoAlchemy2     | 2.0 + 0.16   |
| Validation      | Pydantic                     | 2.9          |
| Migrations      | Alembic                      | 1.13         |
| Parsing Excel   | openpyxl                     | 3.1          |
| Export Excel    | XlsxWriter                   | 3.2          |
| Auth            | python-jose (JWT) + API key  | —            |
| Front-end       | React + Vite + TypeScript    | 18 + 5.4     |
| UI              | Tailwind + shadcn/ui         | 3.4          |
| Carto           | Leaflet + Esri World Imagery | 1.9          |
| Conteneurs      | Docker Compose               | —            |

### 3.2 Arborescence actuelle

```
dhr/
├── docker-compose.yml
├── .env.example / .env
├── .gitignore
├── docs/
│   ├── mcdr.puml, mldr.md (v1.3), mcd.puml
│   ├── openapi.yaml (v1.3, 22 endpoints)
│   ├── metadata_conventions.md (v1.3)
│   ├── HANDOFF.md (ce doc)
│   └── TEST_E2E.md (à créer)
├── sql/schema.sql
├── backend/
│   ├── Dockerfile, entrypoint.sh, pyproject.toml, alembic.ini
│   ├── alembic/
│   │   ├── env.py (filtre NOS_TABLES strict)
│   │   └── versions/
│   │       ├── a3187e43649b_initial_schema.py
│   │       ├── xxxxx_fix_uq_ligne_run_num_add_id_feuille.py
│   │       └── xxxxx_ajout_table_mapping_feuille.py
│   └── app/
│       ├── main.py, config.py, db.py, models.py, auth.py, deps.py
│       ├── schemas/ (common, geo, referentiels, fichiers, ingestion, ouvrages)
│       ├── routers/
│       │   ├── referentiels.py (6 endpoints)
│       │   ├── fichiers.py (3 + 2 mapping)
│       │   ├── ouvrages.py (2 + 2 export)
│       │   ├── carto.py (3 GeoJSON — corrigé ST_AsGeoJSON)
│       │   └── qualite.py (1)
│       └── services/
│           ├── patterns.py             ← NOUVEAU (COLUMN_PATTERNS)
│           ├── coordonnees.py
│           ├── ingestion.py            (importe patterns.py)
│           ├── import_localites.py
│           ├── mapping.py              (importe patterns.py)
│           ├── rapprochement.py
│           └── export.py
├── scripts/
│   ├── inventaire_fichiers.py
│   ├── test_ingestion.py
│   ├── test_ingestion_reelle.py
│   ├── import_localites.py
│   └── test_rapprochement.py
└── tests/
    └── fixtures/
        ├── fichier1.xlsx (1,6 Mo, 5 feuilles, 3511 lignes)
        ├── fichier2.xlsx (272 Ko, 1 feuille, 1307 lignes)
        └── fichier3.xlsx (786 Ko, 1 feuille, 2357 lignes, header_row=7)
```

### 3.3 Modèle de données (14 tables)

**Référentiels** : `source`, `type_ouvrage`, `ref_geo_admin` (hiérarchique), `localite`, `localite_alias`
**Ingestion** : `fichier`, `feuille`, `mapping_feuille`, `ingestion_run`, `ligne_ingeree`
**Métier** : `ouvrage`, `cgpe`, `projet_financement`, `ouvrage_projet`

### 3.4 Décisions de conception figées

| Décision                                                         | Raison                           |
|------------------------------------------------------------------|----------------------------------|
| `hash_sha256` non unique                                         | Réingestion légitime             |
| `code_ouvrage` nullable, non unique                              | Pas d'identifiant métier stable  |
| `UNIQUE (id_feuille, id_run, num_ligne_source)`                  | Plusieurs feuilles + runs        |
| `metadata JSONB` sur `localite`, `ouvrage`, `cgpe`               | Colonnes non mappées             |
| `donnees_brutes JSONB` sur `ligne_ingeree`                       | Source brute immuable            |
| Colonnes générées `geom`                                         | Via `geom_from_latlon` STORED    |
| `geom_from_latlon` STRICT + rejet (0,0)                          | Éviter coordonnées aberrantes    |
| Extensions : `postgis`, `fuzzystrmatch`, `unaccent`, `pg_trgm`   | Pas `postgis_topology`           |
| Auth : API key (lecture) + JWT (écriture)                        | Séparation lecture/écriture      |
| Pagination : offset (petites listes) / cursor (lignes, ouvrages) | Adapter au volume                |
| Export : XlsxWriter + Synthèse KPI + colonne N°                  | Meilleur que openpyxl write_only |
| **Mapping automatique + UI de validation**                       | Fichiers futurs imprévisibles    |
| **Import circulaire corrigé** (`services/patterns.py`)           | Robustesse                       |
| **Carto via `ST_AsGeoJSON`** (pas `to_shape`)                    | Colonne générée non ORM          |

---

## 4. Contrat d'API (22 endpoints)

Base : `http://localhost:8000/v1`

| Méthode | Endpoint                                                                                          | Auth    | Statut |
|---------|---------------------------------------------------------------------------------------------------|---------|--------|
| GET     | `/sources`, `/types-ouvrage`, `/ref-geo`, `/ref-geo/{id}/chemin`, `/localites`, `/localites/{id}` | API key | ✅      |
| GET     | `/fichiers`, `/fichiers/{id}`, `/fichiers/{id}/feuilles`                                          | API key | ✅      |
| GET     | `/fichiers/{id}/mapping-proposal`                                                                 | API key | ✅      |
| PUT     | `/fichiers/{id}/mapping`                                                                          | JWT     | ✅      |
| GET     | `/ouvrages`, `/ouvrages/{id}`, `/cgpe/{id}`                                                       | API key | ✅      |
| GET     | `/ouvrages/export`, `/ouvrages/export.csv`                                                        | API key | ✅      |
| GET     | `/carto/fichiers/{id}/points`, `/carto/tous/points`, `/carto/fichiers/{id}/points.geojson`        | API key | ✅      |
| GET     | `/qualite/fichiers/{id}`                                                                          | API key | ✅      |
| POST    | `/fichiers` (upload)                                                                              | JWT     | ⏳ 4.4  |
| POST    | `/fichiers/{id}/runs`                                                                             | JWT     | ⏳ 4.4  |
| GET     | `/fichiers/{id}/runs`, `/runs/{id}`                                                               | API key | ⏳ 4.4  |
| GET     | `/feuilles/{id}/lignes`, `/runs/{id}/lignes`, `/lignes/{id}`                                      | API key | ⏳ 4.5  |

---

## 5. Démarrage

### 5.1 Première installation

```powershell
git clone <url> dhr
cd dhr
Copy-Item .env.example .env
docker compose up -d --build
docker compose ps   # 3 services healthy
curl.exe http://localhost:8000/health
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
docker compose exec db psql -U dhr -d dhr -c "TRUNCATE ligne_ingeree, ingestion_run, feuille, fichier, mapping_feuille, localite, localite_alias, ref_geo_admin, ouvrage, cgpe, projet_financement, ouvrage_projet RESTART IDENTITY CASCADE;"

# Alembic
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
docker compose exec backend alembic revision -m "description"
```

### 5.3 Tests rapides

```powershell
$apiKey = "dhr_dev_read_key_change_me"

# Référentiels
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/sources
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/types-ouvrage

# Fichiers
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/fichiers

# Mapping proposal
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/fichiers/1/mapping-proposal

# Carto (après correction ST_AsGeoJSON)
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/carto/fichiers/1/points
# Attendu : FeatureCollection avec 3511 features

# Export (vide tant que la consolidation n'est pas faite)
curl.exe -H "X-API-Key: $apiKey" -o export.xlsx http://localhost:8000/v1/ouvrages/export
```

---

## 6. Point de blocage actuel

### 6.1 Symptôme

- `GET /carto/fichiers/1/points` fonctionne (3 511 features, 919 Ko de GeoJSON).
- `GET /carto/tous/points` retourne **0 feature** (table `ouvrage` vide).
- `GET /ouvrages/export` et `/export.csv` sont **vides** (table `ouvrage` vide).

### 6.2 Cause

La table `ouvrage` est **vide**. L'ingestion remplit `ligne_ingeree`, le rapprochement remplit `id_localite`, mais **aucune consolidation** `ligne_ingeree` → `ouvrage` n'a été faite.

### 6.3 Solution : Phase 4.3 — Consolidation

Créer `services/consolidation.py` qui :
1. Pour chaque `ligne_ingeree` avec `statut_qualite = 'ok'` et `id_localite` rempli :
    - Cherche un `ouvrage` existant (via `code_ouvrage` ou `(localite, type, lat/lon)`)
    - Si trouvé : met à jour (dédoublonnage)
    - Sinon : crée un `ouvrage` avec `type_ouvrage`, `etat`, `annee_realisation`, `geom`
2. Marque `ligne_ingeree.id_ouvrage_consolide`

**Script** : `scripts/consolidation.py` pour lancer manuellement.

**Impact** : après consolidation, `/carto/tous/points`, `/ouvrages`, `/ouvrages/export` seront remplis.

---

## 7. TODO détaillé

### Phase 4.3 — Consolidation (**URGENT**)

- [ ] **`services/consolidation.py`** :
    - [ ] `consolider_lignes_run(db, id_run) -> dict` (stats)
    - [ ] Règle de dédoublonnage : `code_ouvrage` si présent, sinon `(id_localite, id_type_ouvrage, annee_realisation)`
    - [ ] Créer/mettre à jour `ouvrage`
    - [ ] Remplir `ligne_ingeree.id_ouvrage_consolide`
- [ ] **`scripts/consolidation.py`** (CLI)
- [ ] **Test** : `SELECT COUNT(*) FROM ouvrage;` → ~3 511 (ou moins si dédoublonnage)
- [ ] **Test** : `GET /carto/tous/points` → FeatureCollection non vide
- [ ] **Test** : `GET /ouvrages/export` → Excel avec données

### Phase 4.4 — Routers upload + runs

- [ ] `POST /v1/fichiers` (upload multipart)
- [ ] `POST /v1/fichiers/{id}/runs` (asynchrone, BackgroundTask)
- [ ] `GET /v1/fichiers/{id}/runs`
- [ ] `GET /v1/runs/{id}` (suivi)
- [ ] Intégration : après upload, appeler `detecter_feuilles` + `importer_localites` (si feuille `Localités`)

### Phase 4.5 — Routers lignes

- [ ] `GET /v1/feuilles/{id}/lignes`
- [ ] `GET /v1/runs/{id}/lignes`
- [ ] `GET /v1/lignes/{id}`
- [ ] `GET /v1/lignes/invalides` (lignes `geom_invalide` pour correction manuelle)

### Phase 6 — Frontend

- [ ] Page **Upload** (multipart + suivi)
- [ ] Page **Mapping** (tableau des colonnes, dropdown champ cible, confiance, valider)
- [ ] Page **Fichiers** (liste, détail, runs)
- [ ] Page **Carte** (Leaflet + Esri + GeoJSON)
- [ ] Page **Liste** (TanStack Table + filtres + export)
- [ ] Page **Qualité** (tableau de bord)

### Phase 7 — Tests

- [ ] Tests d'API (pytest + httpx)
- [ ] Tests d'ingestion (fixtures)
- [ ] Tests d'export (xlsx/csv valides)

---

## 8. Dette technique / points ouverts

| #  | Point                                                 | Impact                                         | À traiter                                   |
|----|-------------------------------------------------------|------------------------------------------------|---------------------------------------------|
| 1  | **Consolidation non faite**                           | `ouvrage` vide, export et carte « Tous » vides | **Phase 4.3**                               |
| 2  | Mapping auto ne reconnaît pas `Localite_ou_Campement` | `type_localite` NULL                           | ✅ Résolu via UI mapping                     |
| 3  | `type_localite` NULL sur 891 localités                | Import                                         | À corriger via `PUT /mapping` + réingestion |
| 4  | UI de mapping                                         | Frontend                                       | **Phase 6**                                 |
| 5  | Déploiement prod                                      | Infra                                          | V2                                          |
| 6  | Nom de domaine réel                                   | Config                                         | Prod                                        |
| 7  | Politique de rétention fichiers                       | Stockage                                       | V2                                          |
| 8  | Gestion utilisateurs                                  | Auth                                           | Config MVP                                  |
| 9  | `Localite.geom_centre` non sérialisé                  | Schémas                                        | V2                                          |
| 10 | DMS corrompu (`7°1'21.29.20"N`)                       | Ingestion                                      | Marqué `geom_invalide` (1 ligne)            |
| 11 | Rapprochement : 7 trigram sur 3 511                   | Rapprochement                                  | OK (99,8 % exact)                           |

---

## 9. Historique des versions

| Version | Date       | Changement                                                                                  |
|---------|------------|---------------------------------------------------------------------------------------------|
| 1.0     | 2026-10-23 | Conception initiale (23 endpoints)                                                          |
| 1.1     | 2026-10-23 | Ajout `metadata` (23 endpoints)                                                             |
| 1.2     | 2026-10-26 | Vue liste + export (25 endpoints)                                                           |
| 2.0     | 2026-10-27 | Phase 1-2 terminées                                                                         |
| 2.1     | 2026-10-27 | Phase 3 terminée (18 endpoints)                                                             |
| 2.2     | 2026-10-28 | Phase 5 terminée (20 endpoints)                                                             |
| 2.3     | 2026-10-29 | Phase 4.1 terminée (ingestion 3 fichiers)                                                   |
| 3.0     | 2026-11-02 | Phase 4.2a terminée (import localités 891)                                                  |
| 3.1     | 2026-11-02 | Phase 4.2b/c/d terminées (mapping UI, rapprochement, statut). Carto corrigé (ST_AsGeoJSON). |

---

## 10. Prochaine action immédiate

**Phase 4.3 — Consolidation** :

1. Créer `services/consolidation.py` (consolider `ligne_ingeree` → `ouvrage`)
2. Créer `scripts/consolidation.py` (CLI)
3. Tester sur fichier1
4. Vérifier `/carto/tous/points` et `/ouvrages/export`

**Critère de validation** : `SELECT COUNT(*) FROM ouvrage;` > 0, et `/carto/tous/points` retourne des features.

---

## 11. Commandes de reprise dans une nouvelle conversation

Pour reprendre, dire :

> « Je reprends le projet DHR. Voici le handoff (coller ce document). Nous en étions à la Phase 4.3 : la consolidation `ligne_ingeree` → `ouvrage` n'est pas faite, donc `/carto/tous/points` et `/ouvrages/export` sont vides. Aide-moi à implémenter `services/consolidation.py` et à tester. »

---

*Handoff rédigé le 2026-11-02. Toute modification du contrat d'API ou du schéma doit être répercutée dans les 5 livrables de conception (`mcdr.puml`, `mldr.md`, `mcd.puml`, `openapi.yaml`, `metadata_conventions.md`) avant implémentation.*