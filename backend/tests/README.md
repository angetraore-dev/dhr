
---

# Tests backend — DHR

Documentation des tests backend (`backend/tests/`).

**Framework** : `pytest` + `pytest-cov`
**Base de test** : PostgreSQL + PostGIS (`dhr_test`)
**Couverture cible** : ≥ 70 % sur `app/services/` et `app/models/`

---

## Table des matières

1. [Structure des tests](#1-structure-des-tests)
2. [Prérequis](#2-prérequis)
3. [Configuration de la base de test](#3-configuration-de-la-base-de-test)
4. [Lancer les tests](#4-lancer-les-tests)
5. [Lancer un test spécifique](#5-lancer-un-test-spécifique)
6. [Couverture de code](#6-couverture-de-code)
7. [Tests d'intégration](#7-tests-dintégration)
8. [CI GitHub Actions](#8-ci-github-actions)
9. [Dépannage](#9-dépannage)
10. [Conventions](#10-conventions)

---

## 1. Structure des tests

```text
backend/tests/
├── README.md                       # Ce fichier
├── conftest.py                     # Fixtures pytest (base, session, client, données)
├── fixtures/
│   └── __init__.py                 # Package vide
├── test_coordonnees.py             # Tests parser_coordonnees (DMS, virgule, inversion)
├── test_ingestion.py               # Tests ingestion (rejets, vides, I1, I2, P12)
├── test_rapprochement.py           # Tests rapprochement (exact, non résolu, I3)
├── test_consolidation.py           # Tests consolidation (B6.1, B6.2, B6.3, _map_*)
└── test_integration_pipeline.py    # Test pipeline complet (intégration)
```

---

## 2. Prérequis

- Docker Compose en état de marche (`docker compose ps` → `db` et `backend` `running`).
- Base `dhr` accessible (celle utilisée par l'application).
- Base `dhr_test` accessible (celle utilisée par les tests, séparée).
- Le fichier `backend/pyproject.toml` contient les dépendances de test (`pytest`, `pytest-cov`, etc.).

**Vérification** :

```bash
docker compose exec backend pytest --version
# Attendu : pytest 8.3.x

docker compose exec backend python -c "import pytest_cov; print('OK')"
# Attendu : OK
```

---

## 3. Configuration de la base de test

Les tests utilisent une base **séparée** (`dhr_test`) pour ne pas polluer la base de dev (`dhr`).

### 3.1 Créer la base `dhr_test`

```bash
docker compose exec db psql -U dhr -d dhr -c "CREATE DATABASE dhr_test;"
```

**Vérification** :

```bash
docker compose exec db psql -U dhr -d dhr -c "\l" | grep dhr_test
# Attendu : dhr_test | dhr | UTF8 | ...
```

### 3.2 Variables d'environnement

Le `conftest.py` lit `TEST_DATABASE_URL`. Deux options :

**Option A** — Ajouter au `.env` (à la racine du projet) :

```bash
TEST_DATABASE_URL=postgresql+psycopg://dhr:dhr_dev_password@db:5432/dhr_test
```

**Option B** — Passer en variable d'environnement à `pytest` :

```bash
docker compose exec -e TEST_DATABASE_URL="postgresql+psycopg://dhr:dhr_dev_password@db:5432/dhr_test" backend pytest
```

**Note** : si `TEST_DATABASE_URL` est absente, `conftest.py` construit l'URL à partir des variables `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_TEST_DB` (avec des valeurs par défaut).

### 3.3 Migrations

Le `conftest.py` (fixture `apply_migrations`) :

1. `DROP SCHEMA public CASCADE; CREATE SCHEMA public;` sur `dhr_test`.
2. `alembic upgrade head` sur `dhr_test`.

**C'est automatique** : tu n'as rien à faire manuellement. À chaque session de test, la base est recréée from scratch.

---

## 4. Lancer les tests

### 4.1 Tous les tests

```bash
docker compose exec backend pytest
```

**Attendu** : tous les tests passent (une fois les fixtures corrigées).

### 4.2 Avec sortie détaillée

```bash
docker compose exec backend pytest -v
```

Affiche le nom de chaque test (`PASSED`, `FAILED`, `SKIPPED`).

### 4.3 Avec sortie très détaillée

```bash
docker compose exec backend pytest -vv
```

Affiche les assertions, les fixtures utilisées, etc. Utile pour déboguer.

### 4.4 Sans capture des logs

```bash
docker compose exec backend pytest -s
```

Affiche les `print()` et logs dans la console. Utile pour voir les `logger.info` des services.

---

## 5. Lancer un test spécifique

### 5.1 Un fichier

```bash
docker compose exec backend pytest tests/test_ingestion.py -v
```

### 5.2 Une classe

```bash
docker compose exec backend pytest tests/test_ingestion.py::TestDetectionRejets -v
```

### 5.3 Une fonction

```bash
docker compose exec backend pytest tests/test_ingestion.py::TestDetectionRejets::test_ligne_total -v
```

### 5.4 Par mot-clé

```bash
docker compose exec backend pytest -k "coordonnees" -v
docker compose exec backend pytest -k "rejets or vide" -v
```

---

## 6. Couverture de code

### 6.1 Couverture globale

```bash
docker compose exec backend pytest --cov=app --cov-report=term-missing
```

**Attendu** : un tableau avec la couverture par fichier. `--cov-report=term-missing` affiche les lignes non couvertes.

### 6.2 Rapport HTML

```bash
docker compose exec backend pytest --cov=app --cov-report=html
```

Génère `backend/htmlcov/index.html`. Ouvre-le dans un navigateur pour voir les lignes couvertes/non couvertes.

### 6.3 Seuil de couverture

```bash
docker compose exec backend pytest --cov=app --cov-fail-under=70
```

Échoue si la couverture < 70 %. Utile en CI.

**Note** : au début, la couverture sera < 70 % (certains services ne sont pas encore testés). On l'augmentera au fur et à mesure.

---

## 7. Tests d'intégration

Les tests d'intégration sont marqués `@pytest.mark.integration`. Ils testent le pipeline complet (ingestion → rapprochement → consolidation).

### 7.1 Lancer uniquement les tests d'intégration

```bash
docker compose exec backend pytest -m integration -v
```

### 7.2 Exclure les tests d'intégration (tests rapides)

```bash
docker compose exec backend pytest -m "not integration" -v
```

Utile quand on veut itérer rapidement sur les tests unitaires.

---

## 8. CI GitHub Actions

La CI (`.github/workflows/ci.yml`) exécute automatiquement :

1. **Lint** : `ruff check .`
2. **Format** : `ruff format --check .`
3. **Types** : `mypy app/services app/models`
4. **Migrations** : `alembic upgrade head` + `downgrade base` + `upgrade head`
5. **Tests** : `pytest --cov=app --cov-fail-under=70`

**Sur chaque PR et push sur `main`.** Aucune PR ne peut être mergée si la CI est rouge.

**Voir les résultats** : onglet « Actions » du repo GitHub.

---

## 9. Dépannage

### Erreur : `database "dhr_test" does not exist`

Créer la base :

```bash
docker compose exec db psql -U dhr -d dhr -c "CREATE DATABASE dhr_test;"
```

### Erreur : `TEST_DATABASE_URL` non défini

Ajouter au `.env` ou passer en variable d'environnement (cf. §3.2).

### Erreur : `ModuleNotFoundError: No module named 'pytest'`

Les dépendances de test ne sont pas installées. Vérifier que `pyproject.toml` contient `pytest` dans `[project.optional-dependencies].dev`, puis rebuild :

```bash
docker compose build --no-cache backend
```

### Erreur : `sqlalchemy.exc.ProgrammingError: relation "source" does not exist`

Les migrations n'ont pas été appliquées. `conftest.py` les applique automatiquement, mais si le test échoue avant, vérifier :

```bash
docker compose exec backend alembic upgrade head
```

### Erreur : `ImportError: cannot import name 'X' from 'app.services.Y'`

Un import est cassé. Vérifier que le service Y expose bien X (peut-être un renommage).

### Test qui échoue de manière inattendue

Lancer avec `-s -vv` pour voir les logs :

```bash
docker compose exec backend pytest tests/test_X.py::test_Y -s -vv
```

---

## 10. Conventions

### 10.1 Nommage

- **Fichier** : `test_<service>.py` (ex. `test_ingestion.py`).
- **Classe** : `Test<Fonction>` (ex. `TestDetectionRejets`).
- **Fonction** : `test_<cas>` (ex. `test_ligne_total`).

### 10.2 Structure d'un test

```python
def test_cas_attendu(self, db, fixture1):
    # Arrange : préparer les données
    ...
    # Act : exécuter la fonction
    ...
    # Assert : vérifier le résultat
    assert ...
```

### 10.3 Fixtures

- `db` : session SQLAlchemy (rollback automatique après le test).
- `client` : client HTTP FastAPI (dépendances overridées).
- `source_onep` : source ONEP (seedée).
- `fichier_vide` / `fichier_avec_feuille` : fichiers de test.
- `ref_geo_ci` / `localite_test` : hiérarchie administrative + localité.
- `excel_fixture_path` : chemin vers le fichier Excel de test.

### 10.4 Marqueurs

- `@pytest.mark.slow` : test lent (> 1s). Peut être skippé avec `-m "not slow"`.
- `@pytest.mark.integration` : test d'intégration (pipeline complet). Peut être skippé avec `-m "not integration"`.

### 10.5 Couverture

Chaque service doit avoir **au moins** un test qui couvre :
- Le cas nominal (happy path).
- Au moins un cas d'erreur (mauvais input, exception).
- Les cas limites (NULL, vide, hors bornes).

---

## Annexe — Commandes rapides

```bash
# Tous les tests
docker compose exec backend pytest

# Tests + couverture
docker compose exec backend pytest --cov=app --cov-report=term-missing

# Un fichier
docker compose exec backend pytest tests/test_ingestion.py -v

# Un test
docker compose exec backend pytest tests/test_ingestion.py::TestDetectionRejets::test_ligne_total -v

# Tests d'intégration
docker compose exec backend pytest -m integration -v

# Tests rapides (sans intégration)
docker compose exec backend pytest -m "not integration" -v

# Lint
docker compose exec backend ruff check .

# Format
docker compose exec backend ruff format --check .

# Types
docker compose exec backend mypy app/services app/models
```

--- FIN TESTS/README.MD ---

---

## 4. Ordre d'application recommandé

### Étape 1 — Créer la base `dhr_test`

```bash
docker compose exec db psql -U dhr -d dhr -c "CREATE DATABASE dhr_test;"
```

### Étape 2 — Ajouter `TEST_DATABASE_URL` au `.env`

À la racine du projet, dans `.env` :

```bash
TEST_DATABASE_URL=postgresql+psycopg://dhr:dhr_dev_password@db:5432/dhr_test
```

**Attention** : adapte `dhr_dev_password` à ton mot de passe réel (défini dans `docker-compose.yml`).

### Étape 3 — Créer les fichiers de test

Applique les fichiers déjà livrés dans le message précédent :

1. `backend/tests/__init__.py` (vide)
2. `backend/tests/conftest.py`
3. `backend/tests/fixtures/__init__.py` (vide)
4. `backend/tests/test_coordonnees.py`
5. `backend/tests/test_ingestion.py`
6. `backend/tests/test_rapprochement.py`
7. `backend/tests/test_consolidation.py`
8. `backend/tests/test_integration_pipeline.py`
9. `backend/tests/README.md` (ce fichier, optionnel)

### Étape 4 — Lancer les tests

```bash
docker compose exec backend pytest -v
```

**Il y aura probablement des échecs au début.** C'est **normal**. Copie les erreurs, je les corrige avec toi.

### Étape 5 — Itérer

Pour chaque test qui échoue :
1. Lire l'erreur (assertion, fixture manquante, import).
2. Corriger (dans le test ou dans le service).
3. Relancer.

---

## 5. Ensuite, on fait l'Option B (frontend)

Une fois les tests backend verts (ou au moins les tests unitaires), on passe au frontend :

| # | Fichier | Correction |
|---|---------|-----------|
| F1 | `Mapping.tsx` | Ajouter `usage_ouvrage_brut` à `CHAMPS_STANDARDS` |
| F2 | `MapView.tsx` | Forme = `nature_ouvrage` (cercle/carré/losange) |
| F3 | `Liste.tsx` | Export via `fetch` + `blob` |
| F4 | `pages/OLD_Carte.tsx` | Supprimer |
| F5 | `api.ts` | Redirection 401 |
| F6 | Toutes les pages | `Skeleton` au lieu de « Chargement... » |
| F7 | `Liste.tsx`, `Qualite.tsx` | Implémenter les stubs |
| F9 | `Parametres.tsx` | Bouton « Supprimer le JWT » |

**Dis-moi si tu veux qu'on commence par les tests backend (Option 1) ou directement par le frontend (Option 2).** Je recommande les tests d'abord.