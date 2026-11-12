
---

# 📦 Handoff complet — Projet DHR (v1.1, 2026-11-12)

Document de reprise mis à jour après la session de corrections Phase D. Il **complète** la Bible (`DHR.md`) et la Constitution (`CONSTITUTION.md`), qui font autorité.

---

## 1. État d'avancement

### 1.1 Ce qui est terminé (Phase C + Phase D partielle)

| Élément | Statut | Détail |
|---------|--------|--------|
| **Bible v1.0** (`DHR.md`) | ✅ | 8 sections, fait autorité |
| **Constitution v1.0** (`CONSTITUTION.md`) | ✅ | Contrat opérationnel |
| **Phase A — Bible** | ✅ | Sections 1 → 8 |
| **Phase B — Constitution** | ✅ | Document 2–3 pages |
| **Phase C — Socle DB** | ✅ | `schema.sql` + `0001_initial.py` + `models.py` alignés |
| **Backend démarre** | ✅ | `/health` OK, migrations passent |
| **Tests backend** | ✅ | **52 passed** (0 échec) |
| **B1** — `export.py` importe `TypeOuvrage` | ✅ | Corrigé |
| **B2–B4** — `models.py` (noms, CHECK, UNIQUE) | ✅ | Corrigés |
| **B5** — `ingestion.py` (rejets) | ✅ | Corrigé |
| **B6** — `consolidation.py` (3 règles manquantes) | ✅ | Corrigé |
| **I1–I4** — `ingestion.py` / `rapprochement.py` | ✅ | Corrigés |
| **B10** — `main.py` (RFC 7807 + lifespan) | ✅ | Appliqué, 52 tests passent |
| **A1–A4** — `carto.py` (vue `v_points_par_fichier`, `qualite_eau`, `bailleur` EXISTS, filtres métier) | ✅ | Appliqué |
| **C8** — `carto.py` (`Literal`) | ✅ | Appliqué |
| **B1** — `referentiels.py` (`geom_centre`) | ✅ | Appliqué |
| **B2** — `referentiels.py` (N+1 `list_ref_geo`) | ✅ | Appliqué (chargement groupé des parents) |
| **B3** — `referentiels.py` (N+1 `get_ref_geo_chemin`) | ✅ | Appliqué (CTE récursive) |
| **B9** — `deps.py` (`Literal` + `StatutQualite`) | ✅ | Appliqué |
| **carto.py (1,2,3,5,6)** — `WHERE` dynamique, `qualite_eau` cohérent, `source`/`date_ingestion` exposés, `StatutQualite` centralisé, `row._mapping` | ✅ | Appliqué |
| **Bug Pydantic `TypeAlimentation`** — `from __future__ import annotations` retiré de `deps.py` et `carto.py` | ✅ | **Résolu** (backend démarre) |

### 1.2 Ce qui reste à faire (Phase D)

| Élément | Statut | Détail |
|---------|--------|--------|
| **Audit `schemas/*`** | ⏳ | `schemas/ouvrages.py`, `fichiers.py`, `referentiels.py`, `common.py`, `qualite.py` (audit partiel fait, RAS bloquant) |
| **Audit `routers/*`** | ✅ | Fait (carto, fichiers, ingestion, ouvrages, qualite, referentiels) |
| **Audit `deps.py`** | ✅ | Fait (B9) |
| **Audit `main.py`** | ✅ | Fait (B10) |
| **B6** — `fichiers.py` (imports dupliqués en bas) | ⏳ | À corriger |
| **B4** — `ouvrages.py` (`RefGeoAdmin.__table__.alias` → `aliased()`) | ⏳ | À corriger |
| **C9** — `ingestion.py` (curseur opaque base64) | ⏳ | À corriger |
| **C3–C5** — `schemas/*` (docstrings, `FinancementResume.bailleur: str \| None`) | ⏳ | À corriger |
| **B7** — `fichiers.py` (unicité `entete_brut` dans `MappingValidation`) | ⏳ | À corriger |
| **F1–F9** — Frontend | ⏳ | À corriger |
| **O1–O5, OI1–OI2** — `openapi.yaml` | ⏳ | À aligner |
| **M1–M6** — `metadata_conventions.md` | ⏳ | À réécrire |
| **Script `tests-api.md`** | ⏳ | À exécuter (bout-en-bout) |
| **CI GitHub Actions** | ⏳ | À vérifier sur GitHub |

---

## 2. Architecture

### 2.1 Stack technique (inchangée)

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

### 2.2 Structure backend (inchangée)

```text
backend/
├── app/
│   ├── main.py              # ✅ RFC 7807 + lifespan
│   ├── config.py
│   ├── db.py
│   ├── auth.py
│   ├── deps.py              # ✅ Literal + StatutQualite (sans PEP 563)
│   ├── models.py            # ✅ 13 modèles alignés
│   ├── schemas/             # ⏳ Audit partiel
│   ├── routers/
│   │   ├── carto.py         # ✅ A1–A4 + C8 + (1,2,3,5,6) + StatutQualite
│   │   ├── fichiers.py      # ⏳ B6 (imports dupliqués), B7 (unicité)
│   │   ├── ingestion.py     # ⏳ C9 (curseur opaque)
│   │   ├── ouvrages.py      # ⏳ B4 (aliased)
│   │   ├── qualite.py       # ✅
│   │   └── referentiels.py  # ✅ B1, B2, B3
│   └── services/            # ✅ B1–B6, I1–I4 corrigés
├── alembic/versions/0001_initial.py
├── scripts/
├── tests/                   # ✅ 52 passed
├── sql/schema.sql           # ✅
└── Dockerfile
```

---

## 3. Corrections Phase D — Détail

### 3.1 `main.py` (B10)

- `exception_handler` pour `StarletteHTTPException` → Problem RFC 7807.
- `exception_handler` pour `RequestValidationError` → Problem + `errors: [{field, message}]`.
- `exception_handler` pour `Exception` → Problem 500 (filet de sécurité).
- `@app.on_event("startup")` → `lifespan` (async context manager).

**Mapping code HTTP → slug** (aligné Bible § 4.4) :
```
400 → bad-request, 401 → unauthorized, 403 → forbidden,
404 → not-found, 409 → conflict, 413 → payload-too-large,
422 → validation, 500 → internal
```

### 3.2 `deps.py` (B9 + bug Pydantic)

- `TypeAlimentation`, `NatureOuvrage`, `RealisationPar`, `EtatOuvrage`, `StatutQualite` définis comme `Literal`.
- `OuvrageFilters` utilise ces `Literal` (422 sur valeur invalide).
- **`from __future__ import annotations` retiré** (sinon Pydantic échoue à résoudre `TypeAlimentation`).

### 3.3 `carto.py` (A1–A4 + C8 + 1,2,3,5,6)

- Mode Fichier : lit `v_points_par_fichier` (feuilles `Localités` exclues).
- `properties` exposent le **brut** (`type_ouvrage_brut`, `etat_ouvrage_brut`, etc.).
- `qualite_eau` dans `properties` ET `details` (`or {}` partout).
- `source` et `date_ingestion` ajoutés aux `properties`.
- Filtre `bailleur` via `EXISTS` (pas de doublons).
- `nature_ouvrage`/`realisation_par` **retirés** du mode Fichier (A4).
- `type_alimentation` : regex `\m...\M` (évite `HV` ⊂ `HVA`).
- `_VUE_FICHIER_SELECT` sans `WHERE` (ajouté dynamiquement).
- `StatutQualite` importé depuis `deps.py`.
- **`from __future__ import annotations` retiré**.

### 3.4 `referentiels.py` (B1, B2, B3)

- `get_localite` : `geom_centre` construit depuis `lat`/`lon` (ordre `[lon, lat]`).
- `list_ref_geo` : chargement groupé des parents (plus de N+1).
- `get_ref_geo_chemin` : CTE récursive (1 requête au lieu de N).
- `list_localites` : `unaccent` pour recherche insensible aux accents.

---

## 4. Écarts restants (à corriger en Phase D)

### 4.1 Backend

| # | Écart | Fichier | Correction |
|---|-------|---------|-----------|
| **B6** | Imports dupliqués en bas de fichier | `fichiers.py` | Supprimer le bloc du bas |
| **B7** | Pas d'unicité `entete_brut` dans `MappingValidation.colonnes` | `fichiers.py` + `schemas/fichiers.py` | `field_validator` |
| **B4** | `RefGeoAdmin.__table__.alias(...)` au lieu de `aliased()` | `ouvrages.py` | Harmoniser sur `aliased()` |
| **C9** | Curseur `int` en clair au lieu de base64 | `ingestion.py` | Base64 (comme `ouvrages.py`) |
| **C3** | Commentaire confus sur `type_ouvrage_inconnu` | `schemas/ouvrages.py` | Reformuler |
| **C4** | `FinancementResume.bailleur: str` (magic `"?"`) | `schemas/ouvrages.py` | `str \| None` |
| **C5** | Pas de `Field(description=...)` sur `metadata`/`qualite_eau` | `schemas/ouvrages.py` | Ajouter |
| **C10** | `get_ligne` sans `response_model` | `ingestion.py` | `LigneIngereeSchema \| LigneIngereeAvecBrut` |
| **`RunPlage`** | Pas de validation `ligne_fin >= ligne_debut` | `schemas/ingestion.py` | `model_validator` |
| **`type_ouvrage_brut`** | Filtre absent du mode Fichier | `carto.py` | Ajouter (à trancher avec frontend) |

### 4.2 Frontend (F1–F9)

| # | Écart | Fichier | Correction |
|---|-------|---------|-----------|
| **F1** | `CHAMPS_STANDARDS` sans `usage_ouvrage_brut` | `Mapping.tsx` | Ajouter |
| **F2** | Forme = nature approximée par `dashArray` | `MapView.tsx` | Vraies formes (cercle/carré/losange) |
| **F3** | `window.open` pour l'export | `Liste.tsx` | `fetch` + `blob` |
| **F4** | `OLD_Carte.tsx` traîne | `pages/` | Supprimer |
| **F5** | Pas de redirection 401 | `api.ts` | Ajouter |
| **F6** | Textes « Chargement... » | Toutes les pages | `Skeleton` |
| **F7** | `Liste.tsx` et `Qualite.tsx` stubs | `pages/` | Implémenter |
| **F8** | Pas de page détail fichier | — | V2 (accepté) |
| **F9** | Pas de bouton « Supprimer le JWT » | `Parametres.tsx` | Ajouter |

### 4.3 Documentation

| # | Écart | Fichier | Correction |
|---|-------|---------|-----------|
| **O1–O5, OI1–OI2** | `openapi.yaml` non aligné | `openapi.yaml` | Régénérer |
| **M1–M6** | `metadata_conventions.md` obsolète | `metadata_conventions.md` | Réécrire |

---

## 5. Commandes de reprise

### 5.1 Démarrage

```powershell
# Démarrer
docker compose up -d --build

# Logs
docker compose logs -f backend

# Vérifier que le backend démarre sans traceback
docker compose logs --tail=30 backend
```

### 5.2 Tests

```powershell
# Backend (52 attendus)
docker compose exec -T backend pytest -q

# Avec couverture
docker compose exec -T backend pytest --cov=app --cov-report=term-missing

# Lint
docker compose exec -T backend ruff check app
docker compose exec -T backend mypy app/services app/models
```

### 5.3 Reset complet (si besoin)

```powershell
# DB
docker compose exec -T db psql -U dhr -d dhr -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose exec -T backend alembic upgrade head

# Uploads
docker compose exec -T backend rm -rf /app/uploads/*

# Réimporter les localités
docker compose exec -T backend python -u /app/scripts/import_localites.py /app/tests/fixtures/fichier1.xlsx
```

### 5.4 Script de test API bout-en-bout

Le script `tests-api.md` (à la racine) couvre :
- Import localités (CLI)
- Upload fichier
- Mapping (proposition + validation)
- Ingestion (run complet + polling)
- Rapprochement (vérification via lignes)
- Consolidation (vérification via ouvrages)
- Carto (mode Tous + mode Fichier + GeoJSON)
- Qualité (dashboard + cohérence des compteurs)
- Export Excel (avec/sans Synthèse, avec/sans metadata, filtres)
- Export CSV
- Erreurs RFC 7807 (401, 404, 422)

**À exécuter** après le push, section par section.

---

## 6. Décisions actées (rappel)

### 6.1 Les 10 décisions de la Bible (§ 1.4)

1. Un ouvrage sans GPS n'existe pas.
2. Localités importées manuellement (CLI).
3. 3 champs sémantiques : `nature_ouvrage`, `type_alimentation`, `realisation_par`.
4. Attributs non mappés → JSONB (`brut_<entête>` + `metadata.<entité>.<clé>`).
5. Données sanitaires → `qualite_eau` (JSONB, nullable).
6. Pas de filtre `district` (KPI dans l'export Excel uniquement).
7. Mapping proposé auto, corrigeable via UI.
8. Repartir sur des bases saines (migration initiale unique).
9. 6 statuts de qualité implémentés.
10. Métadonnées explicites via `metadata.<entité>.<clé>`.

### 6.2 Décisions de la session

| Date | Décision |
|------|----------|
| 2026-11-12 | **B3 corrigé** (CTE récursive pour `get_ref_geo_chemin`) |
| 2026-11-12 | **B9 corrigé** (`Literal` dans `deps.py`) |
| 2026-11-12 | **Bug Pydantic `TypeAlimentation`** : `from __future__ import annotations` retiré de `deps.py` et `carto.py` (Pydantic 2 + PEP 563 incompatible avec `Literal` importé) |
| 2026-11-12 | **carto.py** : `WHERE` dynamique, `qualite_eau` `or {}`, `source`/`date_ingestion` exposés, `StatutQualite` centralisé, `row._mapping` |
| 2026-11-12 | Backend démarre à nouveau, 52 tests passent |

---

## 7. Points ouverts (V2)

| Sujet | Raison |
|-------|--------|
| Déploiement production | MVP local Docker |
| Monitoring (Prometheus, Grafana) | V2 |
| Logging centralisé (ELK, Loki) | V2 |
| Authentification complète (login, OAuth) | JWT manuel au MVP |
| Gestion utilisateurs (rôles) | V2 |
| CI/CD avancé (staging, prod, rollback) | V2 |
| Tests de charge (Locust, k6) | V2 |
| Documentation utilisateur (guide DHR) | V2 |
| Internationalisation (i18n) | V2 |
| Filtre `type_ouvrage_brut` en mode Fichier | À trancher avec frontend |
| Promotion des clés `metadata` en attributs de première classe (`attribut_definition` + `ouvrage_attribut`) | V2 |
| `Localite.geom_centre` exposé en liste | V2 |
| Alias localités non alimentés | V2 |
| CGPE non créés | V2 |
| Projets de financement non créés | V2 |

---

## 8. Commandes de reprise (pour la prochaine session)

> « Je reprends le projet DHR. Voici le handoff (`HANDOFF.md`), la Bible (`DHR.md`) et la Constitution (`CONSTITUTION.md`). La Phase C (socle DB) est terminée. La Phase D (services + routers) est bien avancée : `main.py`, `deps.py`, `carto.py`, `referentiels.py` sont corrigés, le backend démarre, 52 tests passent.
>
> **Il reste à faire** :
> 1. **B6** — `fichiers.py` (imports dupliqués en bas)
> 2. **B7** — `fichiers.py` + `schemas/fichiers.py` (unicité `entete_brut`)
> 3. **B4** — `ouvrages.py` (`aliased()` au lieu de `__table__.alias()`)
> 4. **C9** — `ingestion.py` (curseur opaque base64)
> 5. **C3–C5, C10** — `schemas/*` (docstrings, `bailleur: str | None`, `response_model`)
> 6. **`RunPlage`** — validation `ligne_fin >= ligne_debut`
> 7. **F1–F9** — Frontend
> 8. **O1–O5, OI1–OI2** — `openapi.yaml`
> 9. **M1–M6** — `metadata_conventions.md`
> 10. **`tests-api.md`** — exécuter le script bout-en-bout
> 11. **CI GitHub Actions** — vérifier
>
> On commence par **B6 + B7** (les deux dans `fichiers.py`). »

---

## 9. Annexe — Fichiers modifiés dans cette session

| Fichier | Changement |
|---------|-----------|
| `app/main.py` | RFC 7807 + lifespan |
| `app/deps.py` | `Literal` + `StatutQualite` + sans PEP 563 |
| `app/routers/carto.py` | A1–A4 + C8 + (1,2,3,5,6) + sans PEP 563 |
| `app/routers/referentiels.py` | B1, B2, B3 |
| `tests-api.md` | **Nouveau** — script bout-en-bout |

**Fichiers non modifiés mais vérifiés** : `app/routers/ouvrages.py`, `app/routers/qualite.py`, `app/routers/fichiers.py`, `app/routers/ingestion.py`, `app/schemas/*`, `app/models.py`, `sql/schema.sql`.

---

**Fin du handoff v1.1.** Ce document capture l'état du projet au **2026-11-12**. Pour reprendre, lire ce handoff, puis la Bible (`DHR.md`) et la Constitution (`CONSTITUTION.md`). En cas de conflit, **la Bible fait autorité**.

---
