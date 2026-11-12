
---

## Table des matières

1. [Prérequis](#1-prérequis)
2. [Tests de la base (structure)](#2-tests-de-la-base-structure)
    - 2.1 Tables
    - 2.2 Vues
    - 2.3 Fonctions
    - 2.4 Triggers
    - 2.5 Extensions
    - 2.6 Contraintes CHECK et UNIQUE
    - 2.7 Clés étrangères
    - 2.8 Index (btree, GIN, GIST, partiels)
    - 2.9 Colonnes générées (`geom`, `geom_centre`)
3. [Tests de `schema.sql`](#3-tests-de-schemasql)
4. [Tests de la migration initiale (`0001_initial.py`)](#4-tests-de-la-migration-initiale-0001_initialpy)
5. [Tests de `models.py` (alignement ORM ↔ schéma)](#5-tests-de-modelspy-alignement-orm--schéma)
6. [Tests de `env.py` (Alembic)](#6-tests-de-envpy-alembic)
7. [Tests PostGIS (spécifiques)](#7-tests-postgis-spécifiques)
8. [Tests de cohérence Bible ↔ Base](#8-tests-de-cohérence-bible--base)
9. [Tests de régression (drift)](#9-tests-de-régression-drift)
10. [Checklist finale](#10-checklist-finale)

---

## 1. Prérequis

- Docker Compose en état de marche (`docker compose ps` : `db` et `backend` `running`).
- Base accessible : `docker compose exec db psql -U dhr -d dhr -c "SELECT 1;"` retourne `1`.
- Migration appliquée : `docker compose exec backend alembic current` retourne `0001_initial (head)`.

**Variables utiles** :

```bash
# Alias pour ne pas répéter la commande
PSQL="docker compose exec -T db psql -U dhr -d dhr -c"
```

---

## 2. Tests de la base (structure)

### 2.1 Tables

**Objectif** : vérifier que les **13 tables** de la Bible existent.

```bash
docker compose exec db psql -U dhr -d dhr -c "\dt"
```

**Attendu** :

```
 public | cgpe               | table | dhr
 public | feuille            | table | dhr
 public | fichier            | table | dhr
 public | ingestion_run      | table | dhr
 public | ligne_ingeree      | table | dhr
 public | localite           | table | dhr
 public | localite_alias     | table | dhr
 public | mapping_feuille    | table | dhr
 public | ouvrage            | table | dhr
 public | ouvrage_projet     | table | dhr
 public | projet_financement | table | dhr
 public | ref_geo_admin      | table | dhr
 public | source             | table | dhr
```

**Nombre attendu** : 13 tables.

**Vérification alternative** :

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"
```

**Attendu** : `13`.

**En cas d'échec** :
- Si < 13 → une table n'a pas été créée. Vérifier `0001_initial.py` (opérations `op.create_table`).
- Si > 13 → une table parasite existe. Vérifier `alembic_version` (normale, ne pas compter) ou une ancienne table non supprimée.

### 2.2 Vues

**Objectif** : vérifier que les **3 vues DHR** existent (plus 2 vues PostGIS système).

```bash
docker compose exec db psql -U dhr -d dhr -c "\dv"
```

**Attendu** :

```
 public | geography_columns     | view | dhr    ← PostGIS système
 public | geometry_columns      | view | dhr    ← PostGIS système
 public | v_points_consolides   | view | dhr    ← DHR
 public | v_points_par_fichier  | view | dhr    ← DHR
 public | v_qualite_par_fichier | view | dhr    ← DHR
```

**Nombre attendu** : 5 vues (3 DHR + 2 PostGIS).

**Vérification** :

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public' AND table_name LIKE 'v_%';"
```

**Attendu** : `3`.

**En cas d'échec** :
- Si < 3 → une vue n'a pas été créée. Vérifier `0001_initial.py` (opérations `op.execute("CREATE VIEW ...")`).
- Si 0 → le bloc vues de la migration n'a pas été exécuté.

### 2.3 Fonctions

**Objectif** : vérifier que les **3 fonctions** existent.

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT proname, prosrc FROM pg_proc WHERE proname IN ('geom_from_latlon', 'trg_set_updated_at', 'trg_check_localite_geo') ORDER BY proname;"
```

**Attendu** : 3 lignes.

**Vérification** :

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM pg_proc WHERE proname IN ('geom_from_latlon', 'trg_set_updated_at', 'trg_check_localite_geo');"
```

**Attendu** : `3`.

**En cas d'échec** :
- Si 0 → le bloc fonctions de la migration n'a pas été exécuté.
- Si 1 ou 2 → une fonction manque. Vérifier `0001_initial.py`.

**Test fonctionnel de `geom_from_latlon`** :

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT ST_AsText(geom_from_latlon(7.5, -5.5)) AS point, geom_from_latlon(7.5, -5.5) IS NULL AS should_be_null;"
```

**Attendu** :

```
     point      | should_be_null 
----------------+----------------
 POINT(-5.5 7.5) | f
```

**Note** : `POINT(-5.5 7.5)` = longitude en X, latitude en Y (convention PostGIS).

**Test bornes** :

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT geom_from_latlon(NULL, -5.5) IS NULL AS null_lat, geom_from_latlon(100, -5.5) IS NULL AS lat_hors_bornes, geom_from_latlon(0, 0) IS NULL AS zero;"
```

**Attendu** : `t | t | t` (les 3 retournent NULL).

### 2.4 Triggers

**Objectif** : vérifier que les **8 triggers** existent (7 `set_updated_at` + 1 `check_localite_geo`).

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT event_object_table AS table_name, trigger_name, event_manipulation FROM information_schema.triggers WHERE trigger_schema = 'public' ORDER BY table_name, trigger_name;"
```

**Attendu** : 8 lignes.

| table_name | trigger_name | event_manipulation |
|-----------|--------------|-------------------|
| cgpe | set_updated_at | UPDATE |
| fichier | set_updated_at | UPDATE |
| localite | check_localite_geo | INSERT |
| localite | check_localite_geo | UPDATE |
| localite | set_updated_at | UPDATE |
| ouvrage | set_updated_at | UPDATE |
| projet_financement | set_updated_at | UPDATE |
| ref_geo_admin | set_updated_at | UPDATE |
| source | set_updated_at | UPDATE |

**Note** : `check_localite_geo` apparaît 2 fois (INSERT et UPDATE), c'est normal.

**Vérification** :

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'public' AND trigger_name = 'set_updated_at';"
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'public' AND trigger_name = 'check_localite_geo';"
```

**Attendu** : `7` (set_updated_at) et `2` (check_localite_geo : INSERT + UPDATE).

**Test fonctionnel de `set_updated_at`** :

```bash
# 1. Récupérer updated_at d'une source
docker compose exec db psql -U dhr -d dhr -c "SELECT id_source, updated_at FROM source WHERE id_source = 1;"

# 2. Modifier la source
docker compose exec db psql -U dhr -d dhr -c "UPDATE source SET commentaire = 'test trigger' WHERE id_source = 1;"

# 3. Vérifier que updated_at a changé
docker compose exec db psql -U dhr -d dhr -c "SELECT id_source, updated_at FROM source WHERE id_source = 1;"
```

**Attendu** : `updated_at` a changé après l'UPDATE.

**Test fonctionnel de `check_localite_geo`** :

```bash
# 1. Créer un nœud district (racine)
docker compose exec db psql -U dhr -d dhr -c "INSERT INTO ref_geo_admin (niveau, nom, parent_id) VALUES ('district', 'TEST_DISTRICT', NULL) RETURNING id_geo;"

# 2. Essayer de créer une localité qui pointe vers un district (doit échouer)
docker compose exec db psql -U dhr -d dhr -c "INSERT INTO localite (id_geo, nom_usage) VALUES ((SELECT id_geo FROM ref_geo_admin WHERE nom = 'TEST_DISTRICT'), 'TEST_LOC');"
```

**Attendu** : erreur `localite.id_geo=... doit pointer vers un nœud de niveau 'localite' (trouvé: district)`.

**Nettoyage** :

```bash
docker compose exec db psql -U dhr -d dhr -c "DELETE FROM ref_geo_admin WHERE nom = 'TEST_DISTRICT';"
```

### 2.5 Extensions

**Objectif** : vérifier que les **4 extensions** sont installées.

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT extname, extversion FROM pg_extension WHERE extname IN ('postgis', 'pg_trgm', 'unaccent', 'fuzzystrmatch') ORDER BY extname;"
```

**Attendu** : 4 lignes (postgis, pg_trgm, unaccent, fuzzystrmatch).

**Vérification** :

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM pg_extension WHERE extname IN ('postgis', 'pg_trgm', 'unaccent', 'fuzzystrmatch');"
```

**Attendu** : `4`.

**En cas d'échec** : ajouter `CREATE EXTENSION IF NOT EXISTS <nom>;` dans `schema.sql` et `0001_initial.py`.

### 2.6 Contraintes CHECK et UNIQUE

**Objectif** : vérifier que les **contraintes CHECK et UNIQUE** déclarées dans la Bible existent.

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT conname, contype, conrelid::regclass AS table_name FROM pg_constraint WHERE connamespace = 'public'::regnamespace AND contype IN ('c', 'u') ORDER BY table_name, conname;"
```

**Attendu** (liste non exhaustive, à comparer avec la Bible § 2.2) :

| conname | contype | table_name |
|---------|---------|------------|
| source_type_source_check | c | source |
| uq_source_nom | u | source |
| ref_geo_admin_niveau_check | c | ref_geo_admin |
| ref_geo_admin_type_localite_check | c | ref_geo_admin |
| chk_ref_geo_type_localite | c | ref_geo_admin |
| chk_ref_geo_parent | c | ref_geo_admin |
| uq_ref_geo_parent_nom_niveau | u | ref_geo_admin |
| uq_alias_localite | u | localite_alias |
| fichier_statut_check | c | fichier |
| feuille_type_contenu_check | c | feuille |
| feuille_statut_ingestion_check | c | feuille |
| uq_feuille_fichier_index | u | feuille |
| mapping_feuille_confiance_check | c | mapping_feuille |
| uq_mapping_feuille_entete | u | mapping_feuille |
| ingestion_run_mode_check | c | ingestion_run |
| ingestion_run_statut_check | c | ingestion_run |
| chk_run_mode_params | c | ingestion_run |
| ligne_ingeree_statut_qualite_check | c | ligne_ingeree |
| uq_ligne_feuille_run_num | u | ligne_ingeree |
| ouvrage_nature_check | c | ouvrage |
| ouvrage_alimentation_check | c | ouvrage |
| ouvrage_realisation_check | c | ouvrage |
| ouvrage_etat_check | c | ouvrage |
| cgpe_statut_check | c | cgpe |
| projet_financement_type_check | c | projet_financement |
| ouvrage_projet_role_check | c | ouvrage_projet |

**Vérification rapide** :

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM pg_constraint WHERE connamespace = 'public'::regnamespace AND contype = 'c';"
# Attendu : 15 CHECK
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM pg_constraint WHERE connamespace = 'public'::regnamespace AND contype = 'u';"
# Attendu : 5 UNIQUE
```

**En cas d'échec** : vérifier `0001_initial.py` (opérations `sa.CheckConstraint` et `sa.UniqueConstraint` dans `__table_args__`).

### 2.7 Clés étrangères

**Objectif** : vérifier que les **FK** existent, avec les bonnes actions `ON DELETE`.

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT conname, conrelid::regclass AS table_name, confrelid::regclass AS ref_table, confdeltype FROM pg_constraint WHERE connamespace = 'public'::regnamespace AND contype = 'f' ORDER BY table_name, conname;"
```

**Attendu** (liste non exhaustive) :

| conname | table_name | ref_table | confdeltype |
|---------|-----------|-----------|-------------|
| ref_geo_admin_parent_id_fkey | ref_geo_admin | ref_geo_admin | r (RESTRICT) |
| localite_id_geo_fkey | localite | ref_geo_admin | r |
| localite_alias_id_localite_fkey | localite_alias | localite | c (CASCADE) |
| fichier_id_source_fkey | fichier | source | r |
| feuille_id_fichier_fkey | feuille | fichier | c |
| mapping_feuille_id_feuille_fkey | mapping_feuille | feuille | c |
| ingestion_run_id_fichier_fkey | ingestion_run | fichier | c |
| ingestion_run_id_feuille_fkey | ingestion_run | feuille | c |
| ligne_ingeree_id_feuille_fkey | ligne_ingeree | feuille | c |
| ligne_ingeree_id_run_fkey | ligne_ingeree | ingestion_run | n (SET NULL) |
| ligne_ingeree_id_localite_fkey | ligne_ingeree | localite | n |
| ligne_ingeree_id_ouvrage_consolide_fkey | ligne_ingeree | ouvrage | n |
| ouvrage_id_localite_fkey | ouvrage | localite | r |
| cgpe_id_localite_fkey | cgpe | localite | c |
| cgpe_id_ouvrage_fkey | cgpe | ouvrage | n |
| projet_financement_id_source_financeur_fkey | projet_financement | source | r |
| ouvrage_projet_id_ouvrage_fkey | ouvrage_projet | ouvrage | c |
| ouvrage_projet_id_projet_fkey | ouvrage_projet | projet_financement | c |

**Vérification rapide** :

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM pg_constraint WHERE connamespace = 'public'::regnamespace AND contype = 'f';"
# Attendu : 18 FK
```

**En cas d'échec** : vérifier `0001_initial.py` (opérations `sa.ForeignKeyConstraint` dans `__table_args__`).

### 2.8 Index (btree, GIN, GIST, partiels)

**Objectif** : vérifier que les **index** déclarés dans la Bible existent, avec le bon type.

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' ORDER BY indexname;"
```

**Attendu** : liste des index (à comparer avec la Bible § 2.2).

**Vérifications ciblées** :

```bash
# Compter les index btree
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND indexdef LIKE '%btree%';"

# Compter les index GIN
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND indexdef LIKE '%gin%';"
# Attendu : 8 (idx_ref_geo_nom_trgm, idx_alias_trgm, idx_localite_nom_trgm, idx_localite_metadata, idx_ligne_donnees_brutes, idx_ouvrage_metadata, idx_ouvrage_qualite_eau, idx_cgpe_metadata)

# Compter les index GIST
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND indexdef LIKE '%gist%';"
# Attendu : 3 (idx_localite_geom, idx_ligne_geom, idx_ouvrage_geom)

# Vérifier l'index partiel sur code_ouvrage
docker compose exec db psql -U dhr -d dhr -c "SELECT indexdef FROM pg_indexes WHERE indexname = 'idx_ouvrage_code';"
# Attendu : ... WHERE (code_ouvrage IS NOT NULL)
```

**En cas d'échec** : vérifier `0001_initial.py` (opérations `op.create_index` pour btree, `op.execute("CREATE INDEX ... USING gin/gist")` pour GIN/GIST).

### 2.9 Colonnes générées (`geom`, `geom_centre`)

**Objectif** : vérifier que les **colonnes générées** existent et sont bien calculées.

```bash
# Vérifier la présence des colonnes générées
docker compose exec db psql -U dhr -d dhr -c "SELECT table_name, column_name, is_generated, generation_expression FROM information_schema.columns WHERE table_schema = 'public' AND is_generated = 'ALWAYS' ORDER BY table_name, column_name;"
```

**Attendu** :

| table_name | column_name | is_generated | generation_expression |
|-----------|-------------|--------------|----------------------|
| ligne_ingeree | geom | ALWAYS | geom_from_latlon(latitude_decimal, longitude_decimal) |
| localite | geom_centre | ALWAYS | geom_from_latlon(latitude_centre, longitude_centre) |
| ouvrage | geom | ALWAYS | geom_from_latlon(latitude_decimal, longitude_decimal) |

**Vérification rapide** :

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'public' AND is_generated = 'ALWAYS';"
# Attendu : 3
```

**Test fonctionnel** :

```bash
# 1. Insérer une localité avec des coordonnées (via un nœud localité valide)
docker compose exec db psql -U dhr -d dhr -c "INSERT INTO localite (id_geo, nom_usage, latitude_centre, longitude_centre) VALUES ((SELECT id_geo FROM ref_geo_admin LIMIT 1), 'TEST_GEN', 7.5, -5.5) RETURNING id_localite, ST_AsText(geom_centre);"
```

**Attendu** : `geom_centre` calculé automatiquement (`POINT(-5.5 7.5)`).

**Nettoyage** :

```bash
docker compose exec db psql -U dhr -d dhr -c "DELETE FROM localite WHERE nom_usage = 'TEST_GEN';"
```

**En cas d'échec** :
- Si 0 colonne générée → la migration n'a pas ajouté les colonnes (`op.execute("ALTER TABLE ... ADD COLUMN ... GENERATED ...")`).
- Si 3 mais mauvais `generation_expression` → l'expression SQL est incorrecte.

---

## 3. Tests de `schema.sql`

**Objectif** : vérifier que `schema.sql` est **idempotent** et produit le même schéma que la migration.

### 3.1 Test from scratch

```bash
# 1. Reset la base
docker compose exec db psql -U dhr -d dhr -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# 2. Appliquer schema.sql
docker compose exec -T db psql -U dhr -d dhr < backend/sql/schema.sql

# 3. Vérifier que tout est là (13 tables, 5 vues, 3 fonctions, 8 triggers, 6 sources)
docker compose exec db psql -U dhr -d dhr -c "SELECT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE') AS tables, (SELECT COUNT(*) FROM information_schema.views WHERE table_schema='public') AS views, (SELECT COUNT(*) FROM pg_proc WHERE proname IN ('geom_from_latlon','trg_set_updated_at','trg_check_localite_geo')) AS functions, (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema='public') AS triggers, (SELECT COUNT(*) FROM source) AS sources;"
```

**Attendu** : `tables=13, views=5, functions=3, triggers=8, sources=6`.

### 3.2 Test de comparaison avec la migration

**Objectif** : vérifier que `schema.sql` et `0001_initial.py` produisent le **même schéma**.

```bash
# 1. Reset la base, appliquer schema.sql, dumper la structure
docker compose exec db psql -U dhr -d dhr -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose exec -T db psql -U dhr -d dhr < backend/sql/schema.sql
docker compose exec db pg_dump -U dhr -d dhr --schema-only --no-owner --no-privileges > /tmp/dump_schema.sql

# 2. Reset la base, appliquer la migration, dumper la structure
docker compose exec db psql -U dhr -d dhr -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose exec backend alembic upgrade head
docker compose exec db pg_dump -U dhr -d dhr --schema-only --no-owner --no-privileges > /tmp/dump_migration.sql

# 3. Comparer (les diffs attendus : ordre des CREATE, commentaires, etc.)
diff /tmp/dump_schema.sql /tmp/dump_migration.sql
```

**Attendu** : pas de différence structurelle (les diffs cosmétiques d'ordre sont acceptables).

**En cas de divergence structurelle** : `schema.sql` et `0001_initial.py` ne sont pas alignés. Corriger celui qui dérive.

### 3.3 Test de ré-exécution (idempotence)

**Objectif** : vérifier que `schema.sql` peut être ré-exécuté sans erreur (grâce aux `IF NOT EXISTS` et `ON CONFLICT DO NOTHING`).

```bash
docker compose exec -T db psql -U dhr -d dhr < backend/sql/schema.sql
```

**Attendu** : pas d'erreur (les `CREATE TABLE` échouent silencieusement, les `CREATE INDEX` aussi, les `INSERT ... ON CONFLICT DO NOTHING` ne dupliquent pas).

**Note** : `schema.sql` n'est **pas** idempotent sur `CREATE TABLE` (il faut `DROP SCHEMA` d'abord). C'est **volontaire** : le script est fait pour créer une base from scratch. Si tu veux le rendre idempotent, il faudrait `CREATE TABLE IF NOT EXISTS` partout, ce qui masquerait les erreurs. **Ne pas modifier.**

---

## 4. Tests de la migration initiale (`0001_initial.py`)

### 4.1 Test upgrade from scratch

```bash
# 1. Reset la base
docker compose exec db psql -U dhr -d dhr -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# 2. Appliquer la migration
docker compose exec backend alembic upgrade head

# 3. Vérifier la version
docker compose exec backend alembic current
```

**Attendu** : `0001_initial (head)`.

### 4.2 Test downgrade + upgrade (idempotence)

**Objectif** : vérifier que la migration est **réversible** et **idempotente**.

```bash
# 1. Downgrade
docker compose exec backend alembic downgrade base

# 2. Vérifier que la base est vide
docker compose exec db psql -U dhr -d dhr -c "\dt"
# Attendu : "Did not find any relations."

# 3. Upgrade à nouveau
docker compose exec backend alembic upgrade head

# 4. Vérifier que tout est revenu
docker compose exec db psql -U dhr -d dhr -c "\dt"
# Attendu : 13 tables
```

**En cas d'échec** :
- Si `downgrade base` échoue → une FK n'est pas correctement supprimée. Vérifier l'ordre des `op.drop_table` dans `downgrade()`.
- Si `upgrade head` après downgrade échoue → un objet n'a pas été recréé. Vérifier `upgrade()`.

### 4.3 Test de la version Alembic

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT * FROM alembic_version;"
```

**Attendu** : 1 ligne avec `version_num = '0001_initial'`.

### 4.4 Test du seed

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT id_source, nom, type_source FROM source ORDER BY id_source;"
```

**Attendu** : 6 lignes (ONEP, SODECI, UNICEF, BAD, LONACI, ETAT_CI).

**Test d'idempotence du seed** :

```bash
# Ré-appliquer upgrade head (ne devrait pas dupliquer les sources)
docker compose exec backend alembic upgrade head
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM source;"
```

**Attendu** : `6` (pas 12).

**Explication** : le seed utilise `ON CONFLICT (nom) DO NOTHING`, donc il est idempotent.

---

## 5. Tests de `models.py` (alignement ORM ↔ schéma)

### 5.1 Import des modèles

**Objectif** : vérifier que `models.py` se charge sans erreur.

```bash
docker compose exec backend python -c "from app.models import Source, RefGeoAdmin, Localite, LocaliteAlias, Fichier, Feuille, MappingFeuille, IngestionRun, LigneIngeree, Ouvrage, CGPE, ProjetFinancement, OuvrageProjet; print('OK')"
```

**Attendu** : `OK`.

**En cas d'échec** : erreur d'import (typo, import circulaire, etc.). Lire le traceback.

### 5.2 Vérification que `Base.metadata` contient toutes les tables

```bash
docker compose exec backend python -c "from app.db import Base; from app import models; print(sorted(Base.metadata.tables.keys()))"
```

**Attendu** : 13 tables.

**En cas d'échec** : `models.py` n'importe pas toutes les tables (oubli, ou une classe n'hérite pas de `Base`).

### 5.3 Test d'alignement `models.py` ↔ base

**Objectif** : vérifier que `models.py` correspond à la base (pas de dérive).

```bash
# Générer une migration de test (ne pas l'appliquer)
docker compose exec backend alembic revision --autogenerate -m "test drift" --rev-id test_drift

# Inspecter le fichier généré
cat backend/alembic/versions/test_drift_*.py
```

**Attendu** : la migration ne contient **que** des `op.drop_index` (GIN/GIST) et `op.drop_column` (`geom`, `geom_centre`). C'est **normal** (SQLAlchemy ne voit pas ces objets). **Ne pas l'appliquer.**

**En cas de dérive réelle** : si la migration contient `op.drop_table`, `op.drop_column` sur une colonne standard, `op.create_check_constraint`, etc. → `models.py` ne correspond pas à la base. Corriger `models.py` ou la migration.

**Nettoyage** :

```bash
rm backend/alembic/versions/test_drift_*.py
```

### 5.4 Test de lecture/écriture via ORM

**Objectif** : vérifier que les modèles fonctionnent (lecture, écriture, relations).

```bash
docker compose exec backend python -c "
from app.db import SessionLocal
from app.models import Source, RefGeoAdmin, Localite

db = SessionLocal()

# Lecture
sources = db.query(Source).all()
print(f'Sources: {len(sources)}')

# Écriture
district = RefGeoAdmin(niveau='district', nom='TEST_ORM', parent_id=None)
db.add(district)
db.flush()
print(f'District créé: id={district.id_geo}')

# Nettoyage
db.delete(district)
db.commit()
db.close()
print('OK')
"
```

**Attendu** : `Sources: 6`, `District créé: id=...`, `OK`.

**En cas d'échec** :
- Si `Sources: 0` → le seed n'a pas été appliqué (ou la base est vide).
- Si `UNIQUE constraint failed` sur `TEST_ORM` → un test précédent n'a pas nettoyé. Supprimer manuellement.
- Si erreur de mapping → `models.py` ne correspond pas à la base.

---

## 6. Tests de `env.py` (Alembic)

### 6.1 Vérifier que `env.py` charge bien les modèles

```bash
docker compose exec backend python -c "
import sys
sys.path.insert(0, '/app')
from app.db import Base
from app import models
print(sorted(Base.metadata.tables.keys()))
"
```

**Attendu** : 13 tables.

### 6.2 Vérifier que `NOS_TABLES` n'est pas vide (garde-fou)

```bash
docker compose exec backend python -c "
from app.db import Base
from app import models
NOS_TABLES = set(Base.metadata.tables.keys())
assert len(NOS_TABLES) > 0, 'NOS_TABLES est vide !'
print(f'NOS_TABLES: {len(NOS_TABLES)} tables')
"
```

**Attendu** : `NOS_TABLES: 13 tables`.

**En cas d'échec** : `models.py` n'est pas chargé correctement. Vérifier `env.py` (le `from app import models` doit être **avant** `NOS_TABLES = set(...)`).

### 6.3 Vérifier que `alembic current` fonctionne

```bash
docker compose exec backend alembic current
```

**Attendu** : `0001_initial (head)`.

### 6.4 Vérifier que `alembic history` fonctionne

```bash
docker compose exec backend alembic history
```

**Attendu** : `0001_initial -> (head), ...` (une seule migration).

---

## 7. Tests PostGIS (spécifiques)

### 7.1 Test `ST_AsText` sur `geom_from_latlon`

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT ST_AsText(geom_from_latlon(7.5, -5.5)) AS point;"
```

**Attendu** : `POINT(-5.5 7.5)` (lon en X, lat en Y).

### 7.2 Test `ST_Distance` (distance géodésique)

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT ST_Distance(geom_from_latlon(7.5, -5.5)::geography, geom_from_latlon(7.6, -5.6)::geography) AS distance_m;"
```

**Attendu** : une distance en mètres (~13 000 m).

### 7.3 Test index GIST (performance)

```bash
docker compose exec db psql -U dhr -d dhr -c "EXPLAIN ANALYZE SELECT * FROM ouvrage WHERE ST_DWithin(geom::geography, geom_from_latlon(7.5, -5.5)::geography, 10000);"
```

**Attendu** : `Bitmap Index Scan on idx_ouvrage_geom` (l'index GIST est utilisé).

**En cas d'échec** : si `Seq Scan` → l'index GIST n'existe pas ou n'est pas utilisé. Vérifier `idx_ouvrage_geom`.

### 7.4 Test SRID 4326

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT ST_SRID(geom_from_latlon(7.5, -5.5)) AS srid;"
```

**Attendu** : `4326`.

### 7.5 Test des vues PostGIS système

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT * FROM geometry_columns LIMIT 1;"
docker compose exec db psql -U dhr -d dhr -c "SELECT * FROM geography_columns LIMIT 1;"
```

**Attendu** : ces vues existent (elles sont créées par PostGIS).

---

## 8. Tests de cohérence Bible ↔ Base

### 8.1 Vérifier que toutes les tables de la Bible existent

**Bible § 2.1.1** : 13 tables.

```bash
docker compose exec backend python -c "
from app.db import Base
from app import models

bible_tables = {
    'source', 'ref_geo_admin', 'localite', 'localite_alias',
    'fichier', 'feuille', 'mapping_feuille', 'ingestion_run', 'ligne_ingeree',
    'ouvrage', 'cgpe', 'projet_financement', 'ouvrage_projet',
}
model_tables = set(Base.metadata.tables.keys())

assert bible_tables == model_tables, f'Différence: {bible_tables ^ model_tables}'
print(f'{len(model_tables)} tables alignées avec la Bible')
"
```

**Attendu** : `13 tables alignées avec la Bible`.

### 8.2 Vérifier que les vues de la Bible existent

**Bible § 2.2.D** : 3 vues.

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT table_name FROM information_schema.views WHERE table_schema = 'public' AND table_name LIKE 'v_%' ORDER BY table_name;"
```

**Attendu** : `v_points_consolides`, `v_points_par_fichier`, `v_qualite_par_fichier`.

### 8.3 Vérifier les 6 statuts de qualité

**Bible § 3.1.6** : `'ok'`, `'geom_invalide'`, `'localite_non_resolue'`, `'type_ouvrage_inconnu'`, `'rejete'`, `'doublon_suspect'`.

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'ligne_ingeree_statut_qualite_check';"
```

**Attendu** : `CHECK ((statut_qualite = ANY (ARRAY['ok'::text, 'localite_non_resolue'::text, 'geom_invalide'::text, 'type_ouvrage_inconnu'::text, 'rejete'::text, 'doublon_suspect'::text])))`.

### 8.4 Vérifier les 3 champs sémantiques de `ouvrage`

**Bible § 1.4 décision 3** : `nature_ouvrage`, `type_alimentation`, `realisation_par`.

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ouvrage' AND column_name IN ('nature_ouvrage', 'type_alimentation', 'realisation_par') ORDER BY column_name;"
```

**Attendu** : 3 lignes (`nature_ouvrage`, `realisation_par`, `type_alimentation`).

### 8.5 Vérifier l'absence de `type_ouvrage`

**Bible § 1.4 décision 3** : `type_ouvrage` a été supprimé.

```bash
docker compose exec db psql -U dhr -d dhr -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'type_ouvrage';"
```

**Attendu** : 0 ligne.

---

## 9. Tests de régression (drift)

### 9.1 Vérifier qu'il n'y a pas de dérive non connue

**Objectif** : s'assurer que `models.py` ne dérive pas de la base **autrement que** sur les colonnes générées et les index GIN/GIST.

```bash
# Générer la migration de test
docker compose exec backend alembic revision --autogenerate -m "test drift" --rev-id test_drift

# Inspecter
cat backend/alembic/versions/test_drift_*.py
```

**Opérations autorisées** (faux positifs connus) :
- `op.drop_index(... postgresql_using='gin')` ou `'gist'`
- `op.drop_column(... 'geom')` ou `'geom_centre'`
- Les opérations symétriques dans `downgrade()` (`create_index`, `add_column`)

**Opérations interdites** (vraie dérive) :
- `op.drop_table(...)`
- `op.drop_column(...)` sur une colonne **non générée**
- `op.add_column(...)` sur une colonne **non générée**
- `op.create_check_constraint(...)` / `op.drop_constraint(...)` sur un CHECK
- `op.create_unique_constraint(...)` / `op.drop_constraint(...)` sur un UNIQUE
- `op.create_foreign_key(...)` / `op.drop_constraint(...)` sur une FK

**Si une opération interdite apparaît** : `models.py` dérive. Corriger `models.py` ou la base.

**Nettoyage** :

```bash
rm backend/alembic/versions/test_drift_*.py
```

### 9.2 Vérifier que les tests unitaires passent

```bash
docker compose exec backend pytest tests/ -v
```

**Attendu** : tous les tests passent (une fois les tests écrits en Phase D).

---

## 10. Checklist finale

Cocher chaque case après validation.

### 10.1 Base

- [ ] 13 tables (`\dt`)
- [ ] 5 vues (3 DHR + 2 PostGIS) (`\dv`)
- [ ] 3 fonctions (`\df`)
- [ ] 8 triggers (7 `set_updated_at` + 1 `check_localite_geo`) (`information_schema.triggers`)
- [ ] 4 extensions (`pg_extension`)
- [ ] 15 CHECK (`pg_constraint` contype='c')
- [ ] 5 UNIQUE (`pg_constraint` contype='u')
- [ ] 18 FK (`pg_constraint` contype='f')
- [ ] Index btree, GIN, GIST, partiels (`pg_indexes`)
- [ ] 3 colonnes générées (`information_schema.columns` is_generated='ALWAYS')
- [ ] 6 sources seedées (`SELECT * FROM source`)

### 10.2 `schema.sql`

- [ ] From scratch : `DROP SCHEMA` + `schema.sql` → 13 tables, 5 vues, 3 fonctions, 8 triggers, 6 sources
- [ ] Comparaison avec la migration : `pg_dump` identique (diffs cosmétiques acceptés)

### 10.3 Migration `0001_initial.py`

- [ ] `alembic upgrade head` passe sans erreur
- [ ] `alembic downgrade base` passe sans erreur
- [ ] `alembic upgrade head` après downgrade passe sans erreur (idempotent)
- [ ] `alembic current` retourne `0001_initial (head)`
- [ ] `alembic_version` contient `0001_initial`
- [ ] Seed idempotent (6 sources après 2 upgrades)

### 10.4 `models.py`

- [ ] Import sans erreur
- [ ] `Base.metadata.tables` contient 13 tables
- [ ] Pas de dérive non connue (`alembic revision --autogenerate` ne génère que GIN/GIST/colonnes générées)
- [ ] Lecture/écriture via ORM fonctionne (test `Source` + `RefGeoAdmin`)

### 10.5 `env.py`

- [ ] Charge les modèles (`Base.metadata.tables` non vide)
- [ ] `NOS_TABLES` non vide (garde-fou)
- [ ] `alembic current` fonctionne
- [ ] `alembic history` fonctionne

### 10.6 PostGIS

- [ ] `geom_from_latlon(7.5, -5.5)` → `POINT(-5.5 7.5)`
- [ ] `ST_SRID(geom_from_latlon(7.5, -5.5))` → `4326`
- [ ] `ST_Distance` géodésique fonctionne
- [ ] Index GIST utilisé (`EXPLAIN ANALYZE` → `Bitmap Index Scan`)
- [ ] `geometry_columns` et `geography_columns` existent

### 10.7 Cohérence Bible

- [ ] 13 tables alignées avec la Bible § 2.1.1
- [ ] 3 vues alignées avec la Bible § 2.2.D
- [ ] 6 statuts de qualité alignés avec la Bible § 3.1.6
- [ ] 3 champs sémantiques (`nature_ouvrage`, `type_alimentation`, `realisation_par`) alignés avec la Bible § 1.4 décision 3
- [ ] Pas de `type_ouvrage` (Bible § 1.4 décision 3)

---

## Annexes

### A. Commandes de reset

```bash
# Reset complet (perte de données)
docker compose exec db psql -U dhr -d dhr -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Puis appliquer la migration
docker compose exec backend alembic upgrade head

# Ou appliquer schema.sql
docker compose exec -T db psql -U dhr -d dhr < backend/sql/schema.sql
```

### B. Logs utiles

```bash
# Logs backend
docker compose logs -f backend

# Logs db
docker compose logs -f db

# Logs Alembic (si configuré en mode verbose)
docker compose exec backend alembic -x verbose=true upgrade head
```

### C. Diff structurel entre 2 bases

```bash
# Dump structurel de la base 1
docker compose exec db pg_dump -U dhr -d dhr --schema-only --no-owner --no-privileges > /tmp/dump1.sql

# Dump structurel de la base 2 (après reset + migration)
docker compose exec db psql -U dhr -d dhr -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose exec backend alembic upgrade head
docker compose exec db pg_dump -U dhr -d dhr --schema-only --no-owner --no-privileges > /tmp/dump2.sql

# Comparer
diff /tmp/dump1.sql /tmp/dump2.sql
```

### D. Liens vers la Bible

| Section Bible | Sujet | Tests correspondants |
|---------------|-------|----------------------|
| § 2.1.1 | 4 groupes de tables | § 2.1, § 8.1 |
| § 2.2.A | Référentiels | § 2.1, § 8.1 |
| § 2.2.B | Ingestion | § 2.1, § 8.1 |
| § 2.2.C | Métier consolidé | § 2.1, § 8.1 |
| § 2.2.D | Vues | § 2.2, § 8.2 |
| § 2.3.1 | Fonctions PostgreSQL | § 2.3 |
| § 2.3.2 | Triggers | § 2.4 |
| § 3.1.6 | 6 statuts de qualité | § 8.3 |
| § 1.4 décision 3 | 3 champs sémantiques | § 8.4, § 8.5 |

---

**Fin de `tests-db.md`.** Ce document est **exhaustif** : il couvre la base, `schema.sql`, la migration, `models.py`, `env.py`, PostGIS, et la cohérence Bible ↔ Base.
