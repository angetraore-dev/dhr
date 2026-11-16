
---

# HANDOFF TECHNIQUE — Projet DHR (v1.2)

**Date** : 16 novembre 2026
**Statut global** : Backend 100 % validé (54/54 tests, Ruff OK). Frontend en cours de validation (pages : Fichiers, Mapping, Carte, Liste, Qualité, Paramètres). Corrections d'écarts en cours.

---

## 1. Architecture & Modèle Métier

### 1.1 Stack

| Couche | Technologie | Version |
|--------|-------------|---------|
| Base | PostgreSQL + PostGIS | 16 + 3.4 |
| Backend | Python + FastAPI | 3.12 + 0.115 |
| ORM | SQLAlchemy + GeoAlchemy2 | 2.0 + 0.16 |
| Validation | Pydantic | 2.9 |
| Migrations | Alembic | 1.13 |
| Excel | openpyxl + XlsxWriter | 3.1 + 3.2 |
| Frontend | React + Vite + TS | 18 + 5.4 |
| UI | Tailwind + shadcn/ui | 3.4 |
| Carto | Leaflet + Esri | 1.9 |
| État API | TanStack Query | 5.59 |

### 1.2 Modèle métier (ADR-014)

- **3 champs sémantiques** sur `ouvrage` :
    - `nature_ouvrage` : `puits` | `forage` | `inconnu`
    - `type_alimentation` : `PMH` | `HVA` | `PEA` | `HV` | `AUTRE`
    - `realisation_par` : `public` | `prive` | `inconnu`
- **Pas de `type_ouvrage`** legacy.
- **Pas de `district`** (sauf KPI export).
- `metadata` (JSONB) + `qualite_eau` (JSONB, nullable).

---

## 2. Backend — État validé

### 2.1 Tests & lint

- **54/54 tests `pytest`** passent.
- **`ruff check`** : 0 erreur.

### 2.2 Services

| Service | Statut |
|---------|--------|
| `upload.py` | ✅ SHA-256, détection feuilles, 409 sur doublon |
| `mapping.py` | ✅ Proposition auto + validation |
| `ingestion.py` | ✅ Rejets détectés, `nb_lignes_total = stockées + rejetées` |
| `rapprochement.py` | ✅ Exact > alias > trigram, `message_qualite` strict |
| `consolidation.py` | ✅ Dédoublonnage 3 niveaux (code, tuple, GPS ≤ 20 m), `qualite_eau` |
| `export.py` | ✅ CTE récursive ORM, KPI `par_district` |
| `import_localites.py` | ✅ Détection auto feuille + en-tête |

### 2.3 Données en base (exemple)

- **679 nouvelles localités** + **628 existantes** (0 erreur).
- **`Forage.xlsx`** : 1306 lignes (1 rejetée), 1306 rapprochées (0 non résolue).
- **1070 ouvrages** consolidés.

### 2.4 Corrections backend appliquées (Phase D)

| # | Écart | Fichier | Statut |
|---|-------|---------|--------|
| B1 | `export.py` importe `TypeOuvrage` | `export.py` | ✅ |
| B2–B4 | `models.py` (noms, CHECK, UNIQUE) | `models.py` | ✅ |
| B5 | `ingestion.py` (rejets) | `ingestion.py` | ✅ |
| B6 | `consolidation.py` (3 règles) | `consolidation.py` | ✅ |
| I1–I4 | `ingestion.py` / `rapprochement.py` | — | ✅ |
| B10 | RFC 7807 + lifespan | `main.py` | ✅ |
| A1–A4 | `carto.py` (vue, `qualite_eau`, `bailleur` EXISTS, filtres) | `carto.py` | ✅ |
| C8 | `carto.py` (`Literal`) | `carto.py` | ✅ |
| B1–B3 | `referentiels.py` (`geom_centre`, N+1, CTE) | `referentiels.py` | ✅ |
| B9 | `deps.py` (`Literal` + `StatutQualite`) | `deps.py` | ✅ |
| B6 | `fichiers.py` (imports dupliqués) | `fichiers.py` | ✅ |
| B7 | `MappingValidation` unicité `entete_brut` | `schemas/fichiers.py` | ✅ |
| Bug Pydantic | `from __future__ import annotations` retiré de `deps.py`, `carto.py`, `fichiers.py` | — | ✅ |

---

## 3. Frontend — État en cours

### 3.1 Fichiers validés

| Fichier | Statut | Détail |
|---------|--------|--------|
| `src/lib/api.ts` | ✅ | Types complets, `exportOuvrages` (fetch+blob), 401 redirect, `toQuery`, `parseProblem` |
| `vite.config.ts` | ✅ | Proxy `/api` → `backend:8000/v1` |
| `src/lib/filters.ts` | ✅ | `Filters` + `EMPTY_FILTERS` centralisés |
| `src/components/FiltersPanel.tsx` | ✅ | Cascade géo, reset, debounce, `EMPTY_FILTERS` importé |
| `src/pages/Liste.tsx` | ✅ | Tableau, export, modale détail, `FiltersPanel` importé |
| `src/pages/Carte.tsx` | ⚠️ | Corrigé (imports), **reste : sélecteur `id_run` + palette par qualité en mode Fichier** |
| `src/components/MapView.tsx` | ⚠️ | Formes (carré/losange), `qualite_eau` popup, **reste : palette conditionnelle `mode`** |
| `src/pages/Qualite.tsx` | ⚠️ | Corrigé, **reste : `message_qualite` (backend) + skeletons** |

### 3.2 Fichiers à valider

| Fichier | Statut |
|---------|--------|
| `src/pages/Fichiers.tsx` | ⏳ |
| `src/pages/Mapping.tsx` | ⏳ |
| `src/components/UploadDialog.tsx` | ⏳ |
| `src/components/RunStatus.tsx` | ⏳ |
| `src/pages/Parametres.tsx` | ⏳ |
| `src/App.tsx` | ⏳ |

### 3.3 Écarts frontend identifiés

| # | Écart | Fichier | Priorité |
|---|-------|---------|----------|
| F2a | Formes (carré/losange) | `MapView.tsx` | ✅ fait |
| F2b | `qualite_eau` popup | `MapView.tsx` | ✅ fait |
| F2c | Palette conditionnelle (qualité en mode Fichier) | `MapView.tsx` + `Carte.tsx` | ⏳ |
| F3 | Export `fetch` + `blob` | `api.ts` | ✅ fait |
| F5 | 401 → redirect `/parametres` | `api.ts` | ✅ fait |
| F6 | Skeletons | Toutes les pages | ⏳ |
| **Nouveau** | Sélecteur `id_run` en mode Fichier | `Carte.tsx` | ⏳ |

---

## 4. Décisions actées dans cette session

### 4.1 Décisions frontend

| # | Décision | Justification |
|---|----------|---------------|
| D1 | `Filters` + `EMPTY_FILTERS` dans `src/lib/filters.ts` | Évite duplication, warning HMR |
| D2 | Sélecteur `id_run` dans `Carte.tsx` (mode Fichier) | Résout le problème des 3098 points ; respecte la Bible (G5, G8) |
| D3 | Palette par `statut_qualite` en mode Fichier (à implémenter) | Cohérent avec la sémantique (brut = qualité) |
| D4 | Pas de dédoublonnage à l'ingestion | Contredit la Bible (G5, G8) ; préférer le diff entre runs (V2) |
| D5 | Lignes `rejete` non stockées | Conforme à la Bible § 3.1.6 ; V2 pour les stocker |

### 4.2 Décisions backend (rappel)

| # | Décision | Référence |
|---|----------|-----------|
| D6 | `message_qualite` à ajouter dans `LigneIngeree` (schéma) | Nécessaire pour `Qualite.tsx` |
| D7 | 6 statuts de qualité | Bible § 3.1.6 |
| D8 | Dédoublonnage 3 niveaux | Bible § 3.2.3 |

---

## 5. Prochaines étapes (par ordre)

### 5.1 Immédiat (frontend)

1. **`Carte.tsx`** : sélecteur `id_run` en mode Fichier (D2).
2. **`MapView.tsx`** : palette conditionnelle `mode` (D3).
3. **`Qualite.tsx`** : vérifier l'affichage de `message_qualite` (D6).
4. **`Fichiers.tsx`**, **`Mapping.tsx`**, **`UploadDialog.tsx`**, **`RunStatus.tsx`**, **`Parametres.tsx`**, **`App.tsx`** : audit + correction.

### 5.2 Court terme (backend)

5. **`schemas/ingestion.py`** : ajouter `message_qualite: str | None` à `LigneIngeree`.

### 5.3 V2 (documenté)

6. **Stocker les lignes `rejete`** (Bible § 3.1.6, exception V2).
7. **Endpoint `/runs/{id}/diff/{id_autre}`** (comparer deux runs).
8. **UI de gestion des versions** (Bible § 2.3.5, G5).

---

## 6. Commandes utiles

```powershell
# Backend
docker compose exec -T backend pytest -q
docker compose exec -T backend ruff check app

# Frontend
cd frontend
npm run typecheck
npm run build

# Logs
docker compose logs -f backend
docker compose logs -f frontend

# URLs
# Frontend : http://localhost:5173
# Backend  : http://localhost:8000/docs
# API key  : dhr_dev_read_key_change_me
```

---

## 7. Points d'attention

### 7.1 Mode Fichier — 3098 points

**Cause** : 3 runs × 1306 lignes = 3918 (ou 3098 si certains runs ont moins de lignes). La vue `v_points_par_fichier` retourne toutes les lignes.

**Solution** : sélecteur `id_run` dans `Carte.tsx` (D2). **Pas de modification backend nécessaire** (`carto.py` accepte déjà `?id_run=X`).

### 7.2 Points gris en mode Fichier

**Cause** : `type_alimentation` n'existe pas en mode Fichier (brut, pas consolidé).

**Solution** : palette par `statut_qualite` (D3).

### 7.3 Lignes rejetées

**Comportement** : non stockées (Bible § 3.1.6). Comptées dans `nb_rejetes`. Affichées dans la carte « Lignes rejetées » de `Qualite.tsx`, mais pas dans le tableau de détail.

**V2** : stocker pour correction manuelle.

### 7.4 `message_qualite`

**Comportement** : absent du schéma Pydantic `LigneIngeree`. Le frontend reçoit `undefined`.

**Solution** : ajouter `message_qualite: str | None` dans `schemas/ingestion.py` (D6).

---

## 8. Documents de référence

| Document | Rôle | Statut |
|----------|------|--------|
| `DHR.md` | Bible (fait autorité) | ✅ v1.0 |
| `CONSTITUTION.md` | Contrat opérationnel | ✅ v1.0 |
| `openapi.yaml` | Contrat API | ✅ v1.3.0 |
| `metadata_conventions.md` | Conventions metadata | ⏳ À réécrire (M1–M6) |
| `HANDOFF.md` | Ce document | ✅ v1.2 |

---

## 9. Commandes de reprise

> « Je reprends le projet DHR. Backend 100 % validé (54 tests, Ruff OK). Frontend en cours de validation.
>
> **Fichiers validés** : `api.ts`, `vite.config.ts`, `lib/filters.ts`, `FiltersPanel.tsx`, `Liste.tsx`.
>
> **Fichiers à corriger** :
> - `Carte.tsx` : ajouter sélecteur `id_run` (mode Fichier).
> - `MapView.tsx` : palette conditionnelle (qualité en mode Fichier).
> - `Qualite.tsx` : vérifier `message_qualite`.
> - `Fichiers.tsx`, `Mapping.tsx`, `UploadDialog.tsx`, `RunStatus.tsx`, `Parametres.tsx`, `App.tsx` : audit.
>
> **Backend à corriger** : ajouter `message_qualite` dans `schemas/ingestion.py`.
>
> On commence par `Carte.tsx` (sélecteur `id_run`). »

---

## 10. Annexe — Fichiers modifiés dans cette session

| Fichier | Changement |
|---------|-----------|
| `frontend/src/lib/api.ts` | Réécrit (types, `toQuery`, `parseProblem`, 401, `exportOuvrages`) |
| `frontend/src/lib/filters.ts` | **Nouveau** (`Filters`, `EMPTY_FILTERS`) |
| `frontend/src/components/FiltersPanel.tsx` | Imports corrigés, reset, cascade |
| `frontend/src/pages/Liste.tsx` | Imports corrigés |
| `frontend/src/pages/Carte.tsx` | Imports corrigés, filtres mode Fichier |
| `frontend/src/components/MapView.tsx` | Formes, `qualite_eau` popup |
| `frontend/src/pages/Qualite.tsx` | Réécrit (JSX corrigé) |
| `backend/app/services/export.py` | Réindenté |
| `backend/app/main.py` | RFC 7807 + lifespan |
| `backend/app/deps.py` | `Literal` + `StatutQualite` + sans PEP 563 |
| `backend/app/routers/carto.py` | A1–A4, C8, (1,2,3,5,6), sans PEP 563 |
| `backend/app/routers/referentiels.py` | B1, B2, B3 |
| `backend/app/routers/fichiers.py` | B6, sans PEP 563 |
| `backend/app/schemas/fichiers.py` | B7 (`MappingValidation`) |
| `openapi.yaml` | v1.3.0 (indentation, préfixes, schémas) |

---

**Fin du handoff v1.2.** Ce document capture l'état au **16 novembre 2026**. En cas de conflit, **la Bible fait autorité**.

---


