
---

# Constitution du projet DHR

**Version** : 1.0
**Date** : 2026-11-10
**Objet** : Contrat opérationnel de l'équipe DHR. Complète la Bible (`DHR.md`), qui fait autorité en cas de conflit.
**Portée** : tout contributeur (dev, reviewer, PO). S'applique à chaque PR, chaque commit, chaque décision.

---

## 1. Objet et portée

La **Constitution** est le **contrat opérationnel** de l'équipe DHR. Elle fixe les règles que tout contributeur doit respecter, et renvoie systématiquement à la **Bible** (`DHR.md`) pour les détails.

- La **Bible** fait autorité. En cas de conflit entre le code et la Bible, c'est le code qui est corrigé, pas la Bible (Bible, § 2.1.6).
- La Constitution **ne duplique pas** la Bible. Elle la synthétise et y renvoie.
- La Constitution est **courte** (2–3 pages) : un dev peut la lire en 5 minutes avant de coder.
- La Constitution est **stable** : elle ne change pas à chaque sprint. Seules les règles d'or et les renvois changent, et rarement.

---

## 2. Règles d'or

**10 règles non négociables.** Chacune renvoie à la section de la Bible qui la détaille.

| #  | Règle                                                                                                                                              | Renvoi Bible                            |
|----|----------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------|
| 1  | **La Bible fait autorité.** En cas de conflit entre le code et la Bible, c'est le code qui est corrigé, pas la Bible.                              | § 2.1.6                                 |
| 2  | **Un ouvrage sans GPS n'existe pas.** Il est marqué `statut_qualite = 'geom_invalide'` et n'est pas consolidé.                                     | § 1.4 décision 1                        |
| 3  | **Le brut ne se mélange jamais avec le métier.** `ligne_ingeree` (brut) → `ouvrage` (consolidé). Chaque étape est rejouable.                       | § 2.1.2 (P1), § 3.1.1                   |
| 4  | **Tout ce qui n'est pas mappé va en JSONB**, pas en colonne. Convention `brut_<entête>` + `metadata.<entité>.<clé>` pour les attributs explicites. | § 2.1.2 (P2), § 2.3.4, ADR-002, ADR-013 |
| 5  | **Les 6 statuts de qualité sont implémentés au MVP**, avec leurs règles précises.                                                                  | § 3.1.6, ADR-015                        |
| 6  | **Le pipeline est rejouable** : import localités → ingestion → rapprochement → consolidation. Aucune étape ne dépend d'un état non traçable.       | § 2.3.5 (G1), § 3.1.1                   |
| 7  | **Pas de `type_ouvrage` legacy.** 3 colonnes distinctes : `nature_ouvrage`, `type_alimentation`, `realisation_par`.                                | § 1.4 décision 3, ADR-014               |
| 8  | **Pas de filtre `district`** dans l'UI. Le filtre géo se fait par région → département → sous-préfecture → localité.                               | § 1.4 décision 6, ADR-017               |
| 9  | **Toute PR met à jour la Bible** si elle change le schéma, l'API, un composant ou une décision.                                                    | § 8.5.3                                 |
| 10 | **Pas de merge sans CI verte**, pas de PR sans description, pas de `TODO` non référencé en section 7.                                              | § 8.5, § 7                              |

---

## 3. Conventions de code

**Renvoi** : Bible, § 8.1 (détail complet).

### 3.1 Python (backend)

- **Version** : Python 3.12.
- **Lint + format** : `ruff` (ligne max 100, imports triés).
- **Types** : `mypy --strict` **obligatoire** sur `app/services/` et `app/models/`. `from __future__ import annotations` en tête de chaque fichier.
- **Docstrings** : style Google, obligatoires sur les fonctions publiques.
- **Nommage** : `snake_case` (variables, fonctions, modules), `PascalCase` (classes), `UPPER_SNAKE_CASE` (constantes), `_préfixe` (privé).
- **Interdits** : `print()` en production (utiliser `logging`), `except:` nu, mutable default argument, `Any` non justifié.

### 3.2 SQL

- **Style** : `snake_case`, mots-clés SQL en **MAJUSCULES**.
- **Nommage** : voir Bible § 2.3.4 (tables au singulier, `idx_<table>_<colonne>`, `<table>_<colonne>_check`, etc.).
- **Interdits** : `SELECT *` en production, requêtes dans les routers, f-string SQL (utiliser des requêtes paramétrées).
- **Migrations Alembic** : SQL brut dans `op.execute()` pour les triggers, fonctions, index GIN/GIST.

### 3.3 TypeScript (frontend)

- **Style** : `eslint` + `prettier` (ligne max 100).
- **Types** : `strict: true` dans `tsconfig.json`. Pas de `any` implicite.
- **Nommage** : `camelCase` (variables, fonctions, props), `PascalCase` (composants, types, interfaces), `UPPER_SNAKE_CASE` (constantes globales).
- **Composants** : fonctionnels uniquement. Hooks en haut du composant.
- **Interdits** : `console.log` en production, `any` non justifié.

### 3.4 JSON / JSONB

- **Clés** : `snake_case` (`brut_<entête>`, `profondeur_forage_m`).
- **Valeurs** : typées (nombre, booléen, string ISO 8601 pour les dates).
- **Pas de `null`** : si la valeur est absente, la clé n'est pas écrite.
- **Pas de clé générique** (`valeur1`, `champ2`).

### 3.5 Git

- **Branches** : `main` (protégée), `feat/<sujet>`, `fix/<sujet>`, `docs/<sujet>`, `refactor/<sujet>`, `chore/<sujet>`.
- **Commits** : conventionnels (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`). Impératif, en français, max 72 caractères sur la première ligne.
- **Merge** : `--no-ff` (préserver l'historique des branches). Pas de squash au MVP.

---

## 4. Architecture

**Renvoi** : Bible, § 8.2 (détail complet).

### 4.1 Backend (FastAPI)

```text
routers/   → fins, validation Pydantic, appellent les services
services/  → logique métier, reçoivent une Session SQLAlchemy
models/    → ORM SQLAlchemy (miroir de la Bible)
schemas/   → Pydantic (request/response)
db.py      → engine, session, Base
```

**Règles** :
- **Pas de logique métier dans les routers.** Pas d'accès DB direct dans les routers.
- **Services testables sans HTTP.** Ils reçoivent une `Session`, pas une `Request`.
- **Models = miroir exact de la Bible.** Pas de logique métier dans les modèles (sauf propriétés calculées triviales).
- **Schemas distincts des modèles.** Ne jamais exposer directement un modèle ORM.

### 4.2 Frontend (React)

```text
pages/       → composition, state local, appels API
components/  → réutilisables, sans dépendance à une page
lib/         → client HTTP, types, helpers
```

**Règles** :
- **Pas de state management global** (pas de Redux, pas de Zustand). TanStack Query + `useState` suffisent.
- **Pas de dépendance à une page spécifique** dans `components/`.
- **`lib/api.ts`** est la seule porte d'entrée vers le backend.

---

## 5. Qualité

**Renvoi** : Bible, § 8.3 (tests) et § 8.4 (CI).

### 5.1 Tests

- **Backend** : `pytest` + `pytest-postgresql` (base éphémère) + `httpx`. Couverture **≥ 70 %** sur `services/` et `models/`.
- **Frontend** : `vitest` + `@testing-library/react`. Couverture **≥ 50 %** sur `components/` et `lib/`.
- **Test d'intégration pipeline complet** (upload → run → vérifications) **obligatoire**.

### 5.2 CI (GitHub Actions)

Sur chaque PR et push sur `main` :
- **Backend** : `ruff check .`, `ruff format --check .`, `mypy app/services app/models`, `pytest --cov-fail-under=70`, `alembic upgrade head` + `downgrade base` + `upgrade head`.
- **Frontend** : `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build`.

**Aucune PR ne peut être mergée si la CI est rouge.**

### 5.3 Interdits

- Pas de `--no-verify` sur les commits.
- Pas de secrets en clair dans le repo (utiliser `.env` en local, GitHub Secrets en prod).
- Pas de code non testé mergé.

---

## 6. Workflow

**Renvoi** : Bible, § 8.5 (détail complet).

### 6.1 Cycle d'une contribution

1. **Créer une branche** depuis `main` : `git checkout -b feat/mon-sujet`.
2. **Développer** (code + tests).
3. **Vérifier localement** : `ruff`, `mypy`, `pytest` (backend) ; `eslint`, `tsc`, `vitest`, `build` (frontend).
4. **Committer** avec un message conventionnel.
5. **Pousser** et **ouvrir une PR** avec description (quoi, pourquoi, comment tester).
6. **Attendre la CI verte.**
7. **Revue** (même en solo : relire sa PR à froid, 24h après).
8. **Merge** : `--no-ff` dans `main`.
9. **Supprimer la branche** (locale et distante).

### 6.2 Règles de PR

- **1 PR = 1 sujet.** Pas de mélange (feature + refactoring dans la même PR = refusé).
- **Description obligatoire** : quoi, pourquoi, comment tester, checklist.
- **Taille raisonnable** : < 500 lignes de diff idéalement. Si plus gros, découper.
- **Revue** : commenter les points bloquants (`blocking:`) ou non bloquants (`nit:`).

### 6.3 Mise à jour de la Bible

Toute PR qui change :
- **le schéma** (table, colonne, contrainte, index) → met à jour la section 2.
- **un endpoint** → met à jour la section 4 et l'`openapi.yaml`.
- **un composant ou une page** → met à jour la section 5.
- **une décision d'architecture** → ajoute une ADR (section 6).
- **un écart** → met à jour la section 7 (retirer la ligne de dette).

**La Bible est mise à jour dans la même PR que le code**, pas dans une PR séparée.

---

## 7. Phases

**Renvoi** : Bible, § 8.6 (détail complet).

| Phase | Objectif                         | Livrable                                               | Statut     |
|-------|----------------------------------|--------------------------------------------------------|------------|
| **A** | Finaliser la Bible               | `DHR.md` v1.0 (sections 1–8)                           | ✅ Terminée |
| **B** | Constitution du projet           | `CONSTITUTION.md` v1.0                                 | ✅ Terminée |
| **C** | Socle DB                         | `schema.sql` + `0001_initial.py` + `models.py` alignés | À faire    |
| **D** | Services + frontend + tests + CI | Code aligné, CI verte                                  | À faire    |

**Definition of Done** de chaque phase : voir Bible § 8.6. Une phase n'est **pas terminée** tant que sa DoD n'est pas satisfaite.

---

## 8. En cas de doute

1. **Consulter la Bible** (section concernée).
2. **Si la Bible ne tranche pas** : ouvrir une issue, discuter, puis **mettre à jour la Bible** avant de coder.
3. **La Bible est un document vivant** : elle évolue avec le projet, mais toujours **par ajout ou remplacement explicite**, jamais par modification silencieuse.

**Règle finale** : en cas de conflit entre ce document et la Bible, **c'est la Bible qui gagne**. La Constitution est un **raccourci**, pas une **source de vérité**.

---
