
---

## `docs/HANDOFF.md` — version complète


# Handoff — Projet DHR

**Date** : 2026-10-27
**Version** : 2.1 (Phase 1-2-3 terminées)
**Objet** : Centralisation des ouvrages hydrauliques ruraux pour la Direction de l'Hydraulique Rurale (DHR)

---

## 1. Contexte métier

La DHR reçoit des fichiers Excel hétérogènes (ONEP, SODECI, UNICEF, BAD, LONACI, État) contenant des données sur les ouvrages hydrauliques ruraux, les CGPE et les financements. Elle veut centraliser ces données dans une base PostgreSQL/PostGIS et disposer d'une UI cartographique (vue satellite) permettant d'afficher les points d'un fichier ou tous les points consolidés, ainsi qu'une vue liste exportable en Excel/CSV.

Le projet est en phase MVP : **lecture + ingestion + carto + export**. L'écriture manuelle et l'analytique avancée sont hors scope.

---

### ✅ Terminé

| Phase                             | Contenu                                                                        | Statut |
|-----------------------------------|--------------------------------------------------------------------------------|--------|
| **Conception**                    | MCDR, MLDR, diagramme UML, `schema.sql`, `openapi.yaml`, conventions metadata  | ✅      |
| **Phase 1 — Infrastructure**      | Docker Compose, config, db, entrypoint                                         | ✅      |
| **Phase 2 — Modèles + migration** | 13 tables, migration Alembic complète                                          | ✅      |
| **Phase 3 — API lecture**         | 18 endpoints (référentiels, fichiers, ouvrages, CGPE, carto, qualité)          | ✅      |
| **Phase 5 — Export**              | Excel (XlsxWriter + Synthèse KPI) + CSV, colonne N°, limite 413 (20 endpoints) | ✅      |

### ⏳ À faire

| Phase                   | Contenu                                                  |
|-------------------------|----------------------------------------------------------|
| **Phase 4 — Ingestion** | Parsing Excel multi-feuilles, upload, runs (5 endpoints) |
| **Phase 6 — Front**     | React + Vite + Leaflet + pages                           |
| **Phase 7 — Tests**     | Tests d'API, d'ingestion, d'export                       |

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
│       ├── main.py                   (ORJSONResponse utf-8 + 5 routers)
│       ├── config.py                 (Settings Pydantic)
│       ├── db.py                     (engine, session, get_db, check_db)
│       ├── models.py                 (13 tables SQLAlchemy/GeoAlchemy2)
│       ├── auth.py                   (API key + JWT)
│       ├── deps.py                   (OffsetPagination, CursorPagination, OuvrageFilters)
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── common.py             (Problem, Pagination)
│       │   ├── geo.py                (GeoJSONPoint, Feature)
│       │   ├── referentiels.py       (Source, TypeOuvrage, RefGeoAdmin, Localite)
│       │   ├── fichiers.py           (Fichier, Feuille)
│       │   ├── ingestion.py          (IngestionRun, LigneIngeree, Run*)
│       │   └── ouvrages.py           (Ouvrage, CGPE, QualiteFichier)
│       └── routers/
│           ├── __init__.py
│           ├── referentiels.py       (6 endpoints)
│           ├── fichiers.py           (3 endpoints)
│           ├── ouvrages.py           (2 endpoints)
│           ├── carto.py              (3 endpoints GeoJSON)
│           └── qualite.py            (1 endpoint)
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
| `Content-Type: application/json; charset=utf-8`                  | Fix encodage UTF-8 (PowerShell)             |

---

## 4. Contrat d'API (25 endpoints)

Base URL : `https://api.dhr.local/v1` (placeholder, à remplacer)

### 4.1 Authentification

| Méthode                                        | Usage                        |
|------------------------------------------------|------------------------------|
| **API key** (`X-API-Key`)                      | Lecture (consultation)       |
| **JWT Bearer** (`Authorization: Bearer <jwt>`) | Écriture (ingestion, upload) |

### 4.2 Endpoints

| Méthode | Endpoint                              | Auth    | Statut    |
|---------|---------------------------------------|---------|-----------|
| GET     | `/sources`                            | API key | ✅         |
| GET     | `/types-ouvrage`                      | API key | ✅         |
| GET     | `/ref-geo`                            | API key | ✅         |
| GET     | `/ref-geo/{id}/chemin`                | API key | ✅         |
| GET     | `/localites`                          | API key | ✅         |
| GET     | `/localites/{id}`                     | API key | ✅         |
| GET     | `/fichiers`                           | API key | ✅         |
| GET     | `/fichiers/{id}`                      | API key | ✅         |
| POST    | `/fichiers`                           | JWT     | ⏳ Phase 4 |
| GET     | `/fichiers/{id}/feuilles`             | API key | ✅         |
| POST    | `/fichiers/{id}/runs`                 | JWT     | ⏳ Phase 4 |
| GET     | `/fichiers/{id}/runs`                 | API key | ⏳ Phase 4 |
| GET     | `/runs/{id}`                          | API key | ⏳ Phase 4 |
| GET     | `/feuilles/{id}/lignes`               | API key | ⏳ Phase 4 |
| GET     | `/runs/{id}/lignes`                   | API key | ⏳ Phase 4 |
| GET     | `/lignes/{id}`                        | API key | ⏳ Phase 4 |
| GET     | `/ouvrages`                           | API key | ✅         |
| GET     | `/ouvrages/{id}`                      | API key | ✅         |
| GET     | `/ouvrages/export`                    | API key | ⏳ Phase 5 |
| GET     | `/ouvrages/export.csv`                | API key | ⏳ Phase 5 |
| GET     | `/cgpe/{id}`                          | API key | ✅         |
| GET     | `/carto/fichiers/{id}/points`         | API key | ✅         |
| GET     | `/carto/tous/points`                  | API key | ✅         |
| GET     | `/carto/fichiers/{id}/points.geojson` | API key | ✅         |
| GET     | `/qualite/fichiers/{id}`              | API key | ✅         |

**18/25 endpoints opérationnels** (Phase 3 terminée). 7 restants : 5 pour l'ingestion (Phase 4), 2 pour l'export (Phase 5).

Le détail complet des schémas de réponse est dans `docs/openapi.yaml`.

---

## 5. Démarrage

### 5.1 Première installation

```powershell
# 1. Cloner le repo
git clone <url> dhr
cd dhr

# 2. Copier le template d'env
Copy-Item .env.example .env

# 3. (Optionnel) Générer un JWT_SECRET robuste
# openssl rand -hex 32  → coller dans .env

# 4. Démarrer
docker compose up -d --build

# 5. Vérifier
docker compose ps
# Attendu : 3 services (db healthy, backend healthy, frontend running)

curl.exe http://localhost:8000/health
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

### 5.4 Tester l'API lecture

```powershell
$apiKey = "dhr_dev_read_key_change_me"

# Sources (6 seedées)
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/sources

# Types d'ouvrage (5 seedés)
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/types-ouvrage

# Ouvrages (vide pour l'instant)
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/ouvrages

# Carto (FeatureCollection vide)
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/carto/tous/points

# Sans clé → 401
curl.exe -i http://localhost:8000/v1/sources

# Mauvaise clé → 401
curl.exe -i -H "X-API-Key: mauvaise_cle" http://localhost:8000/v1/sources
```

### 5.5 Générer un JWT pour tester l'écriture (Phase 4+)

```powershell
docker compose exec backend python -c "
from app.auth import create_access_token
print(create_access_token('test-user', 'admin'))
"
```

Puis :

```powershell
curl.exe -H "Authorization: Bearer <jwt>" -X POST http://localhost:8000/v1/fichiers ...
```

---

## 6. Points d'attention (pièges connus)

| Piège                                                           | Solution                                                                        |
|-----------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Migration Alembic contient les `drop_table` PostGIS**         | Résolu : `env.py` filtre via `NOS_TABLES = set(Base.metadata.tables.keys())`    |
| **`server_default="'{}'::jsonb"` crée un DEFAULT invalide**     | Utiliser `server_default=text("'{}'::jsonb")`                                   |
| **`alembic upgrade head` au démarrage du backend**              | `entrypoint.sh` le fait automatiquement                                         |
| **Le backend crash en boucle si migration pourrie**             | `docker compose logs backend` → identifier → supprimer la migration → régénérer |
| **`include_schemas=False` ne suffit pas**                       | Filtre liste blanche `NOS_TABLES` obligatoire                                   |
| **Encodage UTF-8 mal interprété par PowerShell**                | `ORJSONResponse` avec `media_type = "application/json; charset=utf-8"`          |
| **`operationId` dupliqué si une route appelle une autre route** | Extraire la logique dans une fonction non décorée (`_build_...`)                |
| **`localite.metadata_` (Python) vs `localite.metadata` (SQL)**  | Accéder explicitement à `loc.metadata_` dans le router                          |
| **`node_modules` conflit host/container**                       | Volume nommé `frontend_node_modules`                                            |
| **Hot-reload Vite KO dans Docker**                              | `usePolling: true` dans `vite.config.ts`                                        |
| **`postgis_topology` non activé**                               | Décision MVP : pas besoin de topologie                                          |
| **Seed réexécuté à chaque `upgrade`**                           | `ON CONFLICT DO NOTHING`                                                        |

---

## 7. Dette technique / points ouverts

| #  | Point                                                    | Impact        | À traiter             |
|----|----------------------------------------------------------|---------------|-----------------------|
| 1  | Déploiement prod (VPS interne vs cloud)                  | Infra         | V2                    |
| 2  | Nom de domaine réel (`api.dhr.local` placeholder)        | Config        | Prod                  |
| 3  | Politique de rétention des fichiers bruts                | Stockage      | V2                    |
| 4  | Gestion des utilisateurs (table `utilisateur` vs config) | Auth          | Config pour MVP       |
| 5  | Règle de rapprochement des ouvrages (GPS + nom + année)  | Dédoublonnage | V2                    |
| 6  | Valeur exacte de `MAX_EXPORT_ROWS`                       | Export        | 100 000 par défaut    |
| 7  | Rapprochement flou des localités (trigram + alias)       | Ingestion     | Phase 4               |
| 8  | Tests unitaires et d'intégration                         | Qualité       | Phase 7               |
| 9  | `Localite.geom_centre` non sérialisé en GeoJSON          | Schémas       | V2 (non bloquant)     |
| 10 | `bbox` non inclus dans les réponses GeoJSON              | Carto         | Front (calcul client) |

---

## 8. Historique des versions

| Version | Date       | Changement                                                                              |
|---------|------------|-----------------------------------------------------------------------------------------|
| 1.0     | 2026-10-23 | Conception initiale (23 endpoints)                                                      |
| 1.1     | 2026-10-23 | Ajout `metadata` sur `localite`, `ouvrage`, `cgpe`                                      |
| 1.2     | 2026-10-26 | Ajout vue liste + export Excel/CSV (25 endpoints)                                       |
| 2.0     | 2026-10-27 | Phase 1-2 terminées (infra + modèles + migration). Phase 3.1 terminée (schémas + auth). |
| 2.1     | 2026-10-27 | Phase 3 terminée (18 endpoints de lecture opérationnels, auth API key, fix UTF-8).      |
| 2.2     | 2026-10-28 | Phase 5 terminée (export Excel avec Synthèse KPI + CSV + colonne N°, 20 endpoints)      |
---

## 9. Prochaine action immédiate

**Phase 5 — Export Excel/CSV** (recommandée) ou **Phase 4 — Ingestion**.

### Phase 5 — Export (2-3 jours)

1. `backend/app/services/export.py` :
    - `export_ouvrages_xlsx(filters, columns, include_metadata)` → `StreamingResponse`
    - `export_ouvrages_csv(filters, columns, include_metadata)` → `StreamingResponse`
    - Streaming via `openpyxl` (mode `write_only`) + `yield_per(5000)` SQLAlchemy
    - Vérification de `MAX_EXPORT_ROWS` avant streaming (413 si dépassé)
2. `routers/ouvrages.py` : ajout des 2 endpoints
    - `GET /ouvrages/export`
    - `GET /ouvrages/export.csv`

**Critère de validation** : `curl -H "X-API-Key: ..." http://localhost:8000/v1/ouvrages/export -o test.xlsx` télécharge un fichier Excel valide (avec les 13 colonnes standard).

### Phase 4 — Ingestion (5-7 jours)

1. `backend/app/services/ingestion.py` :
    - Détection des feuilles (`openpyxl`)
    - Mapping des colonnes (normalisation)
    - Extraction des colonnes non mappées → `metadata`
    - Remplissage `donnees_brutes` (JSONB)
    - Gestion des modes `complet` / `echantillon` / `plage`
    - Mise à jour `statut_qualite`
2. `backend/app/services/rapprochement.py` :
    - Rapprochement localité (trigram + unaccent + alias)
3. `routers/fichiers.py` : ajout `POST /fichiers` (upload)
4. `routers/ingestion.py` : ajout `POST /fichiers/{id}/runs`, `GET /runs/{id}`, `GET /feuilles/{id}/lignes`, `GET /runs/{id}/lignes`, `GET /lignes/{id}`

**Critère de validation** : upload d'un fichier Excel de test → feuilles détectées → run lancé → lignes ingérées → points visibles sur la carte (via `/carto/fichiers/{id}/points`).

---

*Handoff rédigé le 2026-10-27. Toute modification du contrat d'API ou du schéma doit être répercutée dans les 5 livrables de conception (`mcdr.puml`, `mldr.md`, `mcd.puml`, `openapi.yaml`, `metadata_conventions.md`) avant implémentation.*

---

## Récapitulatif des modifications

| Section | Avant                        | Après                                    |
|---------|------------------------------|------------------------------------------|
| En-tête | v2.0                         | v2.1                                     |
| §2      | Phase 3.2/3.3 « à produire » | Phase 3 ✅ terminée                       |
| §3.2    | `routers/__init__.py` seul   | 5 routers complets                       |
| §3.4    | 12 décisions                 | 13 (ajout fix UTF-8)                     |
| §4.2    | 25 endpoints « à produire »  | 18 ✅, 5 ⏳ Phase 4, 2 ⏳ Phase 5           |
| §5.4    | « Générer un JWT »           | « Tester l'API lecture » (18 endpoints)  |
| §5.5    | —                            | Nouveau (JWT Phase 4+)                   |
| §6      | 10 pièges                    | 12 pièges (ajout encodage + operationId) |
| §7      | 9 dettes                     | 10 dettes (ajout `geom_centre`, `bbox`)  |
| §8      | v2.0                         | v2.1                                     |
| §9      | Phase 3.2                    | Phase 4 ou 5 (avec critères)             |

---

## Question

1. **Remplace `docs/HANDOFF.md`** par cette version.
2. **Commit** :
   ```powershell
   git add docs/HANDOFF.md
   git commit -m "docs: mise à jour handoff (Phase 3 terminée, v2.1)"
   git push origin main
   ```
3. **On enchaîne sur Phase 5 (Export) ou Phase 4 (Ingestion) ?**

Ma reco forte : **Phase 5 d'abord**. Tu auras une victoire rapide en 2-3 jours, testable avec les données seedées, avant d'attaquer le gros morceau qu'est l'ingestion.