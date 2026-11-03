
---

# Handoff — Projet DHR (v4.0)

**Date** : 2026-11-03
**Version** : 4.0 (Phase 1-5 terminées, Phase 4 terminée)
**Objet** : Centralisation des ouvrages hydrauliques ruraux pour la Direction de l'Hydraulique Rurale (DHR)
**Repo** : `https://github.com/angetraore-dev/dhr`

---

## 1. Contexte métier

La DHR reçoit des fichiers Excel hétérogènes (ONEP, SODECI, UNICEF, BAD, LONACI, État) contenant des données sur les ouvrages hydrauliques ruraux, les CGPE et les financements. Elle veut centraliser ces données dans une base PostgreSQL/PostGIS et disposer d'une UI cartographique (vue satellite) et d'un export Excel/CSV.

**MVP** : lecture + ingestion + carto + export. L'écriture manuelle et l'analytique avancée sont hors scope.

**Décision clé** : un ouvrage **sans coordonnées GPS n'existe pas** pour la DHR. Les lignes sans GPS sont marquées `geom_invalide` et **non consolidées**.

---

## 2. État d'avancement

### ✅ Terminé

| Phase                             | Contenu                                                                             | Statut |
|-----------------------------------|-------------------------------------------------------------------------------------|--------|
| **Conception**                    | MCDR, MLDR, UML, `schema.sql`, `openapi.yaml`, conventions metadata                 | ✅      |
| **Phase 1 — Infrastructure**      | Docker Compose, config, db, entrypoint                                              | ✅      |
| **Phase 2 — Modèles + migration** | 14 tables SQLAlchemy (dont `mapping_feuille`), migrations Alembic                   | ✅      |
| **Phase 3 — API lecture**         | 18 endpoints (référentiels, fichiers, ouvrages, CGPE, carto, qualité)               | ✅      |
| **Phase 4 — Ingestion**           | Pipeline complet : upload → ingestion → rapprochement → consolidation               | ✅      |
| **Phase 4.1 — Ingestion**         | `coordonnees.py`, `ingestion.py`, 3 fichiers testés (7 175 lignes)                  | ✅      |
| **Phase 4.2 — Mapping UI**        | `patterns.py`, `mapping.py`, table `mapping_feuille`, endpoints proposal/validation | ✅      |
| **Phase 4.3 — Rapprochement**     | `rapprochement.py` (exact + alias + trigram) — 3 504 exact + 7 trigram              | ✅      |
| **Phase 4.4 — Consolidation**     | `consolidation.py` (filtre localités, mapping type/état, dédoublonnage)             | ✅      |
| **Phase 4.5 — Upload + Run**      | `upload.py`, `run.py`, `POST /fichiers`, `POST /fichiers/{id}/runs`                 | ✅      |
| **Phase 5 — Export**              | Excel XlsxWriter + Synthèse KPI + CSV, colonne N°, limite 413                       | ✅      |

### ⏳ À faire

| Phase                  | Contenu                                                                     |
|------------------------|-----------------------------------------------------------------------------|
| **Phase 6 — Frontend** | React + Vite + Leaflet + pages Fichiers/Carte/Liste/Qualité + UI de mapping |
| **Phase 7 — Tests**    | Tests d'API (pytest), tests d'ingestion, tests d'export                     |

---

## 3. Diagramme du pipeline complet

```text
┌─────────────────────────────────────────────────────────────────────┐
│  ÉTAPE 1 — IMPORT DES LOCALITÉS (manuel, une ou plusieurs fois)     │
│                                                                     │
│  Script : scripts/import_localites.py <fichier.xlsx>                │
│  Service : services/import_localites.py                             │
│                                                                     │
│  Entrée : fichier Excel (feuille "Localités")                       │
│  Sortie : ref_geo_admin (district → région → département →          │
│           sous-préfecture → localité) + localite (nom + GPS)        │
│                                                                     │
│  Quand : au premier démarrage, ou quand un nouveau fichier          │
│          contient de nouvelles localités.                           │
│  Ne duplique pas les localités existantes (check nom_usage+id_geo). │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ÉTAPE 2 — UPLOAD                                                   │
│                                                                     │
│  Endpoint : POST /v1/fichiers (multipart, JWT)                      │
│  Service : services/upload.py                                       │
│                                                                     │
│  Entrée : fichier Excel + id_source                                 │
│  Sortie : fichier (statut='en_attente') + feuille (N feuilles)      │
│           + détection des feuilles (nom, index, nb_lignes_estime)   │
│                                                                     │
│  Détection réingestion : si hash_sha256 existe déjà → 409           │
│  (sauf ?force=true).                                                │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ÉTAPE 3 — RUN (pipeline asynchrone)                                │
│                                                                     │
│  Endpoint : POST /v1/fichiers/{id}/runs (JWT)                       │
│  Service : services/run.py                                          │
│                                                                     │
│  3.1 INGESTION (services/ingestion.py)                              │
│      → ligne_ingeree (donnees_brutes JSONB + coordonnées décimales) │
│      → statut_qualite = 'ok' ou 'geom_invalide'                     │
│                                                                     │
│  3.2 RAPPROCHEMENT (services/rapprochement.py)                      │
│      → ligne_ingeree.id_localite (exact + alias + trigram)          │
│      → statut_qualite = 'ok' ou 'localite_non_resolue'              │
│                                                                     │
│  3.3 CONSOLIDATION (services/consolidation.py)                      │
│      → ouvrage (dédoublonné, type/état/GPS)                         │
│      → ligne_ingeree.id_ouvrage_consolide                           │
│      → ignore les feuilles "Localités" (pas des ouvrages)           │
│                                                                     │
│  Le client poll GET /v1/runs/{id} pour suivre l'avancement.         │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ÉTAPE 4 — LECTURE / EXPORT / CARTO                                 │
│                                                                     │
│  GET /v1/ouvrages            → liste paginée cursor                 │
│  GET /v1/ouvrages/{id}       → détail avec geom                     │
│  GET /v1/ouvrages/export     → Excel (Synthèse KPI + Ouvrages)      │
│  GET /v1/ouvrages/export.csv → CSV (UTF-8, séparateur ;)            │
│  GET /v1/carto/tous/points   → GeoJSON FeatureCollection            │
│  GET /v1/carto/fichiers/{id}/points → GeoJSON par fichier           │
│  GET /v1/qualite/fichiers/{id} → tableau de bord qualité            │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.1 Flux de données (tables)

```text
    ref_geo_admin ◄──── localite ◄──── ligne_ingeree.id_localite
                            ▲                    │
                            │                    │ (consolidation)
                            │                    ▼
                            │                ouvrage
                            │                    │
                            │                    │ (N..N)
                            │                    ▼
                            │              ouvrage_projet ◄──── projet_financement
                            │
                            │ (CGPE)
                            ▼
    cgpe
```

### 3.2 Flux d'ingestion (par run)

```text
fichier (1) ──< feuille (N) ──< ligne_ingeree (N)
│
├─► id_localite (rapprochement)
└─► id_ouvrage_consolide (consolidation)
```

---

## 4. Tests et validations

### 4.1 Tests manuels (scripts CLI)

| Script                     | Rôle                           | Commande                                                 | Résultat attendu                          |
|----------------------------|--------------------------------|----------------------------------------------------------|-------------------------------------------|
| `inventaire_fichiers.py`   | Diagnostic (feuilles, entêtes) | `python /app/scripts/inventaire_fichiers.py <fichier>`   | Liste des feuilles + entêtes              |
| `test_ingestion.py`        | Diagnostic (mapping auto)      | `python /app/scripts/test_ingestion.py <fichier>`        | Colonnes mappées + non mappées            |
| `import_localites.py`      | Import référentiel             | `python /app/scripts/import_localites.py <fichier>`      | 891 localités, 0 erreur                   |
| `test_ingestion_reelle.py` | Ingestion en base              | `python /app/scripts/test_ingestion_reelle.py <fichier>` | 3 511 lignes ingérées                     |
| `test_rapprochement.py`    | Rapprochement                  | `python /app/scripts/test_rapprochement.py <id_run>`     | 3 504 exact + 7 trigram = 3 511 résolues  |
| `consolidation.py`         | Consolidation                  | `python /app/scripts/consolidation.py <id_run>`          | 2 379 ouvrages (1 132 localités ignorées) |

### 4.2 Tests via API

| Endpoint                     | Commande                                                                          | Résultat attendu                          |
|------------------------------|-----------------------------------------------------------------------------------|-------------------------------------------|
| `POST /fichiers`             | `curl -X POST -H "Authorization: Bearer $jwt" -F "file=@..." -F "id_source=1"`    | 201 + id_fichier + feuilles_detectees     |
| `POST /fichiers/{id}/runs`   | `curl -X POST -H "Authorization: Bearer $jwt" ".../fichiers/1/runs?mode=complet"` | 202 + id_run + poll_url                   |
| `GET /runs/{id}`             | `curl -H "X-API-Key: $apiKey" .../runs/1`                                         | statut='termine', nb_lignes_ingerees=3511 |
| `GET /ouvrages`              | `curl -H "X-API-Key: $apiKey" .../ouvrages`                                       | Liste paginée avec geom                   |
| `GET /ouvrages/export`       | `curl -H "X-API-Key: $apiKey" -o export.xlsx .../ouvrages/export`                 | ~187 Ko                                   |
| `GET /ouvrages/export.csv`   | `curl -H "X-API-Key: $apiKey" -o export.csv .../ouvrages/export.csv`              | ~411 Ko                                   |
| `GET /carto/tous/points`     | `curl -H "X-API-Key: $apiKey" .../carto/tous/points`                              | FeatureCollection                         |
| `GET /qualite/fichiers/{id}` | `curl -H "X-API-Key: $apiKey" .../qualite/fichiers/1`                             | 100% réussite                             |

### 4.3 Résultats du dernier test E2E (2026-11-03)

| Étape            | Résultat                                    |
|------------------|---------------------------------------------|
| Import localités | ✅ 891 localités                             |
| Upload fichier1  | ✅ 5 feuilles détectées                      |
| Run complet      | ✅ 3 511 lignes en 13s                       |
| Rapprochement    | ✅ 3 504 exact + 7 trigram                   |
| Consolidation    | ✅ 2 379 ouvrages (1 132 localités ignorées) |
| Répartition      | ✅ PMH 2 117, PEA 172, HVA 86, AUTRE 4       |
| Export Excel     | ✅ 187 Ko                                    |
| Export CSV       | ✅ 411 Ko                                    |
| Carto            | ✅ FeatureCollection                         |
| Qualité          | ✅ 100%                                      |

---

## 5. Architecture

### 5.1 Stack

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

### 5.2 Arborescence

```
dhr/
├── docker-compose.yml
├── .env.example / .env
├── .gitignore
├── docs/
│   ├── mcdr.puml, mldr.md (v1.3), mcd.puml
│   ├── openapi.yaml (v1.3, 27 endpoints)
│   ├── metadata_conventions.md (v1.3)
│   ├── SCRIPTS.md (documentation des scripts)
│   └── HANDOFF.md (ce doc)
├── sql/schema.sql
├── backend/
│   ├── Dockerfile, entrypoint.sh, pyproject.toml, alembic.ini
│   ├── alembic/
│   │   ├── env.py (filtre NOS_TABLES strict)
│   │   └── versions/ (migrations)
│   └── app/
│       ├── main.py, config.py, db.py, models.py, auth.py, deps.py
│       ├── schemas/ (common, geo, referentiels, fichiers, ingestion, ouvrages)
│       ├── routers/
│       │   ├── referentiels.py (6 endpoints)
│       │   ├── fichiers.py (3 + 2 mapping + 2 runs)
│       │   ├── ouvrages.py (2 + 2 export)
│       │   ├── carto.py (3 GeoJSON)
│       │   ├── ingestion.py (4 : runs/lignes)
│       │   └── qualite.py (1)
│       └── services/
│           ├── patterns.py (COLUMN_PATTERNS)
│           ├── coordonnees.py (parser lat/lon)
│           ├── ingestion.py (parsing Excel)
│           ├── import_localites.py (import référentiel)
│           ├── mapping.py (proposal + validation)
│           ├── rapprochement.py (exact + alias + trigram)
│           ├── consolidation.py (ligne → ouvrage)
│           ├── upload.py (upload fichier)
│           ├── run.py (pipeline complet)
│           └── export.py (XlsxWriter + CSV)
├── scripts/
│   ├── inventaire_fichiers.py, test_ingestion.py
│   ├── test_ingestion_reelle.py, import_localites.py
│   ├── test_rapprochement.py, consolidation.py
└── tests/
└── fixtures/
├── fichier1.xlsx (1,6 Mo, 5 feuilles, 3511 lignes)
├── fichier2.xlsx (272 Ko, 1 feuille, 1307 lignes)
└── fichier3.xlsx (786 Ko, 1 feuille, 2357 lignes, header_row=7)
```

### 5.3 Modèle de données (14 tables)

**Référentiels** : `source`, `type_ouvrage`, `ref_geo_admin` (hiérarchique), `localite`, `localite_alias`
**Ingestion** : `fichier`, `feuille`, `mapping_feuille`, `ingestion_run`, `ligne_ingeree`
**Métier** : `ouvrage`, `cgpe`, `projet_financement`, `ouvrage_projet`

---

## 6. Contrat d'API (27 endpoints)

Base : `http://localhost:8000/v1`

| Méthode | Endpoint                                                                                          | Auth    | Statut |
|---------|---------------------------------------------------------------------------------------------------|---------|--------|
| GET     | `/sources`, `/types-ouvrage`, `/ref-geo`, `/ref-geo/{id}/chemin`, `/localites`, `/localites/{id}` | API key | ✅      |
| GET     | `/fichiers`, `/fichiers/{id}`, `/fichiers/{id}/feuilles`                                          | API key | ✅      |
| POST    | `/fichiers` (upload)                                                                              | JWT     | ✅      |
| GET     | `/fichiers/{id}/mapping-proposal`                                                                 | API key | ✅      |
| PUT     | `/fichiers/{id}/mapping`                                                                          | JWT     | ✅      |
| POST    | `/fichiers/{id}/runs`                                                                             | JWT     | ✅      |
| GET     | `/fichiers/{id}/runs`, `/runs/{id}`                                                               | API key | ✅      |
| GET     | `/runs/{id}/lignes`, `/feuilles/{id}/lignes`, `/lignes/{id}`                                      | API key | ✅      |
| GET     | `/ouvrages`, `/ouvrages/{id}`, `/cgpe/{id}`                                                       | API key | ✅      |
| GET     | `/ouvrages/export`, `/ouvrages/export.csv`                                                        | API key | ✅      |
| GET     | `/carto/fichiers/{id}/points`, `/carto/tous/points`, `/carto/fichiers/{id}/points.geojson`        | API key | ✅      |
| GET     | `/qualite/fichiers/{id}`                                                                          | API key | ✅      |

---

## 7. Décisions de conception figées

| Décision                                                         | Raison                                  |
|------------------------------------------------------------------|-----------------------------------------|
| `hash_sha256` non unique                                         | Réingestion légitime                    |
| `code_ouvrage` nullable, non unique                              | Pas d'identifiant métier stable         |
| `UNIQUE (id_feuille, id_run, num_ligne_source)`                  | Plusieurs feuilles + runs               |
| `metadata JSONB` sur `localite`, `ouvrage`, `cgpe`               | Colonnes non mappées                    |
| `donnees_brutes JSONB` sur `ligne_ingeree`                       | Source brute immuable                   |
| Colonnes générées `geom`                                         | Via `geom_from_latlon` STORED           |
| `geom_from_latlon` STRICT + rejet (0,0)                          | Éviter coordonnées aberrantes           |
| Extensions : `postgis`, `fuzzystrmatch`, `unaccent`, `pg_trgm`   | Pas `postgis_topology`                  |
| Auth : API key (lecture) + JWT (écriture)                        | Séparation lecture/écriture             |
| Pagination : offset (petites listes) / cursor (lignes, ouvrages) | Adapter au volume                       |
| Export : XlsxWriter + Synthèse KPI + colonne N°                  | Meilleur que openpyxl write_only        |
| Mapping automatique + UI de validation                           | Fichiers futurs imprévisibles           |
| **Ouvrage sans GPS = inexistant**                                | Décision métier DHR                     |
| **Import localités manuel**                                      | Référentiel stable, pas d'auto-création |
| **Consolidation filtre localités**                               | Les localités ne sont pas des ouvrages  |
| **Carto via `ST_AsGeoJSON`**                                     | Colonne générée non ORM                 |

---

## 8. Commandes utiles

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

# Tests
docker compose exec backend python -c "from app.main import app; import json; print(len(app.openapi()['paths']))"
# Attendu : 27
```

---

## 9. Dette technique / points ouverts

| #  | Point                                                | Impact    | À traiter               |
|----|------------------------------------------------------|-----------|-------------------------|
| 1  | **UI de mapping**                                    | Frontend  | Phase 6                 |
| 2  | **Page Upload**                                      | Frontend  | Phase 6                 |
| 3  | **Page Carte**                                       | Frontend  | Phase 6                 |
| 4  | **Page Liste**                                       | Frontend  | Phase 6                 |
| 5  | **Page Qualité**                                     | Frontend  | Phase 6                 |
| 6  | Tests d'API (pytest)                                 | Qualité   | Phase 7                 |
| 7  | Déploiement prod                                     | Infra     | V2                      |
| 8  | Nom de domaine réel                                  | Config    | Prod                    |
| 9  | Politique de rétention fichiers                      | Stockage  | V2                      |
| 10 | Gestion utilisateurs                                 | Auth      | Config MVP              |
| 11 | `Localite.geom_centre` non sérialisé                 | Schémas   | V2                      |
| 12 | DMS corrompu (`7°1'21.29.20"N`)                      | Ingestion | 1 ligne `geom_invalide` |
| 13 | **Création manuelle de localités** (si non résolues) | Frontend  | V2                      |

---

## 10. Historique des versions

| Version | Date           | Changement                                                                                         |
|---------|----------------|----------------------------------------------------------------------------------------------------|
| 1.0     | 2026-10-23     | Conception initiale (23 endpoints)                                                                 |
| 1.1     | 2026-10-23     | Ajout `metadata`                                                                                   |
| 1.2     | 2026-10-26     | Vue liste + export (25 endpoints)                                                                  |
| 2.0     | 2026-10-27     | Phase 1-2 terminées                                                                                |
| 2.1     | 2026-10-27     | Phase 3 terminée (18 endpoints)                                                                    |
| 2.2     | 2026-10-28     | Phase 5 terminée (20 endpoints)                                                                    |
| 2.3     | 2026-10-29     | Phase 4.1 terminée (ingestion 3 fichiers)                                                          |
| 3.0     | 2026-11-02     | Phase 4.2a terminée (import localités 891)                                                         |
| 3.1     | 2026-11-02     | Phase 4.2b/c/d terminées (mapping UI, rapprochement, statut). Carto corrigé.                       |
| **4.0** | **2026-11-03** | **Phase 4 terminée (upload + run pipeline). Phase 5 export OK. 27 endpoints. Pipeline E2E testé.** |

---

## 11. Prochaine action immédiate

**Phase 6 — Frontend** :

1. **Squelette React + Vite + TS + Tailwind** (déjà en place, à compléter)
2. **Pages** :
    - `Fichiers.tsx` : liste, upload, lancement run, suivi
    - `Mapping.tsx` : UI de mapping (proposal + validation)
    - `Carte.tsx` : sélecteur fichier + option « Tous » + Leaflet + Esri
    - `Liste.tsx` : tableau paginé + filtres + export
    - `Qualite.tsx` : tableau de bord par fichier
3. **Composants** :
    - `MapView.tsx` : Leaflet + Esri + GeoJSON
    - `FileSelector.tsx` : dropdown fichiers
    - `FiltersPanel.tsx` : filtres partagés Carte/Liste
    - `ExportButton.tsx` : export Excel/CSV

---

## 12. Commandes de reprise

Pour reprendre, dire :

> « Je reprends le projet DHR. Voici le handoff (coller ce document). Nous en étions à la Phase 6 : le backend est terminé (27 endpoints, pipeline E2E testé). Aide-moi à implémenter le frontend React/Vite/Leaflet. »

---

*Handoff rédigé le 2026-11-03. Toute modification du contrat d'API ou du schéma doit être répercutée dans les 5 livrables de conception (`mcdr.puml`, `mldr.md`, `mcd.puml`, `openapi.yaml`, `metadata_conventions.md`) avant implémentation.*
