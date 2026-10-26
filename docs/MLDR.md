# MLDR — Modèle Logique de Données Raffiné

**Projet** : DHR — Centralisation des ouvrages hydrauliques ruraux
**SGBD** : PostgreSQL 14+ / PostGIS 3+
**Version** : 1.1 (ajout `metadata` sur `localite`, `ouvrage`, `cgpe`)

---

## 1. Vue d'ensemble

| Package              | Tables                                                                  |
|----------------------|-------------------------------------------------------------------------|
| **Référentiels**     | `source`, `type_ouvrage`, `ref_geo_admin`, `localite`, `localite_alias` |
| **Ingestion**        | `fichier`, `feuille`, `ingestion_run`, `ligne_ingeree`                  |
| **Métier consolidé** | `ouvrage`, `cgpe`, `projet_financement`, `ouvrage_projet`               |
| **Vues**             | `v_points_par_fichier`, `v_points_consolides`, `v_qualite_par_fichier`  |

**Conventions** :
- PK : `bigserial` pour tables volumineuses, `serial` pour référentiels.
- FK : explicites, `ON DELETE` documenté.
- Timestamps : `created_at` / `updated_at` en `timestamptz`.
- Géométrie : `geometry(Point,4326)` générée via `geom_from_latlon`.
- Métadonnées non mappées : `jsonb` (convention : `docs/metadata_conventions.md`).

---

## 2. Tables

### 2.1 `source`

| Colonne     | Type           | Contrainte                                                      |
|-------------|----------------|-----------------------------------------------------------------|
| id_source   | `serial`       | PK                                                              |
| nom         | `varchar(100)` | NOT NULL, UNIQUE                                                |
| type_source | `varchar(30)`  | NOT NULL, CHECK IN ('public','prive','bailleur','etat','autre') |
| actif       | `boolean`      | NOT NULL DEFAULT true                                           |
| commentaire | `text`         |                                                                 |
| created_at  | `timestamptz`  | NOT NULL DEFAULT now()                                          |
| updated_at  | `timestamptz`  | NOT NULL DEFAULT now()                                          |

### 2.2 `type_ouvrage`

| Colonne         | Type           | Contrainte            |
|-----------------|----------------|-----------------------|
| id_type_ouvrage | `serial`       | PK                    |
| code            | `varchar(20)`  | NOT NULL, UNIQUE      |
| libelle         | `varchar(100)` | NOT NULL              |
| description     | `text`         |                       |
| actif           | `boolean`      | NOT NULL DEFAULT true |

### 2.3 `ref_geo_admin`

| Colonne       | Type           | Contrainte                                                                          |
|---------------|----------------|-------------------------------------------------------------------------------------|
| id_geo        | `serial`       | PK                                                                                  |
| niveau        | `varchar(20)`  | NOT NULL, CHECK IN ('district','region','departement','sous_prefecture','localite') |
| nom           | `varchar(150)` | NOT NULL                                                                            |
| parent_id     | `integer`      | FK → ref_geo_admin(id_geo) ON DELETE RESTRICT                                       |
| code_officiel | `varchar(50)`  |                                                                                     |
| type_localite | `varchar(20)`  | CHECK (NULL ou IN ('village','campement','autre')) ; NULL si niveau ≠ localite      |
| created_at    | `timestamptz`  | NOT NULL DEFAULT now()                                                              |
| updated_at    | `timestamptz`  | NOT NULL DEFAULT now()                                                              |

**Contraintes clés** :
- `CHECK ((niveau='localite' AND type_localite IS NOT NULL) OR (niveau<>'localite' AND type_localite IS NULL))`
- `CHECK ((niveau='district' AND parent_id IS NULL) OR (niveau<>'district' AND parent_id IS NOT NULL))`
- `UNIQUE (parent_id, nom, niveau)`

**Index** : `idx_ref_geo_parent`, `idx_ref_geo_niveau`, `idx_ref_geo_nom_trgm` (GIN pg_trgm).

### 2.4 `localite`

| Colonne          | Type                   | Contrainte                                                                       |
|------------------|------------------------|----------------------------------------------------------------------------------|
| id_localite      | `serial`               | PK                                                                               |
| id_geo           | `integer`              | NOT NULL, FK → ref_geo_admin(id_geo), **trigger : niveau doit être 'localite'**  |
| nom_usage        | `varchar(150)`         | NOT NULL                                                                         |
| latitude_centre  | `double precision`     |                                                                                  |
| longitude_centre | `double precision`     |                                                                                  |
| geom_centre      | `geometry(Point,4326)` | GENERATED ALWAYS AS (geom_from_latlon(latitude_centre, longitude_centre)) STORED |
| commentaire      | `text`                 |                                                                                  |
| **metadata**     | **`jsonb`**            | **NOT NULL DEFAULT '{}'::jsonb**                                                 |
| created_at       | `timestamptz`          | NOT NULL DEFAULT now()                                                           |
| updated_at       | `timestamptz`          | NOT NULL DEFAULT now()                                                           |

**Index** : `idx_localite_geo`, `idx_localite_geom` (GiST), `idx_localite_nom_trgm` (GIN), `idx_localite_metadata` (GIN).

**Commentaire** : `metadata` stocke les attributs complémentaires non mappés de la localité (population, existence d'école, type d'habitat…).

### 2.5 `localite_alias`

| Colonne      | Type           | Contrainte                                             |
|--------------|----------------|--------------------------------------------------------|
| id_alias     | `serial`       | PK                                                     |
| id_localite  | `integer`      | NOT NULL, FK → localite(id_localite) ON DELETE CASCADE |
| alias        | `varchar(150)` | NOT NULL                                               |
| source_alias | `varchar(100)` |                                                        |
| —            | —              | UNIQUE (id_localite, alias)                            |

**Index** : `idx_alias_trgm` (GIN pg_trgm).

### 2.6 `fichier`

| Colonne              | Type           | Contrainte                                                                                    |
|----------------------|----------------|-----------------------------------------------------------------------------------------------|
| id_fichier           | `bigserial`    | PK                                                                                            |
| id_source            | `integer`      | NOT NULL, FK → source(id_source) ON DELETE RESTRICT                                           |
| nom_fichier_original | `varchar(255)` | NOT NULL                                                                                      |
| chemin_stockage      | `text`         | NOT NULL                                                                                      |
| hash_sha256          | `char(64)`     | **PAS UNIQUE**                                                                                |
| taille_octets        | `bigint`       |                                                                                               |
| date_reception       | `timestamptz`  | NOT NULL DEFAULT now()                                                                        |
| date_ingestion       | `timestamptz`  |                                                                                               |
| statut               | `varchar(20)`  | NOT NULL DEFAULT 'en_attente', CHECK IN ('en_attente','en_cours','ingere','partiel','erreur') |
| nb_feuilles          | `integer`      | DEFAULT 0                                                                                     |
| nb_lignes_total      | `integer`      | DEFAULT 0                                                                                     |
| est_reingestion      | `boolean`      | NOT NULL DEFAULT false                                                                        |
| commentaire          | `text`         |                                                                                               |
| created_at           | `timestamptz`  | NOT NULL DEFAULT now()                                                                        |
| updated_at           | `timestamptz`  | NOT NULL DEFAULT now()                                                                        |

**Index** : `idx_fichier_source`, `idx_fichier_date`, `idx_fichier_hash` (simple, non unique).

### 2.7 `feuille`

| Colonne           | Type           | Contrainte                                                                                    |
|-------------------|----------------|-----------------------------------------------------------------------------------------------|
| id_feuille        | `bigserial`    | PK                                                                                            |
| id_fichier        | `bigint`       | NOT NULL, FK → fichier(id_fichier) ON DELETE CASCADE                                          |
| nom_feuille       | `varchar(150)` | NOT NULL                                                                                      |
| index_feuille     | `integer`      | NOT NULL                                                                                      |
| type_contenu      | `varchar(20)`  | NOT NULL DEFAULT 'inconnu', CHECK IN ('ouvrages','cgpe','mixte','autre','inconnu')            |
| nb_lignes         | `integer`      | DEFAULT 0                                                                                     |
| nb_lignes_valides | `integer`      | DEFAULT 0                                                                                     |
| statut_ingestion  | `varchar(20)`  | NOT NULL DEFAULT 'en_attente', CHECK IN ('en_attente','en_cours','ingere','partiel','erreur') |
| message_erreur    | `text`         |                                                                                               |
| created_at        | `timestamptz`  | NOT NULL DEFAULT now()                                                                        |
| —                 | —              | UNIQUE (id_fichier, index_feuille)                                                            |

**Index** : `idx_feuille_fichier`.

### 2.8 `ingestion_run`

| Colonne            | Type          | Contrainte                                                                     |
|--------------------|---------------|--------------------------------------------------------------------------------|
| id_run             | `bigserial`   | PK                                                                             |
| id_fichier         | `bigint`      | NOT NULL, FK → fichier(id_fichier) ON DELETE CASCADE                           |
| id_feuille         | `bigint`      | FK → feuille(id_feuille) ON DELETE CASCADE, NULL = toutes                      |
| mode               | `varchar(20)` | NOT NULL DEFAULT 'complet', CHECK IN ('complet','echantillon','plage')         |
| limite_lignes      | `integer`     |                                                                                |
| ligne_debut        | `integer`     |                                                                                |
| ligne_fin          | `integer`     |                                                                                |
| nb_lignes_ingerees | `integer`     | DEFAULT 0                                                                      |
| statut             | `varchar(20)` | NOT NULL DEFAULT 'en_cours', CHECK IN ('en_cours','termine','erreur','annule') |
| message            | `text`        |                                                                                |
| started_at         | `timestamptz` | NOT NULL DEFAULT now()                                                         |
| finished_at        | `timestamptz` |                                                                                |

**CHECK métier** :
```sql
CHECK (
  (mode = 'complet'     AND limite_lignes IS NULL AND ligne_debut IS NULL AND ligne_fin IS NULL)
  OR (mode = 'echantillon' AND limite_lignes IS NOT NULL AND ligne_debut IS NULL AND ligne_fin IS NULL)
  OR (mode = 'plage'       AND limite_lignes IS NULL AND ligne_debut IS NOT NULL AND ligne_fin IS NOT NULL
                           AND ligne_fin >= ligne_debut)
)
```

**Index** : `idx_run_fichier`, `idx_run_feuille`, `idx_run_statut`.

### 2.9 `ligne_ingeree`

| Colonne               | Type                   | Contrainte                                                                                                                      |
|-----------------------|------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| id_ligne              | `bigserial`            | PK                                                                                                                              |
| id_feuille            | `bigint`               | NOT NULL, FK → feuille(id_feuille) ON DELETE CASCADE                                                                            |
| id_run                | `bigint`               | FK → ingestion_run(id_run) ON DELETE SET NULL                                                                                   |
| num_ligne_source      | `integer`              | NOT NULL                                                                                                                        |
| donnees_brutes        | `jsonb`                | NOT NULL                                                                                                                        |
| district_brut         | `varchar(150)`         |                                                                                                                                 |
| region_brute          | `varchar(150)`         |                                                                                                                                 |
| departement_brut      | `varchar(150)`         |                                                                                                                                 |
| sous_prefecture_brute | `varchar(150)`         |                                                                                                                                 |
| localite_brute        | `varchar(150)`         |                                                                                                                                 |
| type_localite_brut    | `varchar(30)`          |                                                                                                                                 |
| latitude_decimal      | `double precision`     |                                                                                                                                 |
| longitude_decimal     | `double precision`     |                                                                                                                                 |
| geom                  | `geometry(Point,4326)` | GENERATED ALWAYS AS (geom_from_latlon(latitude_decimal, longitude_decimal)) STORED                                              |
| type_ouvrage_brut     | `varchar(50)`          |                                                                                                                                 |
| etat_ouvrage_brut     | `varchar(50)`          |                                                                                                                                 |
| annee_projet          | `integer`              |                                                                                                                                 |
| bailleur_brut         | `varchar(150)`         |                                                                                                                                 |
| type_financement_brut | `varchar(50)`          |                                                                                                                                 |
| a_cgpe                | `boolean`              |                                                                                                                                 |
| statut_qualite        | `varchar(30)`          | NOT NULL DEFAULT 'ok', CHECK IN ('ok','localite_non_resolue','geom_invalide','type_ouvrage_inconnu','rejete','doublon_suspect') |
| message_qualite       | `text`                 |                                                                                                                                 |
| id_localite           | `integer`              | FK → localite(id_localite) ON DELETE SET NULL                                                                                   |
| id_ouvrage_consolide  | `bigint`               | FK → ouvrage(id_ouvrage) ON DELETE SET NULL                                                                                     |
| created_at            | `timestamptz`          | NOT NULL DEFAULT now()                                                                                                          |
| —                     | —                      | **UNIQUE (id_run, num_ligne_source)**                                                                                           |

**Index** : `idx_ligne_feuille`, `idx_ligne_run`, `idx_ligne_geom` (GiST), `idx_ligne_statut_qualite`, `idx_ligne_localite`, `idx_ligne_type_ouvrage`, `idx_ligne_donnees_brutes` (GIN jsonb), `idx_ligne_ouvrage`.

> **Point clé** : `UNIQUE (id_run, num_ligne_source)` remplace `UNIQUE (id_feuille, num_ligne_source)` → permet plusieurs runs sur la même feuille.

### 2.10 `ouvrage`

| Colonne           | Type                   | Contrainte                                                                            |
|-------------------|------------------------|---------------------------------------------------------------------------------------|
| id_ouvrage        | `bigserial`            | PK                                                                                    |
| code_ouvrage      | `varchar(100)`         | **nullable, non unique**                                                              |
| id_localite       | `integer`              | NOT NULL, FK → localite(id_localite) ON DELETE RESTRICT                               |
| id_type_ouvrage   | `integer`              | NOT NULL, FK → type_ouvrage(id_type_ouvrage) ON DELETE RESTRICT                       |
| etat              | `varchar(20)`          | NOT NULL DEFAULT 'inconnu', CHECK IN ('fonctionnel','en_panne','abandonne','inconnu') |
| annee_realisation | `integer`              |                                                                                       |
| latitude_decimal  | `double precision`     |                                                                                       |
| longitude_decimal | `double precision`     |                                                                                       |
| geom              | `geometry(Point,4326)` | GENERATED ALWAYS AS (geom_from_latlon(latitude_decimal, longitude_decimal)) STORED    |
| commentaire       | `text`                 |                                                                                       |
| **metadata**      | **`jsonb`**            | **NOT NULL DEFAULT '{}'::jsonb**                                                      |
| created_at        | `timestamptz`          | NOT NULL DEFAULT now()                                                                |
| updated_at        | `timestamptz`          | NOT NULL DEFAULT now()                                                                |

**Index** : `idx_ouvrage_localite`, `idx_ouvrage_type`, `idx_ouvrage_geom` (GiST), `idx_ouvrage_etat`, `idx_ouvrage_code` (partiel), `idx_ouvrage_metadata` (GIN).

### 2.11 `cgpe`

| Colonne       | Type          | Contrainte                                                     |
|---------------|---------------|----------------------------------------------------------------|
| id_cgpe       | `serial`      | PK                                                             |
| id_localite   | `integer`     | NOT NULL, FK → localite(id_localite) ON DELETE CASCADE         |
| id_ouvrage    | `bigint`      | FK → ouvrage(id_ouvrage) ON DELETE SET NULL                    |
| existe        | `boolean`     | NOT NULL DEFAULT true                                          |
| date_creation | `date`        |                                                                |
| statut        | `varchar(20)` | CHECK (NULL ou IN ('fonctionnel','non_fonctionnel','inconnu')) |
| nb_membres    | `integer`     |                                                                |
| commentaire   | `text`        |                                                                |
| **metadata**  | **`jsonb`**   | **NOT NULL DEFAULT '{}'::jsonb**                               |
| created_at    | `timestamptz` | NOT NULL DEFAULT now()                                         |
| updated_at    | `timestamptz` | NOT NULL DEFAULT now()                                         |

**Index** : `idx_cgpe_localite`, `idx_cgpe_ouvrage`, `idx_cgpe_metadata` (GIN).

### 2.12 `projet_financement`

| Colonne             | Type            | Contrainte                                                  |
|---------------------|-----------------|-------------------------------------------------------------|
| id_projet           | `bigserial`     | PK                                                          |
| nom_projet          | `varchar(255)`  | NOT NULL                                                    |
| annee               | `integer`       |                                                             |
| id_source_financeur | `integer`       | NOT NULL, FK → source(id_source) ON DELETE RESTRICT         |
| type_financement    | `varchar(20)`   | NOT NULL, CHECK IN ('etat','prive','partenariat','inconnu') |
| montant             | `numeric(18,2)` |                                                             |
| devise              | `char(3)`       | DEFAULT 'XOF'                                               |
| commentaire         | `text`          |                                                             |
| created_at          | `timestamptz`   | NOT NULL DEFAULT now()                                      |
| updated_at          | `timestamptz`   | NOT NULL DEFAULT now()                                      |

**Index** : `idx_projet_source`, `idx_projet_annee`.

### 2.13 `ouvrage_projet`

| Colonne          | Type          | Contrainte                                                            |
|------------------|---------------|-----------------------------------------------------------------------|
| id_ouvrage       | `bigint`      | NOT NULL, FK → ouvrage(id_ouvrage) ON DELETE CASCADE                  |
| id_projet        | `bigint`      | NOT NULL, FK → projet_financement(id_projet) ON DELETE CASCADE        |
| role_financement | `varchar(20)` | NOT NULL DEFAULT 'principal', CHECK IN ('principal','co_financement') |
| —                | —             | **PK (id_ouvrage, id_projet)**                                        |

**Index** : `idx_ouvrage_projet_projet`.

---

## 3. Fonctions & triggers

**Fonction pure** :
```sql
CREATE OR REPLACE FUNCTION geom_from_latlon(lat double precision, lon double precision)
RETURNS geometry(Point,4326) AS $$
BEGIN
    IF lat IS NULL OR lon IS NULL
       OR lat < -90 OR lat > 90
       OR lon < -180 OR lon > 180
       OR (lat = 0 AND lon = 0) THEN
        RETURN NULL;
    END IF;
    RETURN ST_SetSRID(ST_MakePoint(lon, lat), 4326);
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;
```

**Trigger de cohérence `localite.id_geo`** :
```sql
CREATE OR REPLACE FUNCTION trg_check_localite_geo() RETURNS trigger AS $$
DECLARE v_niveau varchar(20);
BEGIN
    SELECT niveau INTO v_niveau FROM ref_geo_admin WHERE id_geo = NEW.id_geo;
    IF v_niveau IS DISTINCT FROM 'localite' THEN
        RAISE EXCEPTION 'localite.id_geo doit référencer un ref_geo_admin de niveau localite (reçu: %)', v_niveau;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_localite_geo
BEFORE INSERT OR UPDATE OF id_geo ON localite
FOR EACH ROW EXECUTE FUNCTION trg_check_localite_geo();
```

**Trigger `updated_at` générique** : sur `source`, `ref_geo_admin`, `localite`, `fichier`, `ouvrage`, `cgpe`, `projet_financement`.

**Extensions** :
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- postgis_topology : NON retenu pour le MVP
```

### 3.4 Export Excel / CSV

L'export tabulaire (Excel, CSV) **n'ajoute aucune vue SQL dédiée**.

Il s'appuie sur une requête équivalente à `v_points_consolides`, mais avec :
- un `SELECT` tabulaire (pas de colonne `geom`)
- un `JOIN` optionnel sur `cgpe` (via `ouvrage.id_ouvrage`)
- un `JOIN` optionnel sur `ouvrage_projet` + `projet_financement` (concaténation
  des financements)
- un streaming applicatif (`yield_per(5000)` côté SQLAlchemy + `openpyxl`
  en mode `write_only`)

**Limite** : `MAX_EXPORT_ROWS` (variable d'environnement, défaut 100 000).
Au-delà → HTTP 413 (Problem Details), l'utilisateur est invité à affiner ses filtres.

**Colonnes exportées (MVP, figées)** :

| Colonne           | Source                                                       |
|-------------------|--------------------------------------------------------------|
| id_ouvrage        | ouvrage.id_ouvrage                                           |
| code_ouvrage      | ouvrage.code_ouvrage                                         |
| type_ouvrage      | type_ouvrage.code                                            |
| etat              | ouvrage.etat                                                 |
| annee_realisation | ouvrage.annee_realisation                                    |
| district          | ref_geo_admin (niveau district)                              |
| region            | ref_geo_admin (niveau region)                                |
| departement       | ref_geo_admin (niveau departement)                           |
| sous_prefecture   | ref_geo_admin (niveau sous_prefecture)                       |
| localite          | localite.nom_usage                                           |
| latitude          | ouvrage.latitude_decimal                                     |
| longitude         | ouvrage.longitude_decimal                                    |
| cgpe_existe       | cgpe.existe                                                  |
| cgpe_statut       | cgpe.statut                                                  |
| financements      | concaténation "nom_projet (bailleur, role)" séparés par "; " |
| metadata_*        | une colonne par clé de metadata (si `include=metadata`)      |

**Paramètre `?columns=`** accepté côté back (liste séparée par virgule),
mais non exposé dans l'UI au MVP.

---

## 4. Garanties du schéma

| Garantie                                              | Mécanisme                                                                                         |
|-------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| Géométrie toujours cohérente                          | Colonne `GENERATED ALWAYS` + `geom_from_latlon`                                                   |
| Pas de lat/lon aberrantes                             | Rejet bornes + (0,0) dans la fonction                                                             |
| Pas de localité rattachée à un nœud non-localité      | Trigger `check_localite_geo`                                                                      |
| Pas de district avec parent, ni de région sans parent | CHECK `chk_ref_geo_parent`                                                                        |
| `type_localite` uniquement au niveau localité         | CHECK `chk_ref_geo_type_localite`                                                                 |
| Paramètres de run cohérents                           | CHECK `chk_run_mode_params`                                                                       |
| Plusieurs runs sur la même feuille possibles          | `UNIQUE (id_run, num_ligne_source)`                                                               |
| Réingestion d'un même fichier possible                | `hash_sha256` non unique                                                                          |
| `code_ouvrage` optionnel                              | Colonne nullable + index partiel                                                                  |
| Traçabilité ligne Excel                               | `num_ligne_source` + `donnees_brutes jsonb`                                                       |
| **Capturer les données non mappées**                  | `localite.metadata`, `ouvrage.metadata`, `cgpe.metadata` (jsonb) + `ligne_ingeree.donnees_brutes` |
| `updated_at` toujours à jour                          | Trigger générique sur 7 tables                                                                    |
| Export tabulaire streamé                              | `yield_per(5000)` + `openpyxl` write_only, limite `MAX_EXPORT_ROWS`                               |

---

## 5. Ce qui n'est pas dans ce schéma (volontairement)

| Élément                                                           | Raison                    | Quand l'ajouter                             |
|-------------------------------------------------------------------|---------------------------|---------------------------------------------|
| `localite.metadata_sources` (traçabilité fine)                    | V2                        | Si besoin de tracer l'origine de chaque clé |
| `ouvrage.metadata_sources`                                        | V2                        | Idem                                        |
| `cgpe.metadata_sources`                                           | V2                        | Idem                                        |
| `attribut_definition` + `ouvrage_attribut` (promotion d'un champ) | V2, sur-ingénierie au MVP | Si un champ `metadata` devient critique     |
| Partitionnement de `ligne_ingeree`                                | Inutile au MVP            | Si volume > quelques millions               |
| Table `utilisateur`                                               | Config au MVP             | V2                                          |
| Versioning/historique                                             | V2                        | V2                                          |

---

## 6. Historique des versions

| Version | Date       | Changement                                                                                            |
|---------|------------|-------------------------------------------------------------------------------------------------------|
| 1.0     | 2026-10-23 | Version initiale (MCDR + MLDR + schema.sql)                                                           |
| 1.1     | 2026-10-23 | Ajout `metadata jsonb` sur `localite`, `ouvrage`, `cgpe` + index GIN + `docs/metadata_conventions.md` |
| 1.2     | 2026-10-26 | Ajout export Excel/CSV (endpoints `GET /ouvrages/export` et `GET /ouvrages/export.csv`)               |
