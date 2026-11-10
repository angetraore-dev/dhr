# Handoff complet — Projet DHR (v1.0, 2026-11-10)

Document de reprise pour le projet DHR. Il capture l'état actuel, ce qui a été fait, ce qui reste à faire, et les décisions actées. Il **complète** la Bible (`DHR.md`) et la Constitution (`CONSTITUTION.md`), qui font autorité.

---

## Table des matières

1. [Contexte métier](#1-contexte-métier)
2. [État d'avancement](#2-état-davancement)
3. [Architecture](#3-architecture)
4. [Contrat d'API (résumé)](#4-contrat-dapi-résumé)
5. [Frontend (résumé)](#5-frontend-résumé)
6. [Modèle de données (résumé)](#6-modèle-de-données-résumé)
7. [Pipeline d'ingestion (résumé)](#7-pipeline-dingestion-résumé)
8. [Démarrage & commandes utiles](#8-démarrage--commandes-utiles)
9. [TODO détaillé](#9-todo-détaillé)
10. [Dette technique / points ouverts](#10-dette-technique--points-ouverts)
11. [Décisions structurantes](#11-décisions-structurantes)
12. [Documents de référence](#12-documents-de-référence)
13. [Commandes de reprise](#13-commandes-de-reprise)

---

## 1. Contexte métier

La **Direction de l'Hydraulique Rurale (DHR)** est l'entité publique ivoirienne chargée du suivi des ouvrages hydrauliques en zone rurale. Elle reçoit des fichiers Excel de **sources hétérogènes** (ONEP, SODECI, UNICEF, BAD, LONACI, État de CI, etc.), avec des structures, des entêtes et des qualités variables.

**Objectif du projet** : centraliser ces données dans une base PostgreSQL/PostGIS, avec une UI cartographique (vue satellite), un export Excel/CSV, et un suivi de la qualité.

**MVP** : lecture + ingestion + rapprochement + consolidation + carto + export + qualité.
**Hors scope MVP** : création manuelle, analytique avancée, import auto localités, gestion utilisateurs, déploiement prod, mobile, filtre district.

---

## 2. État d'avancement

### 2.1 Ce qui est terminé

| Élément | Statut | Détail |
|---------|--------|--------|
| **Bible v1.0** (`DHR.md`) | ✅ Terminée | 8 sections, cohérente, fait autorité |
| **Constitution v1.0** (`CONSTITUTION.md`) | ✅ Terminée | 8 sections, contrat opérationnel |
| **Phase A — Bible** | ✅ Terminée | Sections 1 → 8, ToC, cohérence |
| **Phase B — Constitution** | ✅ Terminée | Document 2–3 pages, renvois à la Bible |
| **Phase C — Socle DB** | ✅ Terminée | `schema.sql` + `0001_initial.py` + `models.py` alignés |
| **`schema.sql`** | ✅ Généré | 13 tables + 3 vues + 3 fonctions + 8 triggers + seed |
| **`0001_initial.py`** | ✅ Appliqué | Migration unique, idempotente (upgrade/downgrade/upgrade) |
| **`models.py`** | ✅ Aligné | 13 modèles SQLAlchemy 2.0, alignés sur `schema.sql` |
| **`env.py`** | ✅ Corrigé | Garde-fou `NOS_TABLES` non vide, exclusion `alembic_version` |
| **Tests DB** (`tests-db.md`) | ✅ Documentés | Checklist complète (tables, vues, fonctions, triggers, PostGIS) |
| **Backend démarre** | ✅ Vérifié | `/health` répond, migrations passent, `orjson` installé |
| **`patterns.py`** | ✅ Aligné | `type_ouvrage_brut`, `usage_ouvrage_brut`, `INDICATEURS_SANITAIRES` |
| **`ingestion.py`** | ✅ Corrigé (B5, I1, I2) | Rejets détectés, `nb_lignes_total = stockées + rejetées`, `fichier.statut` non touché |
| **`rapprochement.py`** | ✅ Corrigé (I3) | `message_qualite` format strict |
| **`consolidation.py`** | ✅ Corrigé (B6) | `doublon_suspect`, `type_ouvrage_inconnu`, `qualite_eau` |
| **`run.py`** | ✅ Corrigé (I2) | `fichier.statut` mis à jour en fin de pipeline |
| **`export.py`** | ✅ Corrigé (B1) | `TypeOuvrage` retiré, 3 KPI distincts, testé avec 1 ouvrage |
| **`coordonnees.py`** | ✅ Conforme | DMS, virgule, inversion, bornes |
| **`mapping.py`** | ✅ Conforme | Lit `COLUMN_PATTERNS` |

### 2.2 Ce qui est en cours

| Élément | Statut | Détail |
|---------|--------|--------|
| **Tests backend** | 📦 Fichiers livrés, pas appliqués | `conftest.py`, `test_*.py`, `fixtures/__init__.py` |
| **Tests README** | 📦 Livré | `tests/README.md` (commandes, prérequis, dépannage) |
| **CI GitHub Actions** | 📦 Fichier livré, pas appliqué | `.github/workflows/ci.yml` |
| **Audit `schemas/*` + `routers/*`** | ⏳ À faire | Vérifier alignement sur la Bible (3 champs sémantiques, pas de `type_ouvrage`, pas de `district`) |

### 2.3 Ce qui reste à faire

| Élément | Statut | Détail |
|---------|--------|--------|
| **Audit schémas** | ⏳ À faire | `schemas/ouvrages.py`, `schemas/fichiers.py`, `schemas/referentiels.py`, `schemas/common.py`, `schemas/qualite.py` |
| **Audit routers** | ⏳ À faire | `routers/ouvrages.py`, `routers/carto.py`, `routers/referentiels.py`, `routers/fichiers.py`, `routers/ingestion.py`, `routers/qualite.py` |
| **Audit `deps.py`** | ⏳ À faire | `OuvrageFilters` (3 champs, pas de `district`) |
| **Tests backend** | ⏳ À appliquer | Lancer `pytest`, corriger les échecs |
| **CI GitHub Actions** | ⏳ À appliquer | Vérifier la CI sur GitHub |
| **Frontend F1–F9** | ⏳ À faire | `Mapping.tsx`, `MapView.tsx`, `Liste.tsx`, `Qualite.tsx`, `Parametres.tsx`, `api.ts`, `OLD_Carte.tsx` |
| **`openapi.yaml`** | ⏳ À aligner | O1–O5, OI1–OI2 (section 7.2) |
| **`metadata_conventions.md`** | ⏳ À réécrire | M1–M6 (section 7.3) |

---

## 3. Architecture

### 3.1 Stack technique

| Couche | Technologie | Version |
|--------|-------------|---------|
| Base de données | PostgreSQL + PostGIS | 16 + 3.4 |
| Backend | Python + FastAPI | 3.12 + 0.115 |
| ORM | SQLAlchemy + GeoAlchemy2 | 2.0 + 0.16 |
| Validation | Pydantic | 2.9 |
| Migrations | Alembic | 1.13 |
| Parsing Excel | openpyxl | 3.1 |
| Export Excel | XlsxWriter | 3.2 |
| Auth | python-jose (JWT) + API key | — |
| Frontend | React + Vite + TypeScript | 18 + 5.4 |
| UI | Tailwind + shadcn/ui | 3.4 |
| Carto | Leaflet + Esri World Imagery | 1.9 |
| État API | TanStack Query | 5.59 |
| Conteneurs | Docker Compose | — |

### 3.2 Structure backend

```text
backend/
├── app/
│   ├── main.py              # Point d'entrée FastAPI
│   ├── config.py            # Settings (Pydantic)
│   ├── db.py                # Engine, Session, Base, get_db
│   ├── auth.py              # API key + JWT
│   ├── deps.py              # Dépendances FastAPI (pagination, filtres)
│   ├── models.py            # 13 modèles SQLAlchemy (miroir de la Bible)
│   ├── schemas/             # Schémas Pydantic (request/response)
│   │   ├── common.py
│   │   ├── ouvrages.py
│   │   ├── fichiers.py
│   │   ├── referentiels.py
│   │   └── qualite.py
│   ├── routers/             # Endpoints HTTP (fins, délèguent aux services)
│   │   ├── referentiels.py
│   │   ├── fichiers.py
│   │   ├── ingestion.py
│   │   ├── ouvrages.py
│   │   ├── carto.py
│   │   └── qualite.py
│   └── services/            # Logique métier (indépendante de FastAPI)
│       ├── coordonnees.py   # parser_coordonnees
│       ├── patterns.py      # COLUMN_PATTERNS, INDICATEURS_SANITAIRES
│       ├── upload.py        # Sauvegarde + détection feuilles
│       ├── mapping.py       # Proposition + sauvegarde + chargement
│       ├── ingestion.py     # ingerer_fichier, ingerer_feuille
│       ├── rapprochement.py # rapprocher_lignes_run
│       ├── consolidation.py # consolider_lignes_run
│       ├── export.py        # export_ouvrages_xlsx, export_ouvrages_csv
│       └── run.py           # Orchestrateur (pipeline complet)
├── alembic/
│   ├── versions/
│   │   └── 0001_initial.py  # Migration unique
│   └── env.py
├── scripts/                 # Scripts CLI
│   ├── import_localites.py
│   ├── test_ingestion_reelle.py
│   ├── test_rapprochement.py
│   └── consolidation.py
├── tests/                   # Tests pytest
│   ├── conftest.py
│   ├── fixtures/
│   ├── test_coordonnees.py
│   ├── test_ingestion.py
│   ├── test_rapprochement.py
│   ├── test_consolidation.py
│   ├── test_integration_pipeline.py
│   └── README.md
├── sql/
│   └── schema.sql           # Régénéré depuis la Bible
├── pyproject.toml
└── Dockerfile
```

### 3.3 Structure frontend

```text
frontend/
├── src/
│   ├── pages/               # 1 fichier par page
│   │   ├── Fichiers.tsx     # ✅ existante
│   │   ├── Mapping.tsx      # ✅ existante
│   │   ├── Carte.tsx        # ✅ existante
│   │   ├── Liste.tsx        # ⏳ stub
│   │   ├── Qualite.tsx      # ⏳ stub
│   │   └── Parametres.tsx   # ✅ existante
│   ├── components/
│   │   ├── FiltersPanel.tsx # ✅ existant
│   │   ├── MapView.tsx      # ✅ existant
│   │   ├── RunStatus.tsx    # ✅ existant
│   │   ├── UploadDialog.tsx # ✅ existant
│   │   └── ui/              # shadcn/ui
│   ├── lib/
│   │   └── api.ts           # Client HTTP + types + setJwt/getJwt
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── package.json
├── tsconfig.json
├── vite.config.ts
└── Dockerfile
```

---

## 4. Contrat d'API (résumé)

**Base** : `/v1`. **Auth** : `X-API-Key` (lecture), `Authorization: Bearer` (écriture).

### 4.1 Endpoints (27)

| Tag | Endpoints |
|-----|-----------|
| **Référentiels** | `GET /sources`, `/ref-geo`, `/ref-geo/{id}/chemin`, `/localites`, `/localites/{id}` |
| **Fichiers** | `GET /fichiers`, `POST /fichiers`, `GET /fichiers/{id}`, `/fichiers/{id}/feuilles`, `/fichiers/{id}/mapping-proposal`, `PUT /fichiers/{id}/mapping` |
| **Ingestion** | `POST /fichiers/{id}/runs`, `GET /fichiers/{id}/runs`, `/runs/{id}`, `/runs/{id}/lignes`, `/feuilles/{id}/lignes`, `/lignes/{id}` |
| **Ouvrages** | `GET /ouvrages`, `/ouvrages/{id}`, `/ouvrages/export`, `/ouvrages/export.csv`, `/cgpe/{id}` |
| **Carto** | `GET /carto/fichiers/{id}/points`, `/carto/fichiers/{id}/points.geojson`, `/carto/tous/points` |
| **Qualité** | `GET /qualite/fichiers/{id}` |

**Note** : `/types-ouvrage` **supprimé** (table supprimée).

### 4.2 Filtres (Bible § 4.3.4)

- `nature_ouvrage` : `puits` \| `forage` \| `inconnu`
- `type_alimentation` : `PMH` \| `HVA` \| `PEA` \| `HV` \| `AUTRE`
- `realisation_par` : `public` \| `prive` \| `inconnu`
- `etat` : `fonctionnel` \| `en_panne` \| `abandonne` \| `inconnu`
- `region`, `departement`, `sous_prefecture`, `annee_min`, `annee_max`
- **Pas de `district`** (réforme territoriale)

### 4.3 Pagination

- **Offset** : `sources`, `ref-geo`, `localites`, `fichiers`, `feuilles`, `runs`
- **Cursor** : `ouvrages`, `lignes`

### 4.4 Format d'erreur

**RFC 7807** (Problem Details) : `{type, title, status, detail, instance, errors?}`.

---

## 5. Frontend (résumé)

### 5.1 Pages

| Page | Statut | Détail |
|------|--------|--------|
| **Fichiers** | ✅ | Liste, upload, run, statut (polling 2s), lien Mapping |
| **Mapping** | ✅ | Onglets feuilles, destinations (Standard / Ouvrage / Localité / CGPE / Ignorer), sauvegarde |
| **Carte** | ✅ | Mode Tous / Par fichier, filtres, `MapView` Leaflet + Esri |
| **Liste** | ⏳ | Stub, à implémenter (F7) |
| **Qualité** | ⏳ | Stub, à implémenter (F7) |
| **Paramètres** | ✅ | JWT (localStorage), bouton sauvegarder |

### 5.2 Composants

| Composant | Statut | Détail |
|-----------|--------|--------|
| **FiltersPanel** | ✅ | 3 filtres métier + cascade géo + année |
| **MapView** | ✅ | Leaflet + Esri, `circleMarker` coloré par `type_alimentation` |
| **RunStatus** | ✅ | Polling 2s, badge statut |
| **UploadDialog** | ✅ | Fichier, source, commentaire |

### 5.3 Écarts frontend à corriger (F1–F9)

| # | Écart | Correction |
|---|-------|-----------|
| F1 | `CHAMPS_STANDARDS` sans `usage_ouvrage_brut` | Ajouter |
| F2 | `MapView` : forme = nature approximée par `dashArray` | Remplacer par vraies formes (cercle/carré/losange) |
| F3 | `window.open` pour l'export | Remplacer par `fetch` + `blob` |
| F4 | `OLD_Carte.tsx` traîne dans `pages/` | Supprimer |
| F5 | Pas de redirection 401 | Ajouter |
| F6 | Textes « Chargement... » | Remplacer par `Skeleton` |
| F7 | `Liste.tsx`, `Qualite.tsx` stubs | Implémenter |
| F8 | Pas de page détail fichier | V2 (accepté) |
| F9 | `Parametres.tsx` : pas de bouton « Supprimer le JWT » | Ajouter |

---

## 6. Modèle de données (résumé)

### 6.1 Les 4 groupes

- **A — Référentiels** : `source`, `ref_geo_admin`, `localite`, `localite_alias`
- **B — Ingestion** : `fichier`, `feuille`, `mapping_feuille`, `ingestion_run`, `ligne_ingeree`
- **C — Métier consolidé** : `ouvrage`, `cgpe`, `projet_financement`, `ouvrage_projet`
- **D — Vues** : `v_points_par_fichier`, `v_points_consolides`, `v_qualite_par_fichier`

**13 tables + 3 vues + 3 fonctions + 8 triggers.**

### 6.2 Décisions clés

- Pas de `type_ouvrage` (3 champs : `nature_ouvrage`, `type_alimentation`, `realisation_par`).
- `geom` et `geom_centre` : colonnes générées (`geom_from_latlon`).
- `metadata` (JSONB) : `brut_<entête>` + `metadata.<entité>.<clé>` (explicite).
- `qualite_eau` (JSONB, nullable) : indicateurs sanitaires.
- Dédoublonnage : `code_ouvrage` puis tuple `(id_localite, nature, alimentation, annee)`.
- 6 statuts de qualité : `ok`, `geom_invalide`, `localite_non_resolue`, `type_ouvrage_inconnu`, `rejete`, `doublon_suspect`.
- Pas de `district` (réforme territoriale).

---

## 7. Pipeline d'ingestion (résumé)

### 7.1 Les 5 étapes

1. **Import localités** (script CLI manuel) → `ref_geo_admin` + `localite`.
2. **Ingestion** (`POST /fichiers/{id}/runs`) → `ligne_ingeree` (statut `ok` ou `geom_invalide`, rejets non stockés).
3. **Rapprochement** → `id_localite` (exact > alias > trigram), `localite_non_resolue` si échec.
4. **Consolidation** → `ouvrage` (dédoublonné, `doublon_suspect` si code + > 1 km, `type_ouvrage_inconnu` si attributs indéterminés).
5. **Lecture / export / carto** → `ouvrage` + `ligne_ingeree`.

### 7.2 Scripts CLI

| Script | Étape |
|--------|-------|
| `scripts/import_localites.py` | 1 |
| `scripts/test_ingestion_reelle.py` | 2 |
| `scripts/test_rapprochement.py` | 3 |
| `scripts/consolidation.py` | 4 |

### 7.3 Modes d'ingestion

- `complet` (défaut) : tout le fichier.
- `echantillon` : N premières lignes (`limite_lignes`).
- `plage` : plage (`ligne_debut`, `ligne_fin`).

---

## 8. Démarrage & commandes utiles

### 8.1 Docker Compose

```bash
# Démarrer
docker compose up -d --build

# Logs
docker compose logs -f backend

# Redémarrer le backend
docker compose restart backend

# Arrêter
docker compose down

# Reset complet (perte de données)
docker compose down -v
docker compose up -d --build
```

### 8.2 Base de données

```bash
# psql
docker compose exec db psql -U dhr -d dhr

# Migrations
docker compose exec backend alembic upgrade head

# Reset DB (perte de données)
docker compose exec db psql -U dhr -d dhr -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose exec backend alembic upgrade head

# Vérifier les tables
docker compose exec db psql -U dhr -d dhr -c "\dt"
docker compose exec db psql -U dhr -d dhr -c "\dv"
docker compose exec db psql -U dhr -d dhr -c "\df"
```

### 8.3 Scripts CLI

```bash
# Import des localités (1ère fois)
docker compose exec backend python -u /app/scripts/import_localites.py /app/tests/fixtures/fichier1.xlsx

# Re-consolider un run
docker compose exec db psql -U dhr -d dhr -c "UPDATE ligne_ingeree SET id_ouvrage_consolide = NULL;"
docker compose exec db psql -U dhr -d dhr -c "DELETE FROM ouvrage;"
docker compose exec backend python -u /app/scripts/consolidation.py 1

# Générer un JWT
docker compose exec backend python -c "from app.auth import create_access_token; print(create_access_token('test', 'admin'))"
```

### 8.4 Tests (à appliquer)

```bash
# Créer la base de test
docker compose exec db psql -U dhr -d dhr -c "CREATE DATABASE dhr_test;"

# Ajouter au .env
echo "TEST_DATABASE_URL=postgresql+psycopg://dhr:dhr_dev_password@db:5432/dhr_test" >> .env

# Lancer les tests
docker compose exec backend pytest -v

# Couverture
docker compose exec backend pytest --cov=app --cov-report=term-missing

# Tests d'intégration
docker compose exec backend pytest -m integration -v
```

### 8.5 Qualité

```bash
# Backend
docker compose exec backend ruff check .
docker compose exec backend ruff format .
docker compose exec backend mypy app/services app/models

# Frontend
cd frontend
npm run lint
npm run typecheck
npm run build
```

---

## 9. TODO détaillé

### 9.1 Priorité 1 — Audit schémas + routers (bloquant pour les tests)

- [ ] **`schemas/ouvrages.py`** : vérifier qu'il n'y a pas de `type_ouvrage`, que `nature_ouvrage`, `type_alimentation`, `realisation_par` sont bien exposés.
- [ ] **`schemas/fichiers.py`** : `LigneIngeree` expose `type_ouvrage_brut`, `usage_ouvrage_brut`.
- [ ] **`schemas/referentiels.py`** : pas de `TypeOuvrage`.
- [ ] **`schemas/common.py`** : `Problem`, `PaginationOffset`, `PaginationCursor`.
- [ ] **`schemas/qualite.py`** : `QualiteFichier` avec les 6 statuts.
- [ ] **`routers/ouvrages.py`** : filtres `nature_ouvrage`, `type_alimentation`, `realisation_par` ; **pas de `district`**.
- [ ] **`routers/carto.py`** : idem.
- [ ] **`routers/referentiels.py`** : pas d'endpoint `/types-ouvrage`.
- [ ] **`deps.py`** : `OuvrageFilters` avec les 3 champs, **pas de `district`**.
- [ ] **`main.py`** : vérifier les routers inclus, les handlers d'erreur (RFC 7807).

### 9.2 Priorité 2 — Tests backend

- [ ] Créer `backend/tests/__init__.py` (vide).
- [ ] Créer `backend/tests/conftest.py` (fixtures).
- [ ] Créer `backend/tests/fixtures/__init__.py` (vide).
- [ ] Créer `backend/tests/test_coordonnees.py`.
- [ ] Créer `backend/tests/test_ingestion.py`.
- [ ] Créer `backend/tests/test_rapprochement.py`.
- [ ] Créer `backend/tests/test_consolidation.py`.
- [ ] Créer `backend/tests/test_integration_pipeline.py`.
- [ ] Créer `backend/tests/README.md`.
- [ ] Lancer `pytest`, corriger les échecs (fixtures, base `dhr_test`, imports).

### 9.3 Priorité 3 — CI GitHub Actions

- [ ] Créer `.github/workflows/ci.yml`.
- [ ] Vérifier que la CI passe sur GitHub (lint + typecheck + tests + build).
- [ ] Protéger la branche `main` (pas de push direct).

### 9.4 Priorité 4 — Frontend (F1–F9)

- [ ] **F1** : `Mapping.tsx`, ajouter `usage_ouvrage_brut` à `CHAMPS_STANDARDS`.
- [ ] **F2** : `MapView.tsx`, forme = `nature_ouvrage` (cercle/carré/losange).
- [ ] **F3** : `Liste.tsx`, export via `fetch` + `blob`.
- [ ] **F4** : supprimer `pages/OLD_Carte.tsx`.
- [ ] **F5** : `api.ts`, redirection 401 vers `/parametres`.
- [ ] **F6** : `Skeleton` au lieu de « Chargement... » (toutes les pages).
- [ ] **F7** : implémenter `Liste.tsx` et `Qualite.tsx`.
- [ ] **F9** : `Parametres.tsx`, bouton « Supprimer le JWT ».

### 9.5 Priorité 5 — `openapi.yaml` et `metadata_conventions.md`

- [ ] **O1–O5, OI1–OI2** : aligner `openapi.yaml` sur la Bible (section 7.2).
- [ ] **M1–M6** : réécrire `metadata_conventions.md` (section 7.3).

---

## 10. Dette technique / points ouverts

### 10.1 Écarts Bible ↔ Code (à corriger)

**Section 7.1 de la Bible** (déjà corrigés en Phase D) :

| # | Écart | Statut |
|---|-------|--------|
| B1 | `export.py` importe `TypeOuvrage` | ✅ Corrigé |
| B2 | `models.py` : `nature_ouvrage_brut` / `type_alimentation_brut` | ✅ Corrigé (dans `models.py`) |
| B3 | `models.py` : CHECK `type_alimentation_inconnu` | ✅ Corrigé |
| B4 | `models.py` : `UNIQUE (id_run, num_ligne_source)` | ✅ Corrigé |
| B5 | `ingestion.py` : rejets | ✅ Corrigé |
| B6 | `consolidation.py` : `doublon_suspect`, `type_ouvrage_inconnu`, `qualite_eau` | ✅ Corrigé |
| I1 | `ingestion.py` : `departement_brute` | ✅ Corrigé |
| I2 | `ingestion.py` : `fichier.statut` | ✅ Corrigé |
| I3 | `rapprochement.py` : `message_qualite` | ✅ Corrigé |
| I4 | `models.py` : index `idx_ligne_nature_ouvrage` | ✅ Corrigé |

**Écarts restants** :

| # | Écart | Statut |
|---|-------|--------|
| F1–F9 | Frontend | ⏳ À corriger |
| O1–O5, OI1–OI2 | `openapi.yaml` | ⏳ À aligner |
| M1–M6 | `metadata_conventions.md` | ⏳ À réécrire |
| Audit `schemas/*` | Inconnu | ⏳ À faire |
| Audit `routers/*` | Inconnu | ⏳ À faire |
| Audit `deps.py` | Inconnu | ⏳ À faire |
| Audit `main.py` | Inconnu | ⏳ À faire |

### 10.2 Contraintes acceptées au MVP

- Pas de filtre `district` dans l'UI.
- Dédoublonnage `code_ouvrage` sans `id_localite`.
- Trigram sans filtre sous-préfecture.
- Lignes rejetées non stockées.
- Alias localités non alimentés.
- CGPE non créés.
- Projets de financement non créés.
- Import auto localités (V2).
- Création manuelle localités/ouvrages (V2).
- Pas de gestion utilisateurs (rôles) (V2).
- Pas de déploiement prod (V2).
- `Localite.geom_centre` non exposé en liste (V2).
- Filtre bailleur exposé sans données.
- `metadata` non normalisé (`brut_<entête>`).
- `attribut_definition` + `ouvrage_attribut` absents (V2).

### 10.3 Points ouverts du handoff précédent

| # | Point | Statut |
|---|-------|--------|
| D1 | Filtre bailleur (backend OK, pas de données) | Accepté |
| D2 | Import auto localités | V2 |
| D3 | Attributs `metadata` dynamiques (mapping UI) | Partiel (F1) |
| D4 | Création manuelle localités | V2 |
| D5 | `Localite.geom_centre` non sérialisé | V2 |
| D6 | DMS corrompu (1 ligne) | Accepté |
| D7 | Déploiement prod | V2 |
| D8 | Gestion utilisateurs | V2 |
| D9 | Refactoring exports (KPI) | ✅ Résolu (B1) |

---

## 11. Décisions structurantes

Voir Bible § 1.4 (10 décisions) et section 6 (18 ADR).

### 11.1 Les 10 décisions de la Bible

1. Un ouvrage sans GPS n'existe pas.
2. Localités importées manuellement.
3. 3 champs sémantiques (`nature_ouvrage`, `type_alimentation`, `realisation_par`).
4. Attributs non mappés → JSONB (`brut_<entête>`).
5. Données sanitaires → `qualite_eau` (JSONB, nullable).
6. Pas de filtre `district` (sauf KPI export).
7. Mapping proposé auto, corrigeable via UI.
8. Repartir sur des bases saines (migration initiale unique).
9. 6 statuts de qualité implémentés.
10. Métadonnées explicites via `metadata.<entité>.<clé>`.

### 11.2 Les 18 ADR

Voir Bible section 6 :
- ADR-001 : PostgreSQL + PostGIS
- ADR-002 : JSONB pour les attributs non mappés
- ADR-003 : Colonnes générées pour `geom`
- ADR-004 : Trigram + unaccent
- ADR-005 : `serial` / `bigserial` (pas d'UUID)
- ADR-006 : FastAPI + SQLAlchemy 2.0 + Pydantic 2
- ADR-007 : React + Vite + TypeScript + shadcn/ui
- ADR-008 : Leaflet + Esri World Imagery
- ADR-009 : TanStack Query
- ADR-010 : Auth MVP = API key + JWT manuel
- ADR-011 : Pagination offset + cursor
- ADR-012 : RFC 7807
- ADR-013 : `metadata.<entité>.<clé>`
- ADR-014 : Suppression de `type_ouvrage`
- ADR-015 : 6 statuts de qualité
- ADR-016 : Dédoublonnage par `code_ouvrage` puis tuple
- ADR-017 : Pas de filtre `district`
- ADR-018 : Migration initiale unique

---

## 12. Documents de référence

| Document | Rôle | Statut |
|----------|------|--------|
| `DHR.md` | Bible du projet (fait autorité) | ✅ v1.0 |
| `CONSTITUTION.md` | Contrat opérationnel de l'équipe | ✅ v1.0 |
| `tests-db.md` | Tests de la base de données | ✅ Complet |
| `backend/tests/README.md` | Documentation des tests backend | 📦 Livré |
| `openapi.yaml` | Contrat d'API détaillé | ⏳ À aligner (O1–O5, OI1–OI2) |
| `metadata_conventions.md` | Conventions des métadonnées | ⏳ À réécrire (M1–M6) |
| `HANDOFF.md` | Ce document | ✅ v1.0 |

---

## 13. Commandes de reprise

Pour reprendre le projet, dire :

> « Je reprends le projet DHR. Voici le handoff (`HANDOFF.md`), la Bible (`DHR.md`) et la Constitution (`CONSTITUTION.md`). La Phase C (socle DB) est terminée et validée. La Phase D (services) est en cours : `ingestion.py`, `rapprochement.py`, `consolidation.py`, `run.py`, `export.py` sont corrigés et testés. Il reste à :
> 1. Auditer `app/schemas/*`, `app/routers/*`, `app/deps.py`, `app/main.py` pour vérifier l'alignement sur la Bible.
> 2. Appliquer les tests backend (`backend/tests/`), lancer `pytest`, corriger les échecs.
> 3. Appliquer la CI GitHub Actions (`.github/workflows/ci.yml`).
> 4. Corriger le frontend (F1–F9).
> 5. Aligner `openapi.yaml` (O1–O5, OI1–OI2) et `metadata_conventions.md` (M1–M6).
>
> On commence par l'audit des schémas et routers. »

---

## Annexe A — Tableau de correspondance Bible ↔ Code

| Bible | Code | Statut |
|-------|------|--------|
| § 1.4 décision 3 | `nature_ouvrage`, `type_alimentation`, `realisation_par` | ✅ |
| § 1.4 décision 6 | Pas de filtre `district` | ✅ |
| § 1.4 décision 9 | 6 statuts de qualité | ✅ |
| § 2.1.6 | Migration initiale unique | ✅ |
| § 2.2.B | `ligne_ingeree.type_ouvrage_brut`, `usage_ouvrage_brut` | ✅ |
| § 2.2.C | `ouvrage` : 3 champs sémantiques | ✅ |
| § 2.3.1 | `geom_from_latlon` | ✅ |
| § 2.3.2 | 8 triggers | ✅ |
| § 3.1.6 | 6 statuts de qualité | ✅ |
| § 3.2.1 | Ingestion (rejets, `nb_lignes_total`) | ✅ |
| § 3.2.2 | Rapprochement (`message_qualite` strict) | ✅ |
| § 3.2.3 | Consolidation (`doublon_suspect`, `type_ouvrage_inconnu`, `qualite_eau`) | ✅ |
| § 3.2.4 | `run.py` (`fichier.statut` en fin de pipeline) | ✅ |
| § 4.3.4 | Filtres `nature_ouvrage`, `type_alimentation`, `realisation_par` | ⏳ (routers à auditer) |
| § 5.4 | Frontend | ⏳ (F1–F9) |
| § 7.1 | Écarts B/I | ✅ (sauf F, O, M) |
| § 8.3 | Tests | 📦 (à appliquer) |
| § 8.4 | CI | 📦 (à appliquer) |

---

## Annexe B — État des fichiers

### Backend — Services

| Fichier | Statut |
|---------|--------|
| `services/coordonnees.py` | ✅ Conforme |
| `services/patterns.py` | ✅ Aligné |
| `services/mapping.py` | ✅ Conforme |
| `services/upload.py` | ✅ Conforme (à vérifier) |
| `services/ingestion.py` | ✅ Corrigé (B5, I1, I2, P12) |
| `services/rapprochement.py` | ✅ Corrigé (I3) |
| `services/consolidation.py` | ✅ Corrigé (B6.1, B6.2, B6.3) |
| `services/export.py` | ✅ Corrigé (B1) |
| `services/run.py` | ✅ Corrigé (I2) |

### Backend — Modèles et schémas

| Fichier | Statut |
|---------|--------|
| `models.py` | ✅ Aligné (13 modèles) |
| `schemas/__init__.py` | ⏳ À auditer |
| `schemas/common.py` | ⏳ À auditer |
| `schemas/ouvrages.py` | ⏳ À auditer |
| `schemas/fichiers.py` | ⏳ À auditer |
| `schemas/referentiels.py` | ⏳ À auditer |
| `schemas/qualite.py` | ⏳ À auditer |

### Backend — Routers

| Fichier | Statut |
|---------|--------|
| `routers/__init__.py` | ⏳ À auditer |
| `routers/ouvrages.py` | ⏳ À auditer |
| `routers/carto.py` | ⏳ À auditer |
| `routers/referentiels.py` | ⏳ À auditer |
| `routers/fichiers.py` | ⏳ À auditer |
| `routers/ingestion.py` | ⏳ À auditer |
| `routers/qualite.py` | ⏳ À auditer |
| `main.py` | ⏳ À auditer |
| `deps.py` | ⏳ À auditer |

### Backend — Migrations et SQL

| Fichier | Statut |
|---------|--------|
| `sql/schema.sql` | ✅ Généré |
| `alembic/versions/0001_initial.py` | ✅ Appliqué |
| `alembic/env.py` | ✅ Corrigé |
| `pyproject.toml` | ✅ Complet |

### Backend — Tests

| Fichier | Statut |
|---------|--------|
| `tests/__init__.py` | ⏳ À créer |
| `tests/conftest.py` | 📦 Livré, à appliquer |
| `tests/fixtures/__init__.py` | 📦 Livré, à appliquer |
| `tests/test_coordonnees.py` | 📦 Livré, à appliquer |
| `tests/test_ingestion.py` | 📦 Livré, à appliquer |
| `tests/test_rapprochement.py` | 📦 Livré, à appliquer |
| `tests/test_consolidation.py` | 📦 Livré, à appliquer |
| `tests/test_integration_pipeline.py` | 📦 Livré, à appliquer |
| `tests/README.md` | 📦 Livré, à appliquer |

### Frontend

| Fichier | Statut |
|---------|--------|
| `pages/Fichiers.tsx` | ✅ |
| `pages/Mapping.tsx` | ✅ (F1 à corriger) |
| `pages/Carte.tsx` | ✅ |
| `pages/Liste.tsx` | ⏳ (F7) |
| `pages/Qualite.tsx` | ⏳ (F7) |
| `pages/Parametres.tsx` | ✅ (F9 à corriger) |
| `pages/OLD_Carte.tsx` | 🗑️ À supprimer (F4) |
| `components/FiltersPanel.tsx` | ✅ |
| `components/MapView.tsx` | ✅ (F2 à corriger) |
| `components/RunStatus.tsx` | ✅ |
| `components/UploadDialog.tsx` | ✅ |
| `lib/api.ts` | ✅ (F5 à corriger) |

### CI

| Fichier | Statut |
|---------|--------|
| `.github/workflows/ci.yml` | 📦 Livré, à appliquer |

---

## Annexe C — Historique des décisions de la session

| Date | Décision |
|------|----------|
| 2026-11-09 | Démarrage de la Bible v1.0 |
| 2026-11-10 | Bible v1.0 finalisée (sections 1–8) |
| 2026-11-10 | Constitution v1.0 finalisée |
| 2026-11-10 | Phase C (socle DB) terminée |
| 2026-11-10 | `schema.sql` + `0001_initial.py` + `models.py` appliqués |
| 2026-11-10 | Backend démarre (`/health` OK) |
| 2026-11-10 | Phase D : `ingestion.py`, `rapprochement.py`, `consolidation.py`, `run.py`, `export.py` corrigés |
| 2026-11-10 | `export.py` validé avec 1 ouvrage (4 KPI corrects) |
| 2026-11-10 | Décision : audit `schemas/*` + `routers/*` avant tests |
| 2026-11-10 | Handoff v1.0 produit |

---

**Fin du handoff.** Ce document capture l'état du projet au **2026-11-10**. Pour reprendre, lire ce handoff, puis la Bible (`DHR.md`) et la Constitution (`CONSTITUTION.md`). En cas de conflit, la Bible fait autorité.