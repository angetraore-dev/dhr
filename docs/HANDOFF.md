
---

# Handoff — Projet DHR

**Date** : 2026-10-27
**Version** : 2.0 (Phase 1-2 terminées, Phase 3 démarrée)
**Objet** : Centralisation des ouvrages hydrauliques ruraux pour la Direction de l'Hydraulique Rurale (DHR)

---

## 1. Contexte métier

La DHR reçoit des fichiers Excel hétérogènes (ONEP, SODECI, UNICEF, BAD, LONACI, État) contenant des données sur les ouvrages hydrauliques ruraux, les CGPE et les financements. Elle veut centraliser ces données dans une base PostgreSQL/PostGIS et disposer d'une UI cartographique (vue satellite) permettant d'afficher les points d'un fichier ou tous les points consolidés, ainsi qu'une vue liste exportable en Excel/CSV.

Le projet est en phase MVP : **lecture + ingestion + carto + export**. L'écriture manuelle et l'analytique avancée sont hors scope.

---

## 2. État d'avancement

### ✅ Terminé

| Phase                                   | Contenu                                                                                        | Statut |
|-----------------------------------------|------------------------------------------------------------------------------------------------|--------|
| **Conception**                          | MCDR, MLDR, diagramme UML, `schema.sql`, `openapi.yaml`, conventions metadata                  | ✅      |
| **Phase 1 — Infrastructure**            | Docker Compose (Postgres/PostGIS + FastAPI + Vite), config, db, entrypoint                     | ✅      |
| **Phase 2 — Modèles + migration**       | 13 tables SQLAlchemy, migration Alembic complétée, extensions, fonctions, triggers, vues, seed | ✅      |
| **Phase 3.1 — Schémas Pydantic + auth** | `schemas/`, `auth.py`, `deps.py`, `main.py` mis à jour                                         | ✅      |

### 🔄 En cours

| Phase                                              | Contenu                                                         | Statut       |
|----------------------------------------------------|-----------------------------------------------------------------|--------------|
| **Phase 3.2 — Routers référentiels + fichiers**    | `routers/referentiels.py`, `routers/fichiers.py`                | ⏳ à produire |
| **Phase 3.3 — Routers carto + ouvrages + qualité** | `routers/carto.py`, `routers/ouvrages.py`, `routers/qualite.py` | ⏳ à produire |

### ⏳ À faire

| Phase                   | Contenu                                                     |
|-------------------------|-------------------------------------------------------------|
| **Phase 4 — Ingestion** | Service de parsing Excel multi-feuilles, upload, runs       |
| **Phase 5 — Export**    | Export Excel/CSV streamé                                    |
| **Phase 6 — Front**     | React + Vite + Leaflet + pages Fichiers/Carte/Liste/Qualité |
| **Phase 7 — Tests**     | Tests d'API, tests d'ingestion, tests d'export              |

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
| Auth            | python-jose (JWT) + API key  | —            |
| Front-end       | React + Vite + TypeScript    | 18 + 5.4     |
| UI              | Tailwind + shadcn/ui         | 3.4          |
| Carto           | Leaflet + Esri World Imagery | 1.9          |
| État API        | TanStack Query               | 5.59         |
| Tableaux        | TanStack Table               | 8.20         |
| Conteneurs      | Docker Compose               | —            |

### 3.2 Arborescence actuelle

```text
dhr/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── sql/
│   └── schema.sql                    (documentation de référence, non monté)
├── docs/
│   ├── mcdr.puml                     (MCDR métier)
│   ├── mldr.md                       (MLDR technique, v1.2)
│   ├── mcd.puml                      (diagramme de classes UML)
│   ├── openapi.yaml                  (contrat d'API v1.2, 25 endpoints)
│   ├── metadata_conventions.md       (conventions metadata)
│   └── HANDOFF.md                    (ce document)
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py                    (filtrage strict NOS_TABLES)
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── a3187e43649b_initial_schema.py   (complétée manuellement)
│   └── app/
│       ├── __init__.py
│       ├── main.py                   (avec routers branchés)
│       ├── config.py                 (Settings Pydantic)
│       ├── db.py                     (engine, session, get_db, check_db)
│       ├── models.py                 (13 tables SQLAlchemy/GeoAlchemy2)
│       ├── auth.py                   (API key + JWT)
│       ├── deps.py                   (pagination, filtres)
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── common.py
│       │   ├── geo.py
│       │   ├── referentiels.py
│       │   ├── fichiers.py
│       │   ├── ingestion.py
│       │   └── ouvrages.py
│       └── routers/
│           └── __init__.py           (vide pour l'instant)
└── frontend/
├── Dockerfile
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
└── src/
├── main.tsx
├── App.tsx
├── index.css
└── vite-env.d.ts
```

### 3.3 Modèle de données (13 tables)

**Référentiels** :
- `source` — ONEP, SODECI, UNICEF, BAD, LONACI, ETAT_CI (seedés)
- `type_ouvrage` — PMH, HV, HVA, PEA, AUTRE (seedés)
- `ref_geo_admin` — hiérarchie district→région→département→sous-préf→localité (auto-référencée)
- `localite` — village/campement rattaché à un nœud `localite` du référentiel
- `localite_alias` — alias pour rapprochement flou

**Ingestion** :
- `fichier` — fichier uploadé
- `feuille` — feuille Excel
- `ingestion_run` — exécution avec paramètres (mode complet/echantillon/plage)
- `ligne_ingeree` — ligne normalisée + `donnees_brutes` JSONB

**Métier** :
- `ouvrage` — ouvrage consolidé avec `metadata` JSONB
- `cgpe` — comité de gestion avec `metadata` JSONB
- `projet_financement` — projet bailleur
- `ouvrage_projet` — liaison N..N (co-financement)

### 3.4 Décisions de conception figées

| Décision                                                         | Raison                                      |
|------------------------------------------------------------------|---------------------------------------------|
| `hash_sha256` **non unique** sur `fichier`                       | Réingestion légitime pour d'autres feuilles |
| `code_ouvrage` **nullable, non unique**                          | Pas d'identifiant métier stable fourni      |
| `UNIQUE (id_run, num_ligne_source)`                              | Plusieurs runs sur la même feuille          |
| `metadata JSONB` sur `localite`, `ouvrage`, `cgpe`               | Capturer les colonnes non mappées           |
| `donnees_brutes JSONB` sur `ligne_ingeree`                       | Source brute immuable                       |
| Colonnes générées `geom`                                         | Via `geom_from_latlon(lat, lon)` STORED     |
| `geom_from_latlon` STRICT + rejet (0,0)                          | Éviter les coordonnées aberrantes           |
| Extensions : `postgis`, `fuzzystrmatch`, `unaccent`, `pg_trgm`   | Pas `postgis_topology` (inutile MVP)        |
| Auth : API key (lecture) + JWT (écriture)                        | Séparation lecture/écriture                 |
| Pagination : offset (petites listes) / cursor (lignes, ouvrages) | Adapter au volume                           |
| `bbox` GeoJSON calculé côté front                                | Alléger la réponse back                     |
| Export Excel/CSV streamé                                         | Éviter le chargement complet en RAM         |

---

## 4. Contrat d'API (25 endpoints)

Base URL : `https://api.dhr.local/v1` (placeholder, à remplacer)

### 4.1 Authentification

| Méthode                                        | Usage                        |
|------------------------------------------------|------------------------------|
| **API key** (`X-API-Key`)                      | Lecture (consultation)       |
| **JWT Bearer** (`Authorization: Bearer <jwt>`) | Écriture (ingestion, upload) |

### 4.2 Endpoints

| Méthode | Endpoint                              | Auth    | Statut       |
|---------|---------------------------------------|---------|--------------|
| GET     | `/sources`                            | API key | ⏳ à produire |
| GET     | `/types-ouvrage`                      | API key | ⏳ à produire |
| GET     | `/ref-geo`                            | API key | ⏳ à produire |
| GET     | `/ref-geo/{id}/chemin`                | API key | ⏳ à produire |
| GET     | `/localites`                          | API key | ⏳ à produire |
| GET     | `/localites/{id}`                     | API key | ⏳ à produire |
| GET     | `/fichiers`                           | API key | ⏳ à produire |
| GET     | `/fichiers/{id}`                      | API key | ⏳ à produire |
| POST    | `/fichiers`                           | JWT     | ⏳ Phase 4    |
| GET     | `/fichiers/{id}/feuilles`             | API key | ⏳ à produire |
| POST    | `/fichiers/{id}/runs`                 | JWT     | ⏳ Phase 4    |
| GET     | `/fichiers/{id}/runs`                 | API key | ⏳ à produire |
| GET     | `/runs/{id}`                          | API key | ⏳ à produire |
| GET     | `/feuilles/{id}/lignes`               | API key | ⏳ à produire |
| GET     | `/runs/{id}/lignes`                   | API key | ⏳ à produire |
| GET     | `/lignes/{id}`                        | API key | ⏳ à produire |
| GET     | `/ouvrages`                           | API key | ⏳ à produire |
| GET     | `/ouvrages/{id}`                      | API key | ⏳ à produire |
| GET     | `/ouvrages/export`                    | API key | ⏳ Phase 5    |
| GET     | `/ouvrages/export.csv`                | API key | ⏳ Phase 5    |
| GET     | `/cgpe/{id}`                          | API key | ⏳ à produire |
| GET     | `/carto/fichiers/{id}/points`         | API key | ⏳ à produire |
| GET     | `/carto/tous/points`                  | API key | ⏳ à produire |
| GET     | `/carto/fichiers/{id}/points.geojson` | API key | ⏳ à produire |
| GET     | `/qualite/fichiers/{id}`              | API key | ⏳ à produire |

Le détail complet des schémas de réponse est dans `docs/openapi.yaml`.

---

## 5. Démarrage

### 5.1 Première installation

```powershell
# 1. Cloner le repo
git clone <url> dhr
cd dhr

# 2. Copier le template d'env
cp .env.example .env
# (ou : Copy-Item .env.example .env sous PowerShell)

# 3. (Optionnel) Générer un JWT_SECRET robuste
# openssl rand -hex 32  → coller dans .env

# 4. Démarrer
docker compose up -d --build

# 5. Vérifier
docker compose ps
# Attendu : 3 services (db healthy, backend healthy, frontend running)

curl http://localhost:8000/health
# Attendu : {"status":"ok","db":true,"version":"0.1.0","env":"development"}

# 6. Swagger UI
# Ouvrir http://localhost:8000/docs

# 7. Front
# Ouvrir http://localhost:5173
```

### 5.2 Commandes utiles

```powershell
# Logs
docker compose logs -f backend
docker compose logs -f db

# Shell dans le container back
docker compose exec backend bash

# Shell psql
docker compose exec db psql -U dhr -d dhr

# Arrêter
docker compose down

# Arrêter + supprimer les volumes (⚠️ perte de données)
docker compose down -v

# Rebuilder
docker compose up -d --build

# Redémarrer le back
docker compose restart backend
```

### 5.3 Commandes Alembic

```powershell
# Statut
docker compose exec backend alembic current

# Historique
docker compose exec backend alembic history

# Appliquer
docker compose exec backend alembic upgrade head

# Créer une migration (après modif de models.py)
docker compose exec backend alembic revision --autogenerate -m "description"

# Downgrade
docker compose exec backend alembic downgrade -1
```

### 5.4 Générer un JWT pour tester l'écriture

```powershell
docker compose exec backend python -c "
from app.auth import create_access_token
print(create_access_token('test-user', 'admin'))
"
```

Puis :

```powershell
curl -H "Authorization: Bearer <jwt>" -X POST http://localhost:8000/v1/fichiers ...
```

---

## 6. Points d'attention (pièges connus)

| Piège                                                          | Solution                                                                        |
|----------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Migration Alembic contient les `drop_table` PostGIS**        | Résolu : `env.py` filtre via `NOS_TABLES = set(Base.metadata.tables.keys())`    |
| **`server_default="'{}'::jsonb"` crée un DEFAULT invalide**    | Utiliser `server_default=text("'{}'::jsonb")`                                   |
| **`alembic upgrade head` au démarrage du backend**             | `entrypoint.sh` le fait automatiquement                                         |
| **Le backend crash en boucle si migration pourrie**            | `docker compose logs backend` → identifier → supprimer la migration → régénérer |
| **`include_schemas=False` ne suffit pas**                      | Filtre liste blanche `NOS_TABLES` obligatoire                                   |
| **`localite.metadata_` (Python) vs `localite.metadata` (SQL)** | Pydantic utilise `from_attributes=True` + alias si besoin                       |
| **`node_modules` conflit host/container**                      | Volume nommé `frontend_node_modules`                                            |
| **Hot-reload Vite KO dans Docker**                             | `usePolling: true` dans `vite.config.ts`                                        |
| **`postgis_topology` non activé**                              | Décision MVP : pas besoin de topologie                                          |
| **Seed réexécuté à chaque `upgrade`**                          | `ON CONFLICT DO NOTHING`                                                        |

---

## 7. Dette technique / points ouverts

| # | Point                                                    | Impact        | À traiter          |
|---|----------------------------------------------------------|---------------|--------------------|
| 1 | Déploiement prod (VPS interne vs cloud)                  | Infra         | V2                 |
| 2 | Nom de domaine réel (`api.dhr.local` placeholder)        | Config        | Prod               |
| 3 | Politique de rétention des fichiers bruts                | Stockage      | V2                 |
| 4 | Gestion des utilisateurs (table `utilisateur` vs config) | Auth          | Config pour MVP    |
| 5 | Règle de rapprochement des ouvrages (GPS + nom + année)  | Dédoublonnage | V2                 |
| 6 | Valeur exacte de `MAX_EXPORT_ROWS`                       | Export        | 100 000 par défaut |
| 7 | `localite.metadata_` → `metadata` (mapping Pydantic)     | Schémas       | À finaliser en 3.2 |
| 8 | Rapprochement flou des localités (trigram + alias)       | Ingestion     | Phase 4            |
| 9 | Tests unitaires et d'intégration                         | Qualité       | Phase 7            |

---

## 8. Historique des versions

| Version | Date       | Changement                                                                              |
|---------|------------|-----------------------------------------------------------------------------------------|
| 1.0     | 2026-10-23 | Conception initiale (23 endpoints)                                                      |
| 1.1     | 2026-10-23 | Ajout `metadata` sur `localite`, `ouvrage`, `cgpe`                                      |
| 1.2     | 2026-10-26 | Ajout vue liste + export Excel/CSV (25 endpoints)                                       |
| 2.0     | 2026-10-27 | Phase 1-2 terminées (infra + modèles + migration). Phase 3.1 terminée (schémas + auth). |

---

## 9. Prochaine action immédiate

**Phase 3.2 — Routers référentiels + fichiers** :

1. `backend/app/routers/__init__.py` (déjà créé vide)
2. `backend/app/routers/referentiels.py` — 6 endpoints :
    - `GET /sources`
    - `GET /types-ouvrage`
    - `GET /ref-geo`
    - `GET /ref-geo/{id}/chemin`
    - `GET /localites`
    - `GET /localites/{id}`
3. `backend/app/routers/fichiers.py` — 3 endpoints :
    - `GET /fichiers`
    - `GET /fichiers/{id}`
    - `GET /fichiers/{id}/feuilles`

**Critère de validation** : `http://localhost:8000/docs` affiche les 6 + 3 endpoints, et `curl -H "X-API-Key: ..." http://localhost:8000/v1/sources` retourne les 6 sources seedées.

---

*Handoff rédigé le 2026-10-27. Toute modification du contrat d'API ou du schéma doit être répercutée dans les 5 livrables de conception (`mcdr.puml`, `mldr.md`, `mcd.puml`, `openapi.yaml`, `metadata_conventions.md`) avant implémentation.*


