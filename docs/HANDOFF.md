# Handoff — Projet DHR

**Date** : 2026-10-26
**Objet** : Centralisation des ouvrages hydrauliques ruraux pour la Direction de l'Hydraulique Rurale (DHR)
**État** : Conception figée et documentée — prêt pour la production du socle technique
**Version** : 1.2 (ajout vue liste + export Excel/CSV)

---

## 1. Contexte en 3 phrases

La DHR reçoit des fichiers Excel hétérogènes (ONEP, SODECI, UNICEF, BAD, LONACI, État) contenant des données sur les ouvrages hydrauliques ruraux, les CGPE et les financements. Elle veut centraliser ces données dans une base PostgreSQL/PostGIS et disposer d'une UI cartographique (vue satellite) permettant d'afficher les points d'un fichier donné ou tous les points consolidés, **ainsi qu'une vue liste détaillée exportable en Excel/CSV**. Le projet est en phase MVP : lecture + ingestion + carto + export. L'écriture manuelle et l'analytique avancée sont hors scope.

---

## 2. Livrables produits (conception — ✅ terminés)

| Fichier                        | Contenu                                                          | Statut |
|--------------------------------|------------------------------------------------------------------|--------|
| `docs/mcdr.puml`               | MCDR — vue métier (entités, relations, cardinalités)             | ✅      |
| `docs/mldr.md`                 | MLDR — vue technique (tables, colonnes, contraintes, index) v1.2 | ✅      |
| `docs/mcd.puml`                | Diagramme de classes UML complet v1.1                            | ✅      |
| `sql/schema.sql`               | DDL PostgreSQL/PostGIS exécutable, idempotent                    | ✅      |
| `docs/openapi.yaml`            | Contrat d'API OpenAPI 3.1 — **25 endpoints** v1.2                | ✅      |
| `docs/metadata_conventions.md` | Conventions des métadonnées non mappées                          | ✅      |

**Décisions de conception figées** :
- `hash_sha256` non unique (réingestion légitime)
- `code_ouvrage` nullable, non unique (pas d'identifiant métier stable)
- `UNIQUE (id_run, num_ligne_source)` (plusieurs runs par feuille)
- `metadata jsonb` sur `localite`, `ouvrage`, `cgpe`
- `donnees_brutes jsonb` sur `ligne_ingeree` (source brute)
- Colonne `geom` générée via `geom_from_latlon(lat, lon)` (STRICT, rejette bornes et `(0,0)`)
- Extensions : `postgis`, `fuzzystrmatch`, `unaccent`, `pg_trgm` — **pas** `postgis_topology`
- **Export Excel/CSV streamé** (pas de chargement complet en RAM), limite `MAX_EXPORT_ROWS=100000`

---

## 3. Décisions d'architecture figées

### Back-end
- **Python 3.12 + FastAPI** (code-first, OpenAPI auto-générée)
- **SQLAlchemy 2.x + GeoAlchemy2** (ORM)
- **Pydantic v2** (validation, schémas)
- **Alembic** (migrations)
- **openpyxl** (parsing Excel multi-feuilles + export Excel write_only)
- **python-jose + passlib** (JWT HS256)
- **Auth** : API key (`X-API-Key`) pour lecture, JWT Bearer pour écriture

### Front-end
- **React 18 + Vite + TypeScript**
- **shadcn/ui** (Radix + Tailwind)
- **Leaflet 1.9 + Esri World Imagery** (carte satellite)
- **TanStack Query** (appels API) + **TanStack Table** (vue liste)
- **React Router v6**

### Base de données
- **PostgreSQL 16 + PostGIS 3.4**

### Déploiement
- **Docker Compose** (dev)
- Prod : à trancher avec la DHR (hors scope MVP)

### Contrat d'API — décisions
| # | Point          | Décision                                                                                 |
|---|----------------|------------------------------------------------------------------------------------------|
| 1 | Auth           | API key (lecture) + JWT (écriture)                                                       |
| 2 | Filtrage carto | `id_feuille` et `id_run`                                                                 |
| 3 | Vue « Tous »   | Filtre sur `ouvrage` consolidé                                                           |
| 4 | Upload         | Synchrone (201) ; run asynchrone (202)                                                   |
| 5 | Pagination     | Offset (petites listes) / cursor (lignes, ouvrages)                                      |
| 6 | `bbox` GeoJSON | Côté front                                                                               |
| 7 | `poll_url`     | Conservé dans 202                                                                        |
| 8 | Export         | **Excel + CSV**, streamé, filtres identiques à `GET /ouvrages`, limite `MAX_EXPORT_ROWS` |

---

## 4. TODO — Production du socle technique

### 4.1 Infrastructure

- [ ] **`docker-compose.yml`** — Postgres/PostGIS + back + front, healthchecks, volumes persistants
- [ ] **`backend/Dockerfile`** — image Python 3.12 + dépendances
- [ ] **`frontend/Dockerfile`** — image Node 20 + build Vite
- [ ] **`.env.example`** — variables d'environnement (DB, JWT secret, API keys, `MAX_EXPORT_ROWS`)
- [ ] **`.gitignore`** — Python, Node, Docker, IDE

### 4.2 Back-end — squelette

- [ ] **`backend/pyproject.toml`** — dépendances (fastapi, sqlalchemy, geoalchemy2, pydantic, alembic, openpyxl, python-jose, passlib, psycopg2-binary ou asyncpg)
- [ ] **`backend/app/main.py`** — point d'entrée FastAPI, CORS, middlewares, `/health`
- [ ] **`backend/app/config.py`** — Settings Pydantic (DB URL, JWT secret, API keys, MAX_EXPORT_ROWS)
- [ ] **`backend/app/db.py`** — engine SQLAlchemy, session factory, `get_db` dependency

### 4.3 Back-end — modèles & migrations

- [ ] **`backend/app/models.py`** — SQLAlchemy + GeoAlchemy2 (miroir exact de `schema.sql`)
  - `Source`, `TypeOuvrage`, `RefGeoAdmin`, `Localite`, `LocaliteAlias`
  - `Fichier`, `Feuille`, `IngestionRun`, `LigneIngeree`
  - `Ouvrage`, `CGPE`, `ProjetFinancement`, `OuvrageProjet`
- [ ] **`backend/alembic/`** — migration initiale générée depuis les modèles
- [ ] **Vérification** : `alembic upgrade head` produit un schéma identique à `schema.sql`

### 4.4 Back-end — schémas Pydantic

- [ ] **`backend/app/schemas/`** — miroir des schémas OpenAPI
  - `common.py` (Problem, Pagination, GeoJSON)
  - `referentiels.py` (Source, TypeOuvrage, RefGeoAdmin, Localite)
  - `fichiers.py` (Fichier, Feuille)
  - `ingestion.py` (IngestionRun, RunComplet/Echantillon/Plage, LigneIngeree)
  - `ouvrages.py` (Ouvrage, CGPE, QualiteFichier)

### 4.5 Back-end — authentification

- [ ] **`backend/app/auth.py`**
  - Middleware API key (`X-API-Key`) pour lecture
  - Dépendance JWT Bearer pour écriture
  - Gestion des erreurs 401/403 au format RFC 7807

### 4.6 Back-end — routers

- [ ] **`backend/app/routers/referentiels.py`** — sources, types-ouvrage, ref-geo, localites
- [ ] **`backend/app/routers/fichiers.py`** — GET liste, GET détail, POST upload, GET feuilles
- [ ] **`backend/app/routers/ingestion.py`** — GET/POST runs, GET lignes
- [ ] **`backend/app/routers/ouvrages.py`** — GET liste/détail ouvrages, GET CGPE, **GET /ouvrages/export, GET /ouvrages/export.csv**
- [ ] **`backend/app/routers/carto.py`** — endpoints GeoJSON (fichier, tous, téléchargement)
- [ ] **`backend/app/routers/qualite.py`** — tableau de bord qualité
- [ ] **Vérification** : Swagger UI sur `/docs` reflète fidèlement `openapi.yaml`

### 4.7 Back-end — services

- [ ] **`backend/app/services/ingestion.py`**
  - Détection des feuilles (`openpyxl`)
  - Extraction des colonnes mappées → champs normalisés
  - Extraction des colonnes non mappées → `metadata` (via convention)
  - Remplissage `donnees_brutes` (JSONB)
  - Gestion des modes `complet` / `echantillon` / `plage`
  - Mise à jour `statut_qualite` (localité non résolue, géométrie invalide, type inconnu)
- [ ] **`backend/app/services/rapprochement.py`** — rapprochement localité (trigram + unaccent + alias)
- [ ] **`backend/app/services/consolidation.py`** — `ligne_ingeree` → `ouvrage` (V2, mais squelette prêt)
- [ ] **`backend/app/services/export.py`** — export Excel/CSV streamé
  - `export_ouvrages_xlsx(filters, columns, include_metadata) -> StreamingResponse`
  - `export_ouvrages_csv(filters, columns, include_metadata) -> StreamingResponse`
  - `yield_per(5000)` SQLAlchemy + `openpyxl` write_only
  - Vérification de `MAX_EXPORT_ROWS` avant streaming (413 si dépassé)

### 4.8 Back-end — tests

- [ ] **`backend/tests/test_health.py`** — smoke test
- [ ] **`backend/tests/test_auth.py`** — 401/403
- [ ] **`backend/tests/test_carto.py`** — GeoJSON bien formé
- [ ] **`backend/tests/test_ingestion.py`** — fichier Excel de test → lignes ingérées
- [ ] **`backend/tests/test_export.py`** — export xlsx/csv valide, 413 au-delà de la limite

### 4.9 Front-end — squelette

- [ ] **`frontend/package.json`** — React, Vite, TS, Tailwind, shadcn/ui, TanStack Query/Table, Leaflet, React Router
- [ ] **`frontend/vite.config.ts`** — proxy `/api` → back
- [ ] **`frontend/tailwind.config.js`** + **`frontend/src/index.css`**
- [ ] **`frontend/src/main.tsx`** + **`frontend/src/App.tsx`** — routing de base
- [ ] **`frontend/src/lib/api.ts`** — client fetch typé (généré depuis OpenAPI ou manuel)

### 4.10 Front-end — pages

- [ ] **`frontend/src/pages/Fichiers.tsx`** — liste, upload, lancement d'ingestion, suivi de run
- [ ] **`frontend/src/pages/Carte.tsx`** — sélecteur de fichier + option « Tous » + carte satellite Esri
- [ ] **`frontend/src/pages/Liste.tsx`** — **tableau paginé filtrable + boutons d'export Excel/CSV**
- [ ] **`frontend/src/pages/Qualite.tsx`** — tableau de bord par fichier
- [ ] **`frontend/src/components/MapView.tsx`** — Leaflet + Esri + GeoJSON + popups
- [ ] **`frontend/src/components/FileSelector.tsx`** — dropdown fichiers + option « Tous »
- [ ] **`frontend/src/components/FiltersPanel.tsx`** — **composant partagé Carte/Liste** (type, état, district, région, département, sous-préfecture, année min/max, fichier)
- [ ] **`frontend/src/components/ExportButton.tsx`** — **bouton d'export (Excel/CSV) avec indicateur du nombre de lignes filtrées**
- [ ] **`frontend/src/components/UploadDialog.tsx`** — upload + sélection feuilles/plage

### 4.11 Documentation

- [ ] **`README.md`** — installation, lancement, endpoints, variables d'env
- [ ] **`docs/architecture.md`** — vue d'ensemble (DB → back → front)
- [ ] **`docs/ingestion.md`** — flux d'ingestion pas à pas
- [ ] **`docs/export.md`** — format des colonnes exportées, limite, streaming
- [ ] **`docs/deployment.md`** — déploiement Docker Compose

### 4.12 Validation MVP

- [ ] `docker compose up` → les 3 services démarrent
- [ ] `curl http://localhost:8000/health` → `{"status":"ok"}`
- [ ] `curl -H "X-API-Key: ..." http://localhost:8000/v1/sources` → liste seed
- [ ] Upload d'un fichier Excel de test via l'UI → feuilles détectées
- [ ] Lancement d'un run → lignes ingérées en base
- [ ] Carte : sélection d'un fichier → points affichés sur vue satellite
- [ ] Carte : option « Tous » → points consolidés affichés
- [ ] **Liste : filtres appliqués → tableau paginé cohérent**
- [ ] **Liste : bouton « Exporter Excel » → fichier `.xlsx` téléchargé, lignes = filtre courant**
- [ ] **Liste : bouton « Exporter CSV » → fichier `.csv` téléchargé, lignes = filtre courant**
- [ ] **Liste : export au-delà de `MAX_EXPORT_ROWS` → message d'erreur 413 clair**
- [ ] Page Qualité : tableau de bord du fichier de test

---

## 5. TODO — Hors MVP (V2 et au-delà)

### V2 — Fonctionnel
- [ ] Édition manuelle des ouvrages
- [ ] Rapprochement/dédoublonnage automatique (`id_ouvrage_consolide`)
- [ ] Promotion d'un champ `metadata` en attribut de première classe (`attribut_definition` + `ouvrage_attribut`)
- [ ] Traçabilité fine des `metadata` (`metadata_sources` jsonb)
- [ ] Statistiques et tableaux de bord analytiques
- [ ] **Export PDF**
- [ ] **Export multi-feuilles (une feuille par source)**
- [ ] **Choix des colonnes à l'export via l'UI**
- [ ] **Export asynchrone (202 + poll) au-delà de 50k lignes**
- [ ] Gestion des utilisateurs (table `utilisateur`, rôles fins)
- [ ] Versioning/historique des modifications
- [ ] Soft delete
- [ ] WebSocket/SSE pour suivi temps réel

### V2 — Technique
- [ ] Partitionnement de `ligne_ingeree` (si volume > quelques millions)
- [ ] Cache Redis sur les endpoints carto et export
- [ ] Tests de charge (Locust)
- [ ] CI/CD (GitHub Actions ou GitLab CI)
- [ ] Monitoring (Sentry, Prometheus)

### Prod
- [ ] Choix de l'hébergement (VPS interne DHR ou cloud)
- [ ] Nom de domaine réel (remplacer `api.dhr.local`)
- [ ] Certificats TLS
- [ ] Sauvegardes PostgreSQL (pg_dump + rotation)
- [ ] Politique de rétention des fichiers bruts

---

## 6. Points ouverts (à trancher)

| # | Point                                                   | Impact           | Reco                                     |
|---|---------------------------------------------------------|------------------|------------------------------------------|
| 1 | Déploiement prod (VPS interne vs cloud)                 | Infra            | À discuter avec la DHR                   |
| 2 | Nom de domaine réel                                     | API              | À discuter avec la DHR                   |
| 3 | Politique de rétention des fichiers bruts               | Stockage         | À définir (ex. 5 ans)                    |
| 4 | Gestion des utilisateurs au MVP (config vs table)       | Auth             | Config pour le MVP                       |
| 5 | Règle de rapprochement des ouvrages (GPS + nom + année) | Dédoublonnage V2 | À définir en V2                          |
| 6 | Valeur exacte de `MAX_EXPORT_ROWS`                      | Export           | 100 000 par défaut, configurable via env |

---

## 7. Conventions et rappels

### Nommage
- Tables : singulier, `snake_case`
- PK : `id_<table>`
- FK : `<table>_id` ou `id_<table>`
- Timestamps : `created_at`, `updated_at` (timestamptz)
- Métadonnées : `metadata` (jsonb), clés en `snake_case`

### Sécurité
- **Jamais** de secret en clair dans le code
- **Toujours** `.env` pour les secrets (JWT secret, API keys, DB password)
- **Toujours** valider les entrées via Pydantic
- **Toujours** utiliser les requêtes paramétrées (SQLAlchemy)

### Qualité
- **Toujours** documenter une nouvelle clé `metadata` dans `docs/metadata_conventions.md`
- **Toujours** tester un endpoint avant de le merger
- **Toujours** mettre à jour `openapi.yaml` si le contrat change

### Export
- **Toujours** streamer (jamais de `df.to_excel()` en RAM)
- **Toujours** vérifier `MAX_EXPORT_ROWS` avant de commencer le streaming
- **Toujours** réutiliser les filtres de `GET /ouvrages` (pas de divergence vue/export)

### Git
- Branches : `main` (prod), `dev` (intégration), `feat/<nom>`, `fix/<nom>`
- Commits : conventionnels (`feat:`, `fix:`, `docs:`, `chore:`)
- PR : 1 reviewer minimum, tests passants

---

## 8. Ordre de production recommandé
Phase 1 — Socle (1-2 jours)
4.1 Infrastructure + 4.2 Squelette back + 4.3 Modèles + 4.3 Migration
→ Validation : docker compose up + /health + alembic upgrade head

Phase 2 — API lecture (2-3 jours)
4.4 Schémas Pydantic + 4.5 Auth + 4.6 Routers (lecture seule)
→ Validation : Swagger UI + curl sur les 17 endpoints de lecture

Phase 3 — Ingestion (3-5 jours)
4.7 Service d'ingestion + 4.6 Router POST upload + runs
→ Validation : upload d'un fichier Excel de test + run complet

Phase 4 — Export (1-2 jours)
4.7 Service export + 4.6 Router export
→ Validation : curl export xlsx + csv + 413 au-delà de la limite

Phase 5 — Front (4-6 jours)
4.9 Squelette front + 4.10 Pages Fichiers + Carte + Liste + Qualité
→ Validation : parcours utilisateur complet (upload → carte → liste → export)

Phase 6 — Tests & doc (1-2 jours)
4.8 Tests + 4.11 Documentation
→ Validation : MVP prêt
text


**Total estimé** : 12-20 jours ouvrés (1 développeur full-stack).

---

## 9. Ressources

- **Schéma SQL** : `sql/schema.sql`
- **Contrat API** : `docs/openapi.yaml`
- **Diagrammes** : `docs/mcdr.puml`, `docs/mcd.puml`
- **Modèle technique** : `docs/mldr.md`
- **Conventions métadonnées** : `docs/metadata_conventions.md`

---

## 10. Prochaine action immédiate

**Produire le socle Phase 1** :
1. `docker-compose.yml`
2. `backend/Dockerfile`
3. `backend/pyproject.toml`
4. `backend/app/main.py` (avec `/health`)
5. `backend/app/config.py`
6. `backend/app/db.py`

**Critère de validation** : `docker compose up` → `curl http://localhost:8000/health` → `{"status": "ok"}`

---

## 11. Historique des versions

| Version | Date       | Changement                                                        |
|---------|------------|-------------------------------------------------------------------|
| 1.0     | 2026-10-23 | Version initiale du handoff (23 endpoints, sans export)           |
| 1.1     | 2026-10-23 | Ajout `metadata` sur `localite`, `ouvrage`, `cgpe` (23 endpoints) |
| 1.2     | 2026-10-26 | Ajout vue liste + export Excel/CSV (**25 endpoints**)             |


Prochain message : squelettes de code

-- `backend/app/services/export.py` (streaming Excel/CSV)

-- `frontend/src/pages/Liste.tsx` (tableau paginé + filtres + export)

-- `frontend/src/components/FiltersPanel.tsx` (partagé Carte/Liste)