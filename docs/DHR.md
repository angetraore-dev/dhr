
---

# Bible du projet DHR

---

**Version** : 1.0 
**Date de démarrage** : 2026-11-09
**Objet** : Document de référence unique du projet DHR. Fait autorité sur toutes les autres sources (handoffs, docs techniques, code).
**Statut** : rédaction en cours, section 1 validée.

---

# Mise à jour de la Table des matières — Bible v1.0

J'ai relu l'état actuel. Il reste **3 corrections** à faire sur la ToC pour qu'elle soit cohérente avec le contenu (sections 6 et 8 écrites, ADR numérotés ADR-001 → ADR-018 dans le corps, sous-sections 8.1 → 8.9 à ajouter). Voici le bloc à remplacer **intégralement**.

---

## Table des matières

1. [Contexte métier](#1-contexte-métier)
    - 1.1 [La Maitrise d'Ouvrage (MOA)](#11-la-maitrise-douvrage-moa)
    - 1.2 [Le problème actuel](#12-le-problème-actuel)
    - 1.3 [Le MVP — périmètre](#13-le-mvp--périmètre)
    - 1.4 [Décisions structurantes](#14-décisions-structurantes)
    - 1.5 [Glossaire métier](#15-glossaire-métier)
    - 1.6 [Contraintes connues](#16-contraintes-connues)
2. [Modèle de données](#2-modèle-de-données)
    - 2.1 [Vue d'ensemble et principes](#21-vue-densemble-et-principes)
    - 2.2 [Dictionnaire des tables](#22-dictionnaire-des-tables)
    - 2.3 [Règles métier transverses](#23-règles-métier-transverses)
3. [Pipeline d'ingestion](#3-pipeline-dingestion)
    - 3.1 [Vue d'ensemble et les 5 étapes](#31-vue-densemble-et-les-5-étapes)
    - 3.2 [Détail de chaque étape](#32-détail-de-chaque-étape)
4. [Contrat d'API](#4-contrat-dapi)
    - 4.1 [Principes généraux](#41-principes-généraux)
    - 4.2 [Authentification](#42-authentification)
    - 4.3 [Liste des endpoints](#43-liste-des-endpoints-27)
    - 4.4 [Codes d'erreur](#44-codes-derreur)
    - 4.5 [Schémas clés (résumé)](#45-schémas-clés-résumé)
    - 4.6 [Écarts avec l'openapi.yaml](#46-écarts-avec-lopenapiyaml-à-corriger-en-phase-d)
    - 4.7 [Ce qui n'est pas dans l'API au MVP](#47-ce-qui-nest-pas-dans-lapi-au-mvp)
5. [Frontend](#5-frontend)
    - 5.1 [Stack et architecture](#51-stack-et-architecture)
    - 5.2 [Client API (src/lib/api.ts)](#52-client-api-srclibapits)
    - 5.3 [Authentification (MVP)](#53-authentification-mvp)
    - 5.4 [Pages](#54-pages)
    - 5.5 [Composants clés](#55-composants-clés)
    - 5.6 [Règles de rendu carto](#56-règles-de-rendu-carto)
    - 5.7 [Règles UX transverses](#57-règles-ux-transverses)
    - 5.8 [Frontend hors scope (V2)](#58-frontend-hors-scope-v2)
    - 5.9 [Écarts code ↔ Bible (frontend, à corriger en Phase D)](#59-écarts-code--bible-frontend-à-corriger-en-phase-d)
6. [Décisions d'architecture (ADR)](#6-décisions-darchitecture-adr)
    - 6.1 [ADR-001 — PostgreSQL + PostGIS](#adr-001--postgresql--postgis)
    - 6.2 [ADR-002 — JSONB pour les attributs non mappés](#adr-002--jsonb-pour-les-attributs-non-mappés)
    - 6.3 [ADR-003 — Colonnes générées pour `geom`](#adr-003--colonnes-générées-pour-geom)
    - 6.4 [ADR-004 — Trigram + unaccent pour le rapprochement](#adr-004--trigram--unaccent-pour-le-rapprochement)
    - 6.5 [ADR-005 — `serial` / `bigserial` (pas d'UUID)](#adr-005--serial--bigserial-pas-duuid)
    - 6.6 [ADR-006 — FastAPI + SQLAlchemy 2.0 + Pydantic 2](#adr-006--fastapi--sqlalchemy-20--pydantic-2)
    - 6.7 [ADR-007 — React + Vite + TypeScript + shadcn/ui](#adr-007--react--vite--typescript--shadcnui)
    - 6.8 [ADR-008 — Leaflet + Esri World Imagery](#adr-008--leaflet--esri-world-imagery)
    - 6.9 [ADR-009 — TanStack Query](#adr-009--tanstack-query)
    - 6.10 [ADR-010 — Authentification MVP = API key + JWT manuel](#adr-010--authentification-mvp--api-key--jwt-manuel)
    - 6.11 [ADR-011 — Pagination offset + cursor](#adr-011--pagination-offset--cursor)
    - 6.12 [ADR-012 — RFC 7807 pour les erreurs](#adr-012--rfc-7807-pour-les-erreurs)
    - 6.13 [ADR-013 — `metadata.<entité>.<clé>` pour les attributs explicites](#adr-013--metadataentitéclé-pour-les-attributs-explicites)
    - 6.14 [ADR-014 — Suppression de `type_ouvrage` (refactoring sémantique)](#adr-014--suppression-de-type_ouvrage-refactoring-sémantique)
    - 6.15 [ADR-015 — 6 statuts de qualité (règles conservatrices)](#adr-015--6-statuts-de-qualité-règles-conservatrices)
    - 6.16 [ADR-016 — Dédoublonnage par `code_ouvrage` puis tuple](#adr-016--dédoublonnage-par-code_ouvrage-puis-tuple)
    - 6.17 [ADR-017 — Pas de filtre `district`](#adr-017--pas-de-filtre-district)
    - 6.18 [ADR-018 — Migration initiale unique](#adr-018--migration-initiale-unique)
7. [Dette technique et points ouverts](#7-dette-technique-et-points-ouverts)
8. [Méthodologie de travail](#8-méthodologie-de-travail)
    - 8.1 [Conventions de code](#81-conventions-de-code)
    - 8.2 [Architecture cible](#82-architecture-cible)
    - 8.3 [Tests](#83-tests)
    - 8.4 [CI/CD (GitHub Actions)](#84-cicd-github-actions)
    - 8.5 [Workflow de contribution](#85-workflow-de-contribution)
    - 8.6 [Phases du projet](#86-phases-du-projet)
    - 8.7 [Commandes utiles](#87-commandes-utiles)
    - 8.8 [Points de coordination](#88-points-de-coordination)
    - 8.9 [Hors scope (V2)](#89-hors-scope-v2)

---

## 1. Contexte métier

### 1.1 La Maitrise d'Ouvrage (MOA)

La **Direction de l'Hydraulique Rurale (DHR)** est l'entité publique ivoirienne chargée du suivi des ouvrages hydrauliques en zone rurale. Elle doit connaître, pour chaque ouvrage, sa localisation, son état, son mode d'alimentation, sa nature, et les éventuels comités de gestion (CGPE) qui en assurent l'exploitation.

### 1.2 Le problème actuel

La DHR reçoit des fichiers Excel de **sources hétérogènes** :

- **ONEP** — Office National de l'Eau Potable (public)
- **SODECI** — Société de Distribution d'Eau de Côte d'Ivoire (privé)
- **UNICEF**, **BAD** — bailleurs internationaux
- **LONACI** — Loterie Nationale de Côte d'Ivoire (public)
- **État de Côte d'Ivoire** — Ministère de l'Hydraulique
- D'autres sources ponctuelles (projets, ONG, sociétés privées)

Ces fichiers n'ont **ni la même structure, ni les mêmes entêtes, ni la même qualité** :

- Colonnes nommées différemment (`Localité`, `Village`, `Q1.5. Localité/Campement`, `Nom_Village`...)
- Coordonnées en formats variables (décimal, DMS compact, DMS explicite, avec ou sans direction, avec virgule ou point, inversion lat/lon fréquente)
- Informations tantôt centralisées, tantôt éclatées en colonnes (`Q3.1.1h. Type de forage`, `Usage_Ouvrage`, `Type_Ouvrage`...)
- Certains fichiers contiennent des feuilles multiples par type d'ouvrage (`PMH`, `HVA`, `PEA`, `Autres_ouvrages`), d'autres une seule feuille
- Certains fichiers contiennent une feuille `Localités` avec la hiérarchie administrative et les coordonnées des villages (référentiel géographique)
- Qualité variable : coordonnées manquantes, localités mal orthographiées, doublons entre fichiers, données sanitaires (onchocercose, vers de Guinée, eau salée, etc.) présentes ou non

Aujourd'hui, la DHR n'a **pas de vision consolidée**. Elle veut :

- Une **base centralisée** PostgreSQL/PostGIS
- Une **UI cartographique** (vue satellite) pour visualiser les ouvrages
- Un **export Excel/CSV** filtrable
- Un **suivi de la qualité** des fichiers ingérés

### 1.3 Le MVP — périmètre

**Dans le scope :**

| Fonction                  | Description                                                                       |
|---------------------------|-----------------------------------------------------------------------------------|
| Lecture de fichiers Excel | Multi-feuilles, multi-sources, formats hétérogènes                                |
| Ingestion                 | Parsing, normalisation, stockage des données brutes en JSONB                      |
| Rapprochement             | Résolution `localité brute` → `localité du référentiel` (exact / alias / trigram) |
| Consolidation             | Création d'ouvrages dédoublonnés avec attributs normalisés                        |
| Cartographie              | Points sur fond satellite, filtres, popups                                        |
| Export                    | Excel (avec Synthèse KPI) + CSV, filtrable                                        |
| Qualité                   | Tableau de bord par fichier (lignes OK, non résolues, invalides, etc.)            |

**Hors scope du MVP :**

| Fonction                                                           | Raison                                                                                         |
|--------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| Création manuelle d'ouvrages dans l'UI                             | V2 — la DHR veut d'abord consolider l'existant                                                 |
| Analytique avancée (KPI historiques, tendances, cartes de chaleur) | V2 — pas de besoin exprimé                                                                     |
| Import automatique du référentiel localités                        | V2 — script CLI manuel suffit pour le MVP                                                      |
| Création manuelle de localités                                     | V2                                                                                             |
| Gestion complète des utilisateurs (rôles, permissions)             | V2 — MVP utilise un JWT manuel et une API key                                                  |
| Déploiement en production                                          | V2 — MVP tourne en local via Docker Compose                                                    |
| Application mobile                                                 | Hors scope                                                                                     |
| Filtre par district                                                | Obsolète après la réforme territoriale (sauf Abidjan/Yamoussoukro, non concernés par le rural) |

### 1.4 Décisions structurantes


Ces décisions sont actées et ne sont pas rediscutées à chaque sprint :

1. **Un ouvrage sans coordonnées GPS n'existe pas.** Il est marqué `statut_qualite='geom_invalide'` sur la ligne ingérée et **n'est pas consolidé** en ouvrage. Raison : un ouvrage sans géolocalisation ne peut pas apparaître sur la carte, qui est l'usage principal.

2. **Les localités sont importées manuellement** via un script CLI (`import_localites.py`) à partir d'une feuille `Localités`. L'import automatique sera V2.

3. **Trois champs distincts pour qualifier un ouvrage**, et non un seul :
    - `nature_ouvrage` : `puits` | `forage` | `inconnu` — **nature physique**
    - `type_alimentation` : `PMH` | `HVA` | `PEA` | `HV` | `AUTRE` — **mode d'alimentation en eau**
    - `realisation_par` : `public` | `prive` | `inconnu` — **qui a réalisé**

   Cette séparation résout la confusion historique où `type_ouvrage` mélangeait les trois (ex. `"Forage ADM"` = nature forage + réalisation publique).

4. **Les attributs non mappés vont en JSONB**, pas en colonnes. Sur `ouvrage.metadata`, `localite.metadata`, `cgpe.metadata`. Convention de nommage : `brut_<entête Excel d'origine>`. Cela permet de conserver la donnée d'origine sans figer le schéma à chaque nouveau fichier.

5. **Les données sanitaires (qualité de l'eau, maladies hydriques) vont dans un champ dédié** `ouvrage.qualite_eau` de type JSONB, **nullable** (tous les fichiers n'en ont pas). Structure mixte : clés normalisées (`onchocercose`, `vers_de_guinee`, `eau_salee`...) + clés brutes (`brut_<entête>`). Ce champ est distinct de `metadata` pour permettre des requêtes et des index ciblés.

6. **Pas de filtre "district"** dans l'UI. La réforme territoriale ivoirienne a supprimé les districts sauf Abidjan et Yamoussoukro, qui ne sont pas concernés par l'hydraulique rurale. Le filtre géographique se fait par **région → département → sous-préfecture → localité**.
    - **Exception** : le **KPI `par_district`** est conservé dans la feuille Synthèse de l'export Excel (information utile pour la DHR). Ce n'est **pas** un filtre UI, c'est une agrégation en lecture seule. Les endpoints `/ouvrages`, `/ouvrages/export`, `/ouvrages/export.csv`, `/carto/tous/points` n'exposent **pas** de query param `district`.

7. **Le mapping des colonnes est proposé automatiquement, mais l'utilisateur peut le corriger** via l'UI. Chaque colonne Excel peut être affectée à :
    - Un champ cible standard (`region_brute`, `localite_brute`, `latitude_decimal`...)
    - Un champ cible ouvrage (`nature_ouvrage`, `type_alimentation`...)
    - Une clé libre de métadonnées (qui ira en `metadata` ou `qualite_eau`)
    - "Ignorer" (la colonne ne sera pas conservée)

8. **Le projet repart sur des bases saines, guidé par la Bible**.
   La Bible est la spécification cible. Le `schema.sql`, la base, les migrations et le code sont réécrits pour y correspondre. 
   Aucune dette technique n'est conservée par compatibilité avec l'existant. **Une migration initiale unique** remplacera l'historique des migrations.
 
9. **Les 6 statuts de qualité sont implémentés au MVP.**
   * `'ok'`, `'geom_invalide'`, `'localite_non_resolue'`, `'type_ouvrage_inconnu'`, `'rejete'`, `'doublon_suspect'` ont chacun une règle précise (**cf. section 3.1.6**). 
   * Les règles sont conçues pour être **conservatrices** : on ne rejette que ce qui est manifestement inexploitable (lignes de total, coordonnées invalides), et on ne signale que ce qui est **probablement** une erreur (doublons avec coordonnées très différentes). Les lignes valides mais aux attributs incomplets ne sont pas rejetées : elles sont consolidées et marquées `'type_ouvrage_inconnu'` pour être requalifiées en V2.

10. **Les métadonnées explicites sont possibles via** `mapping_feuille.champ_cible`. En plus des champs cibles standard et de `NULL`,
   **une colonne peut être mappée vers** `metadata.ouvrage.<clé>`, `metadata.localite.<clé>` ou `metadata.cgpe.<clé>`. **La valeur est alors stockée dans le metadata de l'entité consolidée**, **sous la clé explicite** (`snake_case`, documentée dans `metadata_conventions.md`). 
   La valeur brute reste toujours dans `donnees_brutes` et dans `metadata.brut_<entête>` (**traçabilité**). **Cette fonctionnalité permet à l'utilisateur de créer des attributs métier stables sans attendre une migration** (V2 : promotion en attribut de première classe via `attribut_definition` + `ouvrage_attribut`).


### 1.5 Glossaire métier

| Terme                         | Définition                                                                                                                                                                                                                               |
|-------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Ouvrage**                   | Un point d'eau (puits ou forage) équipé pour l'extraction. Un ouvrage consolidé est unique dans la base, dédoublonné entre fichiers.                                                                                                     |
| **Nature**                    | `puits` ou `forage`. C'est la nature physique du point d'eau.                                                                                                                                                                            |
| **Alimentation**              | Le mode d'extraction / d'adduction. `PMH` = Pompe à motricité humaine, `HVA` = Hydraulique villageoise améliorée, `HV` = Hydraulique villageoise, `PEA` = Poste d'eau autonome, `AUTRE`.                                                 |
| **Réalisation**               | Qui a réalisé l'ouvrage : `public` (État, ONEP, commune...) ou `prive` (particulier, SODECI, ONG...).                                                                                                                                    |
| **CGPE**                      | Comité de Gestion de Point d'Eau. Association villageoise qui gère l'ouvrage. Peut être `fonctionnel`, `non_fonctionnel` ou `inconnu`.                                                                                                   |
| **Localité**                  | Village ou campement, rattaché à un nœud de niveau `localite` dans la hiérarchie administrative.                                                                                                                                         |
| **Référentiel administratif** | Hiérarchie `district → région → département → sous-préfecture → localité` stockée dans `ref_geo_admin`.                                                                                                                                  |
| **Rapprochement**             | Processus qui résout un `localite_brute` (texte libre extrait d'un fichier) vers un `id_localite` du référentiel.                                                                                                                        |
| **Consolidation**             | Processus qui transforme les `ligne_ingeree` (lignes brutes) en `ouvrage` (entités uniques et dédoublonnées).                                                                                                                            |
| **Ingestion**                 | Processus de lecture d'un fichier Excel et d'insertion des lignes brutes dans `ligne_ingeree`.                                                                                                                                           |
| **Source**                    | Émetteur du fichier : ONEP, SODECI, UNICEF, BAD, LONACI, État de Côte d'Ivoire, etc.                                                                                                                                                     |
| **Bailleur**                  | Terme parfois utilisé pour "source", parfois pour "financeur d'un projet". Dans la base, `source.type_source` distingue `public`, `prive`, `bailleur`, `etat`, `autre`.                                                                  |
| **Ligne ingérée**             | Une ligne d'Excel, stockée brute en JSONB + quelques champs normalisés (coordonnées, localité, etc.).                                                                                                                                    |
| **Ligne consolidée**          | Une ligne ingérée qui a abouti à un `ouvrage`. On la marque via `ligne_ingeree.id_ouvrage_consolide`.                                                                                                                                    |
| **`statut_qualite`**          | État d'une ligne ingérée : `ok`, `localite_non_resolue`, `geom_invalide`, `type_ouvrage_inconnu`, `rejete`, `doublon_suspect`.                                                                                                           |
| **Puits**                     | Excavation verticale, généralement peu profonde.                                                                                                                                                                                         |
| **Forage**                    | Forage mécanique, généralement plus profond, souvent équipé d'une pompe.                                                                                                                                                                 |
| **usage_ouvrage_brut**        | valeur brute d'une colonne décrivant l'usage / le type d'alimentation d'un ouvrage ("`Hydraulique villageoise`", `"Point d'eau autonome`"...). Extraite à l'ingestion, interprétée à la consolidation pour produire `type_alimentation`. |


### 1.6 Contraintes connues

1. **Les fichiers ONEP** contiennent une colonne `Type_Ouvrage` (ex. `"Forage ADM"`, `"Sondage"`) qui mélange nature et réalisation. Il faut la décortiquer (nature = forage, réalisation = public si `ADM` / `Administratif`).

2. **Les fichiers DHR classiques** peuvent contenir une feuille `Localités` (référentiel) et des feuilles `PMH`, `HVA`, `PEA`, `Autres_ouvrages` (ouvrages). L'alimentation est alors déduite du **nom de la feuille**, plus fiable que la colonne.

3. **Les coordonnées GPS** sont fournies dans des formats très variables. Cas problématiques observés :
    - DMS compact (`075225` = 07°52'25" W, mais sans indication de direction → il faut **forcer le signe** de la longitude en Côte d'Ivoire : lat ∈ [4, 11], lon ∈ [-9, -2])
    - Inversion lat/lon (colonne `Latitude` contient en réalité la longitude et vice-versa)
    - Virgule décimale française (`7,0291`)
    - Point décimal anglo-saxon (`7.0291`)

4. **Certains fichiers contiennent des colonnes sanitaires** (`Onchocercose`, `Vers_Guinee`, `Bilharziose`, `Eau_Salee`...), d'autres pas. Le champ `ouvrage.qualite_eau` reste `NULL` pour les fichiers qui n'en ont pas.

5. **Certains fichiers contiennent des informations CGPE** (existence, statut, nombre de membres, date de création), d'autres pas. Un CGPE peut ne pas être lié à un ouvrage précis (il est toujours lié à une localité).

6. **Le rapprochement des localités n'est pas parfait.** Le trigram (similarité > 0,6) rattrape les fautes de frappe mais peut produire des faux positifs. Une partie des lignes reste `localite_non_resolue`. C'est accepté pour le MVP.

7. **Le dédoublonnage des ouvrages** repose sur deux critères :
    - Priorité 1 : `code_ouvrage` identique
    - Priorité 2 : même `(id_localite, nature_ouvrage, type_alimentation, annee_realisation)`

   Les doublons non détectés sont acceptés pour le MVP. Un mécanisme de résolution manuelle est V2.

8. **La consolidation ne modifie pas les lignes déjà consolidées** (`id_ouvrage_consolide` non NULL). Pour rejouer la consolidation, il faut d'abord reset (`UPDATE ligne_ingeree SET id_ouvrage_consolide = NULL;` puis `DELETE FROM ouvrage;`).

---

## 2. Modèle de données

### 2.1 Vue d'ensemble et principes

#### 2.1.1 Les 4 groupes de tables

La base est organisée en 4 groupes fonctionnels, du plus statique au plus dynamique :

```text
┌─────────────────────────────────────────────────────────────────────┐
│  GROUPE A — RÉFÉRENTIELS                                            │
│                                                                     │
│  source           Émetteur de fichiers (ONEP, SODECI, UNICEF...)    │
│  ref_geo_admin    Hiérarchie administrative (district → localité)   │
│  localite         Village / campement rattaché à ref_geo_admin      │
│  localite_alias   Variantes de noms pour le rapprochement           │
└─────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────┐
│  GROUPE B — INGESTION                                               │
│                                                                     │
│  fichier          Fichier Excel uploadé                             │
│  feuille          Feuille d'un classeur Excel                       │
│  mapping_feuille  Mapping validé entête Excel → champ cible         │
│  ingestion_run    Exécution d'ingestion (paramètres + statut)       │
│  ligne_ingeree    Ligne brute normalisée issue d'une feuille        │
└─────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────┐
│  GROUPE C — MÉTIER CONSOLIDÉ                                        │
│                                                                     │
│  ouvrage          Point d'eau consolidé, dédoublonné                │
│  cgpe             Comité de gestion de point d'eau                  │
│  projet_financement  Projet de financement (bailleur, montant)      │
│  ouvrage_projet   Association N..N ouvrage ↔ projet                 │
└─────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────┐
│  GROUPE D — VUES (lecture seule)                                    │
│                                                                     │
│  v_points_par_fichier      Points bruts d'un fichier (carto)        │
│  v_points_consolides       Points consolidés (carto "Tous")         │
│  v_qualite_par_fichier     Tableau de bord qualité par fichier      │
└─────────────────────────────────────────────────────────────────────┘
```

**12 tables métier + 3 vues.** La table `alembic_version` (technique, gérée par Alembic) n'est pas comptée. La table `type_ouvrage`, qui existait dans les premières versions, **a été supprimée** lors du refactoring sémantique (Nature/Alimentation/Réalisation) ; elle ne fait plus partie du schéma cible. Le concept qu'elle portait est désormais éclaté en 3 colonnes sur `ouvrage` : `nature_ouvrage`, `type_alimentation`, `realisation_par`.

#### 2.1.2 Principes de conception

**P1 — Séparer le brut du métier.**
Une ligne d'Excel est d'abord stockée **telle quelle** dans `ligne_ingeree.donnees_brutes` (JSONB), avec quelques champs normalisés extraits (coordonnées, localité, type). Ce n'est qu'après **rapprochement** (résolution de la localité) et **consolidation** (dédoublonnage) qu'elle devient un `ouvrage`. Cette séparation permet de rejouer chaque étape sans réingérer.

**P2 — Tout ce qui n'est pas mappé vers un champ cible va en JSONB.**
`ouvrage.metadata`, `localite.metadata`, `cgpe.metadata` stockent les attributs non standardisés. Convention de nommage : `brut_<entête Excel d'origine>`. Exemple : `{"brut_Type_Pompe": "PMH VERGNET", "brut_Prof_Totale": 58.5}`.

La fonctionnalité **« ignorer une colonne »** dans l'UI est une fonctionnalité **V2** : pour le MVP, une colonne non mappée vers un champ cible va automatiquement en `metadata` (ou `qualite_eau` si elle matche un indicateur sanitaire). L'utilisateur peut décider de la mapper vers un autre champ cible, mais pas de la supprimer entièrement.

**P3 — Les coordonnées GPS sont calculées, pas stockées.**
`geom` (geometry Point,4326) est une **colonne générée** (`GENERATED ALWAYS AS geom_from_latlon(lat, lon) STORED`). On ne l'écrit jamais directement. Si `lat` ou `lon` est NULL, `geom` est NULL. La fonction `geom_from_latlon` rejette les bornes invalides (lat hors [-90, 90], lon hors [-180, 180], et `(0, 0)`).

**P4 — Un `ouvrage` est toujours rattaché à une `localite`.**
`ouvrage.id_localite` est `NOT NULL` avec `ON DELETE RESTRICT`. On ne peut pas supprimer une localité si des ouvrages y sont rattachés.

**P5 — Les attributs métier d'un ouvrage sont normalisés et contraints.**
- `nature_ouvrage` : `CHECK IN ('puits', 'forage', 'inconnu')`
- `type_alimentation` : `CHECK IN ('PMH', 'HVA', 'PEA', 'HV', 'AUTRE')`
- `realisation_par` : `CHECK IN ('public', 'prive', 'inconnu')`
- `etat` : `CHECK IN ('fonctionnel', 'en_panne', 'abandonne', 'inconnu')`

Ces contraintes vivent **en base**, pas seulement en Python. Cela garantit l'intégrité même en cas d'insertion directe par script.

**P6 — Les données sanitaires sont un champ JSONB dédié, nullable.**
`ouvrage.qualite_eau` (JSONB, nullable) contient les indicateurs sanitaires. Structure mixte : clés normalisées (`onchocercose`, `vers_de_guinee`, `eau_salee`...) + clés brutes (`brut_<entête>`). Nullable parce que tous les fichiers n'en contiennent pas. Distinct de `metadata` parce qu'on veut pouvoir indexer (GIN) et requêter dessus.

**P7 — Le dédoublonnage est explicite et rejouable.**
`ligne_ingeree.id_ouvrage_consolide` (FK nullable vers `ouvrage`) trace quelle ligne a produit quel ouvrage. NULL = pas encore consolidée. Pour rejouer la consolidation : `UPDATE ligne_ingeree SET id_ouvrage_consolide = NULL; DELETE FROM ouvrage;`.

**P8 — Les identifiants sont `serial` ou `bigserial`.**
Pas d'UUID. Pourquoi ? Les volumes sont modestes (quelques milliers à dizaines de milliers de lignes), les jointures SQL sont plus rapides sur des entiers, et le débogage manuel est plus simple avec des IDs courts.

**P9 — Les dates sont en `timestamptz`, pas en `timestamp`.**
Toutes les colonnes de date/heure sont `timestamp with time zone`. Le serveur et la base sont configurés en UTC. L'affichage local est fait côté UI.

**P10 — `updated_at` est maintenu par trigger.**
7 tables ont un trigger `set_updated_at` qui met `NEW.updated_at = now()` à chaque `UPDATE`. On ne gère pas ça en Python.

**P11 — Séparer le mapping (entête) de l'interprétation (contenu).**
Le `mapping-proposal` regarde **l'entête** d'une colonne (`Type_Ouvrage`, `Usage_Ouvrage`, `Localité`...) et propose un **champ cible** sur la base de patterns. Il ne se prononce **jamais** sur le contenu.

L'**interprétation du contenu** (ex. `"Hydraulique villageoise"` → `HV`, `"Forage ADM"` → `nature=forage` + `realisation=public`) est faite **à la consolidation**, par les fonctions `_map_nature`, `_map_alimentation`, `_map_realisation`.

Cette séparation garantit :
- La **traçabilité** : on peut voir quelle colonne a produit quelle valeur (via `ligne_ingeree.*_brut` et `donnees_brutes`).
- La **testabilité** : on peut tester le mapping et l'interprétation indépendamment.
- L'**évolutivité** : ajouter un nouveau fichier ne casse pas les mappings existants.

**P12 — Les concepts métier standardisés ont une colonne « brute » dédiée sur `ligne_ingeree`.**
Au-delà de `donnees_brutes` (qui stocke tout), `ligne_ingeree` contient des colonnes « brutes » extraites pour les concepts métier standardisés :
- `type_ouvrage_brut`
- `etat_ouvrage_brut`
- `bailleur_brut`
- `type_financement_brut`
- `usage_ouvrage_brut` *(nouveau)*

Ces colonnes sont remplies par l'ingestion à partir du mapping validé. Elles servent à la consolidation pour produire les attributs normalisés de `ouvrage`.

**Pourquoi une colonne dédiée plutôt que `donnees_brutes` ?** Pour trois raisons :
1. **Performance** : la consolidation peut lire ces colonnes par nom, sans parcourir tout le JSONB à chaque ligne.
2. **Normalisation** : plusieurs entêtes différents (`Usage_Ouvrage`, `Usage`, `Type_Alimentation`) peuvent pointer vers le même champ cible. La logique est centralisée.
3. **Traçabilité** : on peut exposer ces colonnes dans l'API qualité (V2) pour debugger.

`usage_ouvrage_brut` capte les colonnes du type `Usage_Ouvrage` (valeurs `"Hydraulique villageoise"`, `"Point d'eau autonome"`...) qui portent l'information d'alimentation sans être des noms de feuille ni des `type_ouvrage_brut`.

#### 2.1.3 Cardinalités principales

| Relation                                    | Cardinalité | Contrainte                                         |
|---------------------------------------------|-------------|----------------------------------------------------|
| `source` → `fichier`                        | 1..N        | `fichier.id_source NOT NULL`                       |
| `fichier` → `feuille`                       | 1..N        | `ON DELETE CASCADE`                                |
| `feuille` → `mapping_feuille`               | 0..N        | `ON DELETE CASCADE`                                |
| `fichier` → `ingestion_run`                 | 1..N        | `ON DELETE CASCADE`                                |
| `ingestion_run` → `ligne_ingeree`           | 0..N        | `ON DELETE SET NULL` (les lignes survivent au run) |
| `feuille` → `ligne_ingeree`                 | 1..N        | `ON DELETE CASCADE`                                |
| `ref_geo_admin` → `ref_geo_admin` (parent)  | 0..1 / 1..N | auto-référence, `ON DELETE RESTRICT`               |
| `ref_geo_admin` → `localite`                | 0..N        | `ON DELETE RESTRICT`                               |
| `localite` → `localite_alias`               | 0..N        | `ON DELETE CASCADE`                                |
| `localite` → `ouvrage`                      | 0..N        | `ON DELETE RESTRICT`                               |
| `localite` → `cgpe`                         | 0..N        | `ON DELETE CASCADE`                                |
| `localite` → `ligne_ingeree`                | 0..N        | `ON DELETE SET NULL`                               |
| `ouvrage` → `ligne_ingeree` (consolidation) | 0..N        | `ON DELETE SET NULL`                               |
| `ouvrage` → `cgpe`                          | 0..N        | `ON DELETE SET NULL`                               |
| `ouvrage` ↔ `projet_financement`            | 0..N / 0..N | via `ouvrage_projet`, `ON DELETE CASCADE`          |
| `source` → `projet_financement` (financeur) | 1..N        | `ON DELETE RESTRICT`                               |

#### 2.1.4 Choix d'identifiants et de clés

| Table                | PK                        | Clés naturelles / UNIQUE                                     |
|----------------------|---------------------------|--------------------------------------------------------------|
| `source`             | `id_source` (serial)      | `nom` UNIQUE                                                 |
| `ref_geo_admin`      | `id_geo` (serial)         | `(parent_id, nom, niveau)` UNIQUE                            |
| `localite`           | `id_localite` (serial)    | — (dédoublonnage géré par le rapprochement, pas par la base) |
| `localite_alias`     | `id_alias` (serial)       | `(id_localite, alias)` UNIQUE                                |
| `fichier`            | `id_fichier` (bigserial)  | `hash_sha256` **non** UNIQUE (réingestion légitime)          |
| `feuille`            | `id_feuille` (bigserial)  | `(id_fichier, index_feuille)` UNIQUE                         |
| `mapping_feuille`    | `id_mapping` (serial)     | `(id_feuille, entete_brut)` UNIQUE                           |
| `ingestion_run`      | `id_run` (bigserial)      | —                                                            |
| `ligne_ingeree`      | `id_ligne` (bigserial)    | `(id_feuille, id_run, num_ligne_source)` UNIQUE              |
| `ouvrage`            | `id_ouvrage` (bigserial)  | — (`code_ouvrage` nullable, non unique)                      |
| `cgpe`               | `id_cgpe` (serial)        | —                                                            |
| `projet_financement` | `id_projet` (bigserial)   | —                                                            |
| `ouvrage_projet`     | `(id_ouvrage, id_projet)` | —                                                            |

**Pourquoi `code_ouvrage` n'est pas UNIQUE :** dans les fichiers ONEP, plusieurs localités peuvent avoir le même code si le code est local à une sous-préfecture. Le dédoublonnage se fait donc à la consolidation (avec un tuple plus riche), pas au niveau base.

**Pourquoi `hash_sha256` n'est pas UNIQUE :** la réingestion d'un même fichier est légitime (correction de bug, changement de mapping, ajout de champs). On veut pouvoir tracer les réingestions (`fichier.est_reingestion = true`), pas les interdire.

#### 2.1.5 Extensions PostgreSQL utilisées

| Extension       | Rôle                                 | Utilisée par                                   |
|-----------------|--------------------------------------|------------------------------------------------|
| `postgis`       | Type `geometry`, fonctions spatiales | `geom`, `geom_centre`                          |
| `pg_trgm`       | Similarité de chaînes (trigram)      | Rapprochement flou sur `localite.nom_usage`    |
| `unaccent`      | Suppression des accents              | Rapprochement, filtres insensibles aux accents |
| `fuzzystrmatch` | `levenshtein`, `soundex` (V2)        | Non utilisé activement, installé pour V2       |

**Note :** `postgis_topology` et `postgis_tiger_geocoder` sont installés par défaut avec PostGIS (héritage de l'image Docker), mais **non utilisés**. On ne s'appuie pas dessus.

#### 2.1.6 Décision structurante — repartir sur des bases saines

**Décision 8 (section 1.4) — Le projet repart sur des bases saines, guidé par la Bible.**

La Bible est la **spécification cible**. Le `schema.sql`, la base, les migrations et le code sont **réécrits** pour y correspondre. Aucune dette technique n'est conservée par compatibilité avec l'existant.

Conséquences concrètes :
- Une **migration initiale unique** (`0001_initial.py`) remplacera l'historique des migrations (les 5 migrations + le patch `qualite_eau`).
- La base sera **recréée from scratch** (`DROP SCHEMA public CASCADE; CREATE SCHEMA public;` puis `alembic upgrade head`).
- `schema.sql` sera **régénéré** à partir de la Bible (pas patché).
- `models.py`, les services, le frontend seront **alignés** sur la Bible.
- Les fichiers existants servent de **base de travail** (la logique éprouvée est conservée), mais tout ce qui n'est pas conforme à la Bible est corrigé, pas rafistolé.

**Point de non-retour :** une fois la migration initiale générée et la base recréée, on ne revient pas aux anciennes migrations. Le repo sera nettoyé.

---

### 2.2 Dictionnaire des tables

Chaque fiche suit la même structure :
- **Rôle** : à quoi sert la table.
- **Colonnes** : tableau avec nom, type, nullabilité, défaut, contrainte.
- **Contraintes** : CHECK, UNIQUE, FK.
- **Index** : nom + colonnes + type.
- **Règles de remplissage** : qui écrit dans cette table, quand, comment.
- **Points d'attention** : pièges, cas particuliers.

---

#### 2.2.A — Référentiels

##### `source`

**Rôle** : émetteur d'un fichier (ONEP, SODECI, UNICEF, BAD, LONACI, État de CI, etc.). Sert à identifier l'origine des données et à rattacher les projets de financement à un financeur.

**Colonnes**

| Nom           | Type           | Null | Défaut  | Contrainte                                              |
|---------------|----------------|------|---------|---------------------------------------------------------|
| `id_source`   | `serial`       | non  | —       | PK                                                      |
| `nom`         | `varchar(100)` | non  | —       | UNIQUE                                                  |
| `type_source` | `varchar(30)`  | non  | —       | CHECK `IN ('public','prive','bailleur','etat','autre')` |
| `actif`       | `boolean`      | non  | `true`  | —                                                       |
| `commentaire` | `text`         | oui  | —       | —                                                       |
| `created_at`  | `timestamptz`  | non  | `now()` | —                                                       |
| `updated_at`  | `timestamptz`  | non  | `now()` | —                                                       |

**Contraintes**
- `source_type_source_check` : `type_source IN ('public','prive','bailleur','etat','autre')`
- `UNIQUE (nom)` : deux sources ne peuvent pas avoir le même nom.

**Index**
- Aucun index au-delà de la PK et de l'UNIQUE sur `nom` (volume faible : ~10 lignes).

**Règles de remplissage**
- Seedé à la création de la base avec 6 sources : `ONEP`, `SODECI`, `UNICEF`, `BAD`, `LONACI`, `ETAT_CI`.
- La DHR peut en ajouter via un script ou l'UI (V2).
- **Ne jamais supprimer une source** qui a des fichiers (`ON DELETE RESTRICT` sur `fichier.id_source`).

**Points d'attention**
- `type_source = 'bailleur'` est utilisé pour les organismes de financement (UNICEF, BAD). Ce n'est **pas** un type "public" ou "privé" au sens strict. C'est une catégorie à part.
- Une même entité peut être source et financeur (ex. l'État est source ET financeur de certains projets). Le lien se fait via `projet_financement.id_source_financeur`.

---

##### `ref_geo_admin`

**Rôle** : référentiel administratif hiérarchique de la Côte d'Ivoire. Chaque nœud a un niveau (`district`, `region`, `departement`, `sous_prefecture`, `localite`) et un parent (sauf les districts, racines).

**Colonnes**

| Nom             | Type           | Null | Défaut  | Contrainte                                                                        |
|-----------------|----------------|------|---------|-----------------------------------------------------------------------------------|
| `id_geo`        | `serial`       | non  | —       | PK                                                                                |
| `niveau`        | `varchar(20)`  | non  | —       | CHECK `IN ('district','region','departement','sous_prefecture','localite')`       |
| `nom`           | `varchar(150)` | non  | —       | —                                                                                 |
| `parent_id`     | `integer`      | oui  | —       | FK `ref_geo_admin.id_geo`, `ON DELETE RESTRICT`                                   |
| `code_officiel` | `varchar(50)`  | oui  | —       | —                                                                                 |
| `type_localite` | `varchar(20)`  | oui  | —       | CHECK `type_localite IS NULL OR type_localite IN ('village','campement','autre')` |
| `created_at`    | `timestamptz`  | non  | `now()` | —                                                                                 |
| `updated_at`    | `timestamptz`  | non  | `now()` | —                                                                                 |

**Contraintes**
- `chk_ref_geo_parent` : `(niveau = 'district' AND parent_id IS NULL) OR (niveau <> 'district' AND parent_id IS NOT NULL)`. Les districts sont racines, tout le reste a un parent.
- `chk_ref_geo_type_localite` : `(niveau <> 'localite' AND type_localite IS NULL) OR (niveau = 'localite')`. Seuls les nœuds de niveau `localite` peuvent avoir un `type_localite`. Les autres **doivent** l'avoir NULL.
- `ref_geo_admin_niveau_check` : `niveau IN ('district','region','departement','sous_prefecture','localite')`
- `ref_geo_admin_type_localite_check` : `type_localite IS NULL OR type_localite IN ('village','campement','autre')`
- `UNIQUE (parent_id, nom, niveau)` : deux nœuds de même niveau et même parent ne peuvent pas avoir le même nom. Attention : PostgreSQL considère `NULL` comme distinct, donc deux districts peuvent avoir le même nom si `parent_id` est NULL. En pratique, on n'a qu'un seul district racine (`DISTRICT_NON_DEFINI`) + les districts réels (V2).
- `ON DELETE RESTRICT` sur `parent_id` : on ne peut pas supprimer un district qui a des régions.

**Index**
- `idx_ref_geo_niveau` (btree sur `niveau`)
- `idx_ref_geo_parent` (btree sur `parent_id`)
- `idx_ref_geo_nom_trgm` (GIN sur `nom`, avec `gin_trgm_ops`) : utilisé pour la recherche floue sur les noms de localités.

**Règles de remplissage**
- Rempli par `import_localites.py` (script CLI) à partir d'une feuille `Localités` Excel.
- Le script crée la hiérarchie dans l'ordre : district (par défaut `DISTRICT_NON_DEFINI`) → région → département → sous-préfecture → localité.
- **Ne duplique pas** : si un nœud existe déjà (même `niveau`, `nom`, `parent_id`), il est réutilisé.
- Le district `DISTRICT_NON_DEFINI` est créé à la première utilisation et reste. Il est un fallback pour les localités dont le district n'est pas connu.

**Points d'attention**
- **Ne pas confondre `ref_geo_admin.niveau='localite'` et la table `localite`.** `ref_geo_admin` contient la **hiérarchie** (y compris les localités). `localite` contient les **entités métier** rattachées à un nœud `localite` de `ref_geo_admin`. Une ligne `localite` a toujours un `id_geo` qui pointe vers un nœud `niveau='localite'`.
- Le trigger `check_localite_geo` sur la table `localite` vérifie que `id_geo` pointe bien vers un nœud `localite`. Cela empêche les erreurs de rattachement.
- La contrainte `chk_ref_geo_type_localite` a été **assouplie** : avant, elle exigeait `type_localite NOT NULL` pour les nœuds `localite`. Aujourd'hui, un nœud `localite` peut avoir `type_localite = NULL` (si le fichier source ne précise pas "village" ou "campement"). C'est pour gérer les fichiers incomplets.

---

##### `localite`

**Rôle** : entité métier "village" ou "campement". Chaque localité est rattachée à un nœud `ref_geo_admin.niveau='localite'`. C'est la cible du rapprochement : on résout `ligne_ingeree.localite_brute` vers `localite.id_localite`.

**Colonnes**

| Nom                | Type                   | Null | Défaut        | Contrainte                                                                |
|--------------------|------------------------|------|---------------|---------------------------------------------------------------------------|
| `id_localite`      | `serial`               | non  | —             | PK                                                                        |
| `id_geo`           | `integer`              | non  | —             | FK `ref_geo_admin.id_geo`, `ON DELETE RESTRICT`                           |
| `nom_usage`        | `varchar(150)`         | non  | —             | —                                                                         |
| `latitude_centre`  | `double precision`     | oui  | —             | —                                                                         |
| `longitude_centre` | `double precision`     | oui  | —             | —                                                                         |
| `commentaire`      | `text`                 | oui  | —             | —                                                                         |
| `metadata`         | `jsonb`                | non  | `'{}'::jsonb` | —                                                                         |
| `created_at`       | `timestamptz`          | non  | `now()`       | —                                                                         |
| `updated_at`       | `timestamptz`          | non  | `now()`       | —                                                                         |
| `geom_centre`      | `geometry(Point,4326)` | oui  | —             | **colonne générée** `geom_from_latlon(latitude_centre, longitude_centre)` |

**Contraintes**
- FK `id_geo` avec `ON DELETE RESTRICT` : on ne peut pas supprimer un nœud `ref_geo_admin` qui a des localités.
- **Trigger `check_localite_geo`** : à l'INSERT/UPDATE de `id_geo`, vérifie que le nœud cible est bien `niveau='localite'`. Empêche de rattacher une localité à une région ou un département.
- **Pas de UNIQUE sur `nom_usage`.** Deux localités différentes peuvent avoir le même nom si elles sont dans des sous-préfectures différentes. Le dédoublonnage se fait par `(id_geo, nom_usage)` à l'import, mais pas par contrainte base.

**Index**
- `idx_localite_geo` (btree sur `id_geo`) : pour les jointures.
- `idx_localite_geom` (GIST sur `geom_centre`) : pour les requêtes spatiales (V2).
- `idx_localite_nom_trgm` (GIN sur `nom_usage`, avec `gin_trgm_ops`) : pour le rapprochement flou (trigram).
- `idx_localite_metadata` (GIN sur `metadata`).

**Règles de remplissage**
- Rempli par `import_localites.py` (script CLI) à partir de la feuille `Localités`.
- Le script :
    - Crée/récupère le nœud `localite` dans `ref_geo_admin`.
    - Crée la `localite` si elle n'existe pas (check par `(id_geo, nom_usage)`).
    - Remplit `latitude_centre`/`longitude_centre` si fournis.
    - Remplit `metadata` (population, etc. — V2).
- **Ne duplique pas** : deux localités identiques (même `id_geo`, même `nom_usage`) ne sont créées qu'une fois.

**Points d'attention**
- `geom_centre` est la **position approximative** de la localité (centroïde du village, coordonnées fournies par le référentiel). Ce n'est **pas** un point d'ouvrage. Ne pas confondre avec `ouvrage.geom`.
- **`geom_centre` ne doit pas apparaître sur la carte "Tous"** (qui affiche les ouvrages). En mode Fichier, les feuilles de localités doivent être ignorées (filtrage à faire dans `carto.py`).
- `localite` peut avoir des alias (`localite_alias`) pour améliorer le rapprochement.

---

##### `localite_alias`

**Rôle** : variantes de noms d'une localité. Utilisé par le rapprochement pour matcher `"Camp X"` → `"Campement de X"`, `"Abidjan-Cocody"` → `"Cocody"`, etc.

**Colonnes**

| Nom            | Type           | Null | Défaut | Contrainte                                     |
|----------------|----------------|------|--------|------------------------------------------------|
| `id_alias`     | `serial`       | non  | —      | PK                                             |
| `id_localite`  | `integer`      | non  | —      | FK `localite.id_localite`, `ON DELETE CASCADE` |
| `alias`        | `varchar(150)` | non  | —      | —                                              |
| `source_alias` | `varchar(100)` | oui  | —      | —                                              |

**Contraintes**
- `UNIQUE (id_localite, alias)` : un alias est unique pour une localité donnée.
- FK `id_localite` avec `ON DELETE CASCADE` : si on supprime une localité, ses alias partent aussi.

**Index**
- `idx_alias_trgm` (GIN sur `alias`, avec `gin_trgm_ops`) : pour le rapprochement flou sur les alias.

**Règles de remplissage**
- **Non alimenté par le MVP.** Le MVP peut fonctionner sans alias (le rapprochement exact + trigram suffit dans la plupart des cas).
- V2 : soit par script CLI, soit via une UI dédiée, soit par un mécanisme d'apprentissage (si l'utilisateur corrige un rapprochement, l'alias est ajouté).

**Points d'attention**
- `source_alias` trace l'origine de l'alias (ex. `"manuel"`, `"import"`, `"correction_ui"`). Utile pour le debug.
- La table est là, elle est vide au démarrage. C'est normal.

---

#### Récapitulatif 2.2.A

| Table            | Volumétrie attendue                                                               | Écriture              |
|------------------|-----------------------------------------------------------------------------------|-----------------------|
| `source`         | ~10 lignes                                                                        | Seed + UI V2          |
| `ref_geo_admin`  | ~5 000 lignes (districts + régions + départements + sous-préfectures + localités) | `import_localites.py` |
| `localite`       | ~1 000-2 000 lignes                                                               | `import_localites.py` |
| `localite_alias` | 0 (V1) puis croissance (V2)                                                       | V2                    |

---

#### 2.2.B — Ingestion

##### `fichier`

**Rôle** : représente un fichier Excel uploadé. Trace l'origine (source, nom, hash), l'état d'avancement (statut), et les métriques globales (nb feuilles, nb lignes).

**Colonnes**

| Nom                    | Type           | Null | Défaut         | Contrainte                                                       |
|------------------------|----------------|------|----------------|------------------------------------------------------------------|
| `id_fichier`           | `bigserial`    | non  | —              | PK                                                               |
| `id_source`            | `integer`      | non  | —              | FK `source.id_source`, `ON DELETE RESTRICT`                      |
| `nom_fichier_original` | `varchar(255)` | non  | —              | —                                                                |
| `chemin_stockage`      | `text`         | non  | —              | —                                                                |
| `hash_sha256`          | `varchar(64)`  | oui  | —              | —                                                                |
| `taille_octets`        | `bigint`       | oui  | —              | —                                                                |
| `date_reception`       | `timestamptz`  | non  | `now()`        | —                                                                |
| `date_ingestion`       | `timestamptz`  | oui  | —              | —                                                                |
| `statut`               | `varchar(20)`  | non  | `'en_attente'` | CHECK `IN ('en_attente','en_cours','ingere','partiel','erreur')` |
| `nb_feuilles`          | `integer`      | non  | `0`            | —                                                                |
| `nb_lignes_total`      | `integer`      | non  | `0`            | —                                                                |
| `est_reingestion`      | `boolean`      | non  | `false`        | —                                                                |
| `commentaire`          | `text`         | oui  | —              | —                                                                |
| `created_at`           | `timestamptz`  | non  | `now()`        | —                                                                |
| `updated_at`           | `timestamptz`  | non  | `now()`        | —                                                                |

**Contraintes**
- `fichier_statut_check` : `statut IN ('en_attente','en_cours','ingere','partiel','erreur')`
- FK `id_source` avec `ON DELETE RESTRICT` : on ne supprime pas une source qui a des fichiers.
- **Pas de UNIQUE sur `hash_sha256`** : la réingestion d'un même fichier est légitime.

**Index**
- `idx_fichier_source` (btree sur `id_source`)
- `idx_fichier_date` (btree sur `date_reception`)
- `idx_fichier_hash` (btree sur `hash_sha256`) : pour détecter les réingestions rapidement.

**Règles de remplissage**
- Créé par `POST /fichiers` (upload, auth JWT).
- Le service `upload.py` :
    - Sauvegarde le fichier dans `/app/uploads/`.
    - Calcule le hash SHA-256.
    - Vérifie s'il existe déjà un fichier avec le même hash.
        - Si oui et `force=False` : retourne 409 Conflict.
        - Si oui et `force=True` : crée un nouveau `fichier` avec `est_reingestion = true`.
    - Détecte les feuilles (`detecter_feuilles`) et crée les lignes `feuille`.
    - `statut = 'en_attente'`, `nb_feuilles = N`.
- Mis à jour par `run.py` à la fin de l'ingestion :
    - `statut = 'ingere'` (ou `'partiel'` / `'erreur'` selon les résultats).
    - `date_ingestion = now()`.
    - `nb_lignes_total = nb_lignes_stockees + nb_lignes_rejetees`.
      **Les lignes rejetées (totaux, sous-totaux)** ne sont pas stockées dans `ligne_ingeree`, mais elles sont comptées dans `nb_lignes_total` pour que la vue `v_qualite_par_fichier` puisse **calculer** `nb_rejetes` par **différence (cf. 2.2.D et 3.1.6)**. 
      Sans cette **inclusion**, la cohérence `nb_ok + nb_localite_non_resolue + nb_geom_invalide + nb_type_inconnu + nb_doublon_suspect + nb_rejetes = nb_lignes_total` serait fausse.

**Points d'attention**
- `est_reingestion = true` signale qu'un fichier avec le même hash existait déjà. Cela permet de tracer (et éventuellement de comparer) deux ingestions successives.
- **Le même fichier peut être ingéré plusieurs fois.** Il ne faut pas bloquer, seulement avertir (409) ou forcer (`?force=true`).
- `chemin_stockage` est un chemin **absolu sur le serveur** (`/app/uploads/20261105_143000_fichier.xlsx`). Ne pas exposer directement au client.

---

##### `feuille`

**Rôle** : représente une feuille d'un classeur Excel. Un fichier a 1..N feuilles. Chaque feuille est ingérée séparément.

**Colonnes**

| Nom                 | Type           | Null | Défaut         | Contrainte                                                       |
|---------------------|----------------|------|----------------|------------------------------------------------------------------|
| `id_feuille`        | `bigserial`    | non  | —              | PK                                                               |
| `id_fichier`        | `bigint`       | non  | —              | FK `fichier.id_fichier`, `ON DELETE CASCADE`                     |
| `nom_feuille`       | `varchar(150)` | non  | —              | —                                                                |
| `index_feuille`     | `integer`      | non  | —              | —                                                                |
| `type_contenu`      | `varchar(20)`  | non  | `'inconnu'`    | CHECK `IN ('ouvrages','cgpe','mixte','autre','inconnu')`         |
| `nb_lignes`         | `integer`      | non  | `0`            | —                                                                |
| `nb_lignes_valides` | `integer`      | non  | `0`            | —                                                                |
| `statut_ingestion`  | `varchar(20)`  | non  | `'en_attente'` | CHECK `IN ('en_attente','en_cours','ingere','partiel','erreur')` |
| `message_erreur`    | `text`         | oui  | —              | —                                                                |
| `created_at`        | `timestamptz`  | non  | `now()`        | —                                                                |

**Contraintes**
- `feuille_statut_ingestion_check` : `statut_ingestion IN ('en_attente','en_cours','ingere','partiel','erreur')`
- `feuille_type_contenu_check` : `type_contenu IN ('ouvrages','cgpe','mixte','autre','inconnu')`
- `UNIQUE (id_fichier, index_feuille)` : une feuille par index dans un fichier.
- FK `id_fichier` avec `ON DELETE CASCADE` : si on supprime un fichier, ses feuilles partent aussi.

**Index**
- `idx_feuille_fichier` (btree sur `id_fichier`)

**Règles de remplissage**
- Créé par `upload.py` lors de l'upload (une ligne par feuille détectée).
- **`type_contenu` reste `'inconnu'` au MVP.** La détection automatique du type de feuille (`ouvrages` vs `cgpe` vs `mixte`) est V2. Le MVP se base sur le **nom de la feuille** et le **mapping** pour décider.
- Mis à jour par `ingestion.py` :
    - `nb_lignes = len(lignes extraites)`.
    - `nb_lignes_valides = nb lignes avec géométrie valide`.
    - `statut_ingestion = 'ingere'` (ou `'erreur'` si exception).
    - `message_erreur = str(e)` si erreur.

**Points d'attention**
- **Une feuille `Localités` est une feuille comme les autres** au sens du schéma. C'est la consolidation qui l'ignore (via `_est_feuille_localites`). Idem pour la carto (à ajouter, cf. décision "centroïdes non affichés").
- `nb_lignes` compte **toutes** les lignes extraites, `nb_lignes_valides` compte celles qui ont passé le contrôle qualité (lat/lon valides). La différence = lignes `geom_invalide`.

---

##### `mapping_feuille`

**Rôle** : stocke le mapping validé (par l'utilisateur) entre un entête Excel et un champ cible. Un enregistrement par entête.

**Colonnes**

| Nom                      | Type           | Null | Défaut  | Contrainte                                                                                     |
|--------------------------|----------------|------|---------|------------------------------------------------------------------------------------------------|
| `id_mapping`             | `serial`       | non  | —       | PK                                                                                             |
| `id_feuille`             | `bigint`       | non  | —       | FK `feuille.id_feuille`, `ON DELETE CASCADE`                                                   |
| `entete_brut`            | `varchar(255)` | non  | —       | —                                                                                              |
| `champ_cible`            | `varchar(100)` | oui  | —       | — (voir 2.3.4 pour les valeurs possibles : champ standard, `metadata.<entité>.<clé>`, ou NULL) |
| `confiance`              | `numeric(3,2)` | oui  | —       | CHECK `confiance IS NULL OR (confiance >= 0 AND confiance <= 1)`                               |
| `valide_par_utilisateur` | `boolean`      | non  | `false` | —                                                                                              |
| `created_at`             | `timestamptz`  | non  | `now()` | —                                                                                              |

**Contraintes**
- `mapping_feuille_confiance_check` : `confiance IS NULL OR (confiance >= 0 AND confiance <= 1)`
- `UNIQUE (id_feuille, entete_brut)` : un seul mapping par entête dans une feuille.
- FK `id_feuille` avec `ON DELETE CASCADE` : si on supprime une feuille, ses mappings partent.

**Index**
- `idx_mapping_feuille_feuille` (btree sur `id_feuille`)

**Règles de remplissage**
- Créé/vidé par `PUT /fichiers/{id}/mapping` (auth JWT).
- Le service `mapping.py` :
    - `sauvegarder_mapping_feuille` supprime les anciens mappings `valide_par_utilisateur=true` de la feuille, puis insère les nouveaux avec `valide_par_utilisateur=true`.
    - `charger_mapping_pour_ingestion` lit les mappings validés en priorité, sinon retombe sur le mapping auto.
- **Au MVP, `confiance` n'est pas utilisée** dans la logique. Elle est stockée (utile pour l'UI V2 : afficher la confiance du mapping auto). Le mapping validé par l'utilisateur a toujours `confiance = 1.00`.

**Points d'attention**

* **Le mapping auto n'est PAS stocké en base**. Il est **recalculé** à chaque appel de `mapping-proposal` (via `_proposer_mapping_feuille`). Seul **le mapping validé par l'utilisateur est persisté**. C'est volontaire : si on améliore COLUMN_PATTERNS, le mapping auto s'améliore automatiquement, sans avoir à rejouer une migration.

* `champ_cible` a **3 familles de valeurs** (cf. 2.3.4) :

    - **Un champ cible standard** (`region_brute`, `localite_brute`, `type_ouvrage_brut`, `usage_ouvrage_brut`, etc.) : la valeur est extraite dans la colonne brute correspondante de `ligne_ingeree`.

    - **Une destination métadonnée explicite** (`metadata.ouvrage.<clé>`, `metadata.localite.<clé>`, `metadata.cgpe.<clé>`) : **la valeur est stockée dans le metadata de l'entité consolidée, sous la clé explicite** (en plus de `brut_<entête>`).

    - `NULL` : la colonne est ignorée (elle va uniquement dans `donnees_brutes`, pas de métadonnée explicite).

* **La liste des champs cibles standard est figée par** `COLUMN_PATTERNS` (`patterns.py`). Elle inclut : `region_brute`, `departement_brute`, `sous_prefecture_brute`, `localite_brute`, `type_localite_brut`, `latitude_decimal`, `longitude_decimal`, `type_ouvrage_brut`, `usage_ouvrage_brut`, `etat_ouvrage_brut`, `annee_projet`, `bailleur_brut`, `type_financement_brut`, `a_cgpe`. `usage_ouvrage_brut` **est nouveau** (cf. P12).

* **La clé** `<clé>` **de** `metadata.<entité>.<clé>` **doit être documentée** dans `metadata_conventions.md` (section 4) avant d'être utilisée. Le mapping validé par l'utilisateur peut techniquement accepter n'importe quelle clé, mais la convention de projet est de ne pas créer de clé non documentée.

* **La fonctionnalité « ignorer complètement une colonne »** (ne pas la mettre dans `donnees_brutes` non plus) est V2. Pour le MVP, `champ_cible = NULL` **signifie « pas de normalisation, pas de métadonnée explicite »**, mais la valeur brute reste dans `donnees_brutes`.

* `metadata.<entité>.<clé>` n'est pas exclusive : la valeur brute est toujours aussi dans `donnees_brutes` et dans `metadata.brut_<entête>`. **La clé explicite s'ajoute, elle ne remplace pas**.

---

##### `ingestion_run`

**Rôle** : représente une **exécution** de l'ingestion sur un fichier. Un fichier peut avoir N runs (réingestion, run partiel, run échoué, etc.). Le run porte les paramètres (`mode`, `limite_lignes`, `ligne_debut`, `ligne_fin`) et le statut.

**Colonnes**

| Nom                  | Type          | Null | Défaut       | Contrainte                                          |
|----------------------|---------------|------|--------------|-----------------------------------------------------|
| `id_run`             | `bigserial`   | non  | —            | PK                                                  |
| `id_fichier`         | `bigint`      | non  | —            | FK `fichier.id_fichier`, `ON DELETE CASCADE`        |
| `id_feuille`         | `bigint`      | oui  | —            | FK `feuille.id_feuille`, `ON DELETE CASCADE`        |
| `mode`               | `varchar(20)` | non  | `'complet'`  | CHECK `IN ('complet','echantillon','plage')`        |
| `limite_lignes`      | `integer`     | oui  | —            | —                                                   |
| `ligne_debut`        | `integer`     | oui  | —            | —                                                   |
| `ligne_fin`          | `integer`     | oui  | —            | —                                                   |
| `nb_lignes_ingerees` | `integer`     | non  | `0`          | —                                                   |
| `statut`             | `varchar(20)` | non  | `'en_cours'` | CHECK `IN ('en_cours','termine','erreur','annule')` |
| `message`            | `text`        | oui  | —            | —                                                   |
| `started_at`         | `timestamptz` | non  | `now()`      | —                                                   |
| `finished_at`        | `timestamptz` | oui  | —            | —                                                   |

**Contraintes**
- `ingestion_run_mode_check` : `mode IN ('complet','echantillon','plage')`
- `ingestion_run_statut_check` : `statut IN ('en_cours','termine','erreur','annule')`
- `chk_run_mode_params` : cohérence entre `mode` et les paramètres :
    - `complet` : `limite_lignes`, `ligne_debut`, `ligne_fin` tous NULL
    - `echantillon` : `limite_lignes` NOT NULL, `ligne_debut`, `ligne_fin` NULL
    - `plage` : `limite_lignes` NULL, `ligne_debut` NOT NULL, `ligne_fin` NOT NULL, `ligne_fin >= ligne_debut`
- FK `id_fichier` avec `ON DELETE CASCADE`.
- FK `id_feuille` avec `ON DELETE CASCADE` (nullable, permet un run sur tout le fichier).

**Index**
- `idx_run_fichier` (btree sur `id_fichier`)
- `idx_run_feuille` (btree sur `id_feuille`)
- `idx_run_statut` (btree sur `statut`)

**Règles de remplissage**
- Créé par `POST /fichiers/{id}/runs` (auth JWT) ou par `run.py` (orchestrateur).
- `statut = 'en_cours'`, `started_at = now()`.
- Mis à jour à la fin :
    - `statut = 'termine'` si `total_lignes > 0`, sinon `'erreur'`.
    - `nb_lignes_ingerees = total_lignes`.
    - `finished_at = now()`.
    - `message = str(e)` si erreur.

**Points d'attention**
- Un run est **asynchrone** (BackgroundTask FastAPI au MVP). L'utilisateur poll `GET /runs/{id}` pour voir l'avancement.
- **Un run ne peut pas être « annulé »** au MVP (`statut = 'annule'` est déclaré mais pas implémenté). V2 : implémenter un mécanisme d'annulation (interruption de la BackgroundTask).
- **`id_feuille` est optionnel.** Si NULL, le run porte sur tout le fichier. Si renseigné, le run porte sur une seule feuille. Le MVP utilise `NULL` (run sur tout le fichier).
- **Un fichier peut avoir plusieurs runs actifs en parallèle ?** Non, au MVP. Il n'y a pas de verrou, mais l'UI ne propose qu'un run à la fois. Si on lance deux runs sur le même fichier, ils s'exécutent l'un après l'autre (ou se marchent dessus) — V2 : ajouter un verrou.

---

##### `ligne_ingeree`

**Rôle** : représente **une ligne d'Excel ingérée**, stockée brute en JSONB (`donnees_brutes`) avec quelques champs normalisés extraits (coordonnées, localité, type). C'est la **matière première** de la consolidation.

**Colonnes**

| Nom                     | Type                   | Null | Défaut  | Contrainte                                                                                                 |
|-------------------------|------------------------|------|---------|------------------------------------------------------------------------------------------------------------|
| `id_ligne`              | `bigserial`            | non  | —       | PK                                                                                                         |
| `id_feuille`            | `bigint`               | non  | —       | FK `feuille.id_feuille`, `ON DELETE CASCADE`                                                               |
| `id_run`                | `bigint`               | oui  | —       | FK `ingestion_run.id_run`, `ON DELETE SET NULL`                                                            |
| `num_ligne_source`      | `integer`              | non  | —       | —                                                                                                          |
| `donnees_brutes`        | `jsonb`                | non  | —       | —                                                                                                          |
| `district_brut`         | `varchar(150)`         | oui  | —       | —                                                                                                          |
| `region_brute`          | `varchar(150)`         | oui  | —       | —                                                                                                          |
| `departement_brut`      | `varchar(150)`         | oui  | —       | —                                                                                                          |
| `sous_prefecture_brute` | `varchar(150)`         | oui  | —       | —                                                                                                          |
| `localite_brute`        | `varchar(150)`         | oui  | —       | —                                                                                                          |
| `type_localite_brut`    | `varchar(30)`          | oui  | —       | —                                                                                                          |
| `latitude_decimal`      | `double precision`     | oui  | —       | —                                                                                                          |
| `longitude_decimal`     | `double precision`     | oui  | —       | —                                                                                                          |
| `geom`                  | `geometry(Point,4326)` | oui  | —       | **colonne générée** `GENERATED ALWAYS AS geom_from_latlon(latitude_decimal, longitude_decimal) STORED`     |
| `type_ouvrage_brut`     | `varchar(50)`          | oui  | —       | —                                                                                                          |
| `etat_ouvrage_brut`     | `varchar(50)`          | oui  | —       | —                                                                                                          |
| `annee_projet`          | `integer`              | oui  | —       | —                                                                                                          |
| `bailleur_brut`         | `varchar(150)`         | oui  | —       | —                                                                                                          |
| `type_financement_brut` | `varchar(50)`          | oui  | —       | —                                                                                                          |
| `usage_ouvrage_brut`    | `varchar(50)`          | oui  | —       | — *(nouveau)*                                                                                              |
| `a_cgpe`                | `boolean`              | oui  | —       | —                                                                                                          |
| `statut_qualite`        | `varchar(30)`          | non  | `'ok'`  | CHECK `IN ('ok','localite_non_resolue','geom_invalide','type_ouvrage_inconnu','rejete','doublon_suspect')` |
| `message_qualite`       | `text`                 | oui  | —       | Message libre expliquant le statut (ex. `"Localité non résolue : 'Camp X'"`)                               |
| `id_localite`           | `integer`              | oui  | —       | FK `localite.id_localite`, `ON DELETE SET NULL`                                                            |
| `id_ouvrage_consolide`  | `bigint`               | oui  | —       | FK `ouvrage.id_ouvrage`, `ON DELETE SET NULL`                                                              |
| `created_at`            | `timestamptz`          | non  | `now()` | —                                                                                                          |

**Contraintes**
- `ligne_ingeree_statut_qualite_check` : `statut_qualite IN ('ok','localite_non_resolue','geom_invalide','type_ouvrage_inconnu','rejete','doublon_suspect')`
- `UNIQUE (id_feuille, id_run, num_ligne_source)` : une ligne par (feuille, run, numéro de ligne source). Évite les doublons en cas de réingestion partielle.
- FK `id_feuille` avec `ON DELETE CASCADE` : si on supprime une feuille, ses lignes partent.
- FK `id_run` avec `ON DELETE SET NULL` : si on supprime un run, les lignes **survivent** (mais perdent leur lien au run).
- FK `id_localite` avec `ON DELETE SET NULL` : si on supprime une localité, les lignes survivent avec `id_localite = NULL`.
- FK `id_ouvrage_consolide` avec `ON DELETE SET NULL` : si on supprime un ouvrage, les lignes survivent avec `id_ouvrage_consolide = NULL`.

**Index**
- `idx_ligne_feuille` (btree sur `id_feuille`)
- `idx_ligne_run` (btree sur `id_run`)
- `idx_ligne_geom` (GIST sur `geom`)
- `idx_ligne_statut_qualite` (btree sur `statut_qualite`)
- `idx_ligne_localite` (btree sur `id_localite`)
- `idx_ligne_type_ouvrage` (btree sur `type_ouvrage_brut`)
- `idx_ligne_usage_ouvrage` (btree sur `usage_ouvrage_brut`)
- `idx_ligne_donnees_brutes` (GIN sur `donnees_brutes`)
- `idx_ligne_ouvrage` (btree sur `id_ouvrage_consolide`)

**Règles de remplissage**
- Créé par `ingestion.py` (`ingerer_feuille`), une ligne par ligne Excel non vide.
- **Champs normalisés extraits** (à partir du mapping validé, cf. `_extraire_lignes`) :
    - `donnees_brutes` : **toutes** les colonnes de la ligne, avec l'entête comme clé. Sérialisation des dates en ISO, des nombres en int/float.
    - `latitude_decimal` / `longitude_decimal` : parsées via `parser_coordonnees` (gère DMS, virgule, inversion, signe).
    - `geom` : calculé automatiquement (colonne générée).
    - `type_ouvrage_brut`, `etat_ouvrage_brut`, `annee_projet`, `bailleur_brut`, `type_financement_brut`, `usage_ouvrage_brut` : extraits du mapping (`champ_cible` de `mapping_feuille`).
    - `a_cgpe` : extrait via `_to_bool` (Oui/Non/1/0 → bool).
    - `localite_brute`, `region_brute`, etc. : extraits du mapping.
    - `statut_qualite` : `'ok'` si lat/lon valides, sinon `'geom_invalide'`.
- **Mis à jour par `rapprochement.py`** :
    - `id_localite` : rempli si la localité est résolue.
    - `statut_qualite` : passe à `'localite_non_resolue'` si non résolue.
- **Mis à jour par `consolidation.py`** :
    - `id_ouvrage_consolide` : rempli si l'ouvrage est créé.

**Points d'attention**

- `donnees_brutes` **est la source de vérité** pour les attributs non mappés. La consolidation lit `donnees_brutes` pour remplir `ouvrage.metadata` et `ouvrage.qualite_eau`. Ne jamais modifier `donnees_brutes` après l'ingestion (sauf réingestion).

- `usage_ouvrage_brut` est nouveau (cf. P12). Il stocke les valeurs "Hydraulique villageoise", "Point d'eau autonome"... qui serviront à déduire type_alimentation à la consolidation.

- Les 6 statuts de statut_qualite sont implémentés au MVP (cf. 3.1.6 pour les règles précises) :

    * `ok` : écrit par l'ingestion, confirmé par le rapprochement et la consolidation. Ligne consolidée.

    * `geom_invalide` : écrit par l'ingestion (lat/lon manquantes ou invalides). Non consolidée.

    * `localite_non_resolue` : écrit par le rapprochement. Non consolidée.

    * `type_ouvrage_inconnu` : écrit par la consolidation après création de l'ouvrage, quand nature_ouvrage='inconnu' ET type_alimentation='AUTRE' ET realisation_par='inconnu'. L'ouvrage est créé et apparaît sur la carte ; la ligne est marquée pour requalification V2.

    * `doublon_suspect` : écrit par la consolidation avant création, quand un code_ouvrage existe déjà avec des coordonnées distantes de plus de 1 km. Non consolidée.

    * `rejete` : valeur conservée dans le CHECK mais jamais écrite en base au MVP. Les lignes de total/sous-total sont détectées à l'ingestion et ne sont pas stockées (pas de ligne_ingeree créée). Elles sont uniquement comptées via nb_rejetes = fichier.nb_lignes_total - COUNT(ligne_ingeree) dans v_qualite_par_fichier. La valeur est conservée dans le domaine pour permettre V2 (stockage des rejets pour correction manuelle).

- Formats de `message_qualite` par statut (à respecter pour que l'UI puisse parser) :

    * `ok` : NULL.

    * `geom_invalide` : "`Coordonnées manquantes ou invalides`".

    * `localite_non_resolue` : "`Localité non résolue : <localite_brute>`".

    * `doublon_suspect` : "`Code ouvrage <code> déjà utilisé à <distance> km`".

    * `type_ouvrage_inconnu` : "Attributs métier indéterminés (nature, alimentation, réalisation)".

    * `rejete` : jamais écrit (ligne non stockée).

**Les lignes avec `statut_qualite != 'ok'` ne sont pas consolidées** (`_consolider_ligne` les ignore), **sauf** '`type_ouvrage_inconnu`' qui est écrit **après** création de l'ouvrage (la ligne a donc bien `id_ouvrage_consolide` rempli).

Les lignes de feuilles `Localités` sont ingérées normalement, puis ignorées à la **consolidation** (via _`est_feuille_localites`). Cela permet de garder une trace de ce qui a été ingéré. En mode Fichier (carte), elles doivent aussi être exclues (cf. décision « centroïdes non affichés »).

---

#### Récapitulatif 2.2.B

| Table             | Volumétrie attendue (MVP, un fichier de 1300 lignes) | Écriture                     |
|-------------------|------------------------------------------------------|------------------------------|
| `fichier`         | 1 par upload                                         | `POST /fichiers`             |
| `feuille`         | ~1 par fichier                                       | `upload.py`                  |
| `mapping_feuille` | ~40 par feuille (une par entête)                     | `PUT /fichiers/{id}/mapping` |
| `ingestion_run`   | 1 par exécution                                      | `POST /fichiers/{id}/runs`   |
| `ligne_ingeree`   | ~1300 par fichier                                    | `ingestion.py`               |

---

#### 2.2.C — Métier consolidé

##### `ouvrage`

**Rôle** : entité centrale du projet. Représente un **point d'eau unique et dédoublonné** (puits ou forage), rattaché à une localité. C'est ce que voit l'utilisateur dans l'UI (carte, liste, export).

**Colonnes**

| Nom                 | Type                   | Null | Défaut        | Contrainte                                                                                               |
|---------------------|------------------------|------|---------------|----------------------------------------------------------------------------------------------------------|
| `id_ouvrage`        | `bigserial`            | non  | —             | PK                                                                                                       |
| `code_ouvrage`      | `varchar(100)`         | oui  | —             | — (non unique)                                                                                           |
| `id_localite`       | `integer`              | non  | —             | FK `localite.id_localite`, `ON DELETE RESTRICT`                                                          |
| `nature_ouvrage`    | `varchar(20)`          | oui  | —             | CHECK `nature_ouvrage IS NULL OR nature_ouvrage IN ('puits','forage','inconnu')`                         |
| `type_alimentation` | `varchar(20)`          | oui  | —             | CHECK `type_alimentation IS NULL OR type_alimentation IN ('PMH','HVA','PEA','HV','AUTRE')`               |
| `realisation_par`   | `varchar(20)`          | oui  | —             | CHECK `realisation_par IS NULL OR realisation_par IN ('public','prive','inconnu')`                       |
| `etat`              | `varchar(20)`          | non  | `'inconnu'`   | CHECK `etat IN ('fonctionnel','en_panne','abandonne','inconnu')`                                         |
| `annee_realisation` | `integer`              | oui  | —             | —                                                                                                        |
| `latitude_decimal`  | `double precision`     | oui  | —             | —                                                                                                        |
| `longitude_decimal` | `double precision`     | oui  | —             | —                                                                                                        |
| `geom`              | `geometry(Point,4326)` | oui  | —             | **colonne générée** (`GENERATED ALWAYS AS geom_from_latlon(latitude_decimal, longitude_decimal) STORED`) |
| `commentaire`       | `text`                 | oui  | —             | —                                                                                                        |
| `metadata`          | `jsonb`                | non  | `'{}'::jsonb` | —                                                                                                        |
| `qualite_eau`       | `jsonb`                | oui  | —             | — *(nullable, cf. P6)*                                                                                   |
| `created_at`        | `timestamptz`          | non  | `now()`       | —                                                                                                        |
| `updated_at`        | `timestamptz`          | non  | `now()`       | —                                                                                                        |

**Contraintes**
- `ouvrage_nature_check` : `nature_ouvrage IS NULL OR nature_ouvrage IN ('puits','forage','inconnu')`
- `ouvrage_alimentation_check` : `type_alimentation IS NULL OR type_alimentation IN ('PMH','HVA','PEA','HV','AUTRE')`
- `ouvrage_realisation_check` : `realisation_par IS NULL OR realisation_par IN ('public','prive','inconnu')`
- `ouvrage_etat_check` : `etat IN ('fonctionnel','en_panne','abandonne','inconnu')`
- FK `id_localite` avec `ON DELETE RESTRICT` : on ne supprime pas une localité qui a des ouvrages.
- **Pas de UNIQUE sur `code_ouvrage`** : le code peut être local à une sous-préfecture (cf. 2.1.4).

**Index**
- `idx_ouvrage_code` (btree sur `code_ouvrage`, **partiel** : `WHERE code_ouvrage IS NOT NULL`)
- `idx_ouvrage_localite` (btree sur `id_localite`)
- `idx_ouvrage_etat` (btree sur `etat`)
- `idx_ouvrage_nature` (btree sur `nature_ouvrage`)
- `idx_ouvrage_alimentation` (btree sur `type_alimentation`)
- `idx_ouvrage_realisation` (btree sur `realisation_par`)
- `idx_ouvrage_geom` (GIST sur `geom`)
- `idx_ouvrage_metadata` (GIN sur `metadata`)
- `idx_ouvrage_qualite_eau` (GIN sur `qualite_eau`)

**Règles de remplissage**
- Créé par `consolidation.py` (`_consolider_ligne`), à partir des `ligne_ingeree` avec :
    - `statut_qualite = 'ok'`
    - `id_localite` rempli (donc après rapprochement)
    - `latitude_decimal` et `longitude_decimal` non NULL (donc `geom_invalide` exclu)
- **Nature** (`_map_nature`) : `puits` / `forage` / `inconnu`. Priorité : `type_ouvrage_brut`.
- **Alimentation** (`_map_alimentation`) : `PMH` / `HVA` / `PEA` / `HV` / `AUTRE`. Priorité : nom de feuille > `type_ouvrage_brut` > `usage_ouvrage_brut`.
- **Réalisation** (`_map_realisation`) : `public` / `prive` / `inconnu`. Priorité : colonne explicite `Type de forage` > `type_ouvrage_brut` (ex. `"Forage ADM"`) > nom de feuille.
- **État** (`_map_etat`) : `fonctionnel` / `en_panne` / `abandonne` / `inconnu`. Priorité : `etat_ouvrage_brut`.
- **Metadata** : toutes les colonnes de `donnees_brutes` non mappées, préfixées par `brut_`.
- **Qualité_eau** : extraite de `donnees_brutes` via `_extraire_qualite_eau` (mots-clés sanitaires). Si aucun indicateur, `NULL`.
- **Dédoublonnage** (`_trouver_ouvrage_existant`) :
    - Priorité 1 : `code_ouvrage` identique.
    - Priorité 2 : `(id_localite, nature_ouvrage, type_alimentation, annee_realisation)` identiques.
    - Si trouvé : mise à jour des champs vides + fusion metadata + fusion qualite_eau.
    - Sinon : création.

**Points d'attention**
- **`nature_ouvrage`, `type_alimentation`, `realisation_par` sont nullables.** Pourquoi ? Un ouvrage peut être créé sans qu'on sache la nature (`inconnu`), ou sans qu'on sache la réalisation (`inconnu`). Il faut pouvoir les mettre à jour plus tard si un fichier ultérieur apporte l'info.
- **`etat` est non-nullable avec défaut `'inconnu'`.** Un ouvrage a toujours un état (même "inconnu"). C'est différent des 3 attributs ci-dessus.
- **`geom` est nullable** en base, mais en pratique on ne crée un ouvrage **que si** `lat`/`lon` sont non-NULL (la consolidation refuse les lignes `geom_invalide`). Donc en pratique, `geom` est non-NULL pour tous les ouvrages.
- **`qualite_eau` est nullable, pas `'{}'`.** NULL = « pas d'info sur la qualité de l'eau ». `{}` = « champ présent mais vide » (ne devrait pas arriver). On utilise NULL.
- **`metadata` est non-nullable avec `'{}'::jsonb`.** Un ouvrage a toujours un metadata (même vide).
- **Le dédoublonnage par `code_ouvrage` ne filtre pas sur `id_localite`.** Deux localités différentes avec le même code peuvent être fusionnées à tort. C'est un risque accepté au MVP. V2 : ajouter `id_localite` au dédoublonnage, ou un mécanisme de résolution manuelle.

---

##### `cgpe`

**Rôle** : Comité de Gestion de Point d'Eau. Association villageoise qui gère l'ouvrage. **Un CGPE est rattaché à une localité**, et **optionnellement à un ouvrage**. Un CGPE peut exister sans ouvrage précis (il gère un point d'eau collectif non consolidé), et un ouvrage peut exister sans CGPE.

**Colonnes**

| Nom             | Type          | Null | Défaut        | Contrainte                                                                      |
|-----------------|---------------|------|---------------|---------------------------------------------------------------------------------|
| `id_cgpe`       | `serial`      | non  | —             | PK                                                                              |
| `id_localite`   | `integer`     | non  | —             | FK `localite.id_localite`, `ON DELETE CASCADE`                                  |
| `id_ouvrage`    | `bigint`      | oui  | —             | FK `ouvrage.id_ouvrage`, `ON DELETE SET NULL`                                   |
| `existe`        | `boolean`     | non  | `true`        | —                                                                               |
| `date_creation` | `date`        | oui  | —             | —                                                                               |
| `statut`        | `varchar(20)` | oui  | —             | CHECK `statut IS NULL OR statut IN ('fonctionnel','non_fonctionnel','inconnu')` |
| `nb_membres`    | `integer`     | oui  | —             | —                                                                               |
| `commentaire`   | `text`        | oui  | —             | —                                                                               |
| `metadata`      | `jsonb`       | non  | `'{}'::jsonb` | —                                                                               |
| `created_at`    | `timestamptz` | non  | `now()`       | —                                                                               |
| `updated_at`    | `timestamptz` | non  | `now()`       | —                                                                               |

**Contraintes**
- `cgpe_statut_check` : `statut IS NULL OR statut IN ('fonctionnel','non_fonctionnel','inconnu')`
- FK `id_localite` avec `ON DELETE CASCADE` : si on supprime une localité, ses CGPE partent.
- FK `id_ouvrage` avec `ON DELETE SET NULL` : si on supprime un ouvrage, le CGPE survit avec `id_ouvrage = NULL`.

**Index**
- `idx_cgpe_localite` (btree sur `id_localite`)
- `idx_cgpe_ouvrage` (btree sur `id_ouvrage`)
- `idx_cgpe_metadata` (GIN sur `metadata`)

**Règles de remplissage**
- **Non implémenté au MVP.** La consolidation ne crée **pas** de `cgpe` à partir des lignes ingérées. Le champ `ligne_ingeree.a_cgpe` (booléen) est rempli mais n'est pas utilisé pour créer des CGPE.
- V2 : implémenter la détection et la création (cf. question 3 du client, non traitée au MVP).
- Pour le MVP, la table existe mais reste vide.

**Points d'attention**
- **`existe` et `statut` sont deux choses différentes.** `existe = false` signifie « pas de CGPE du tout ». `existe = true, statut = 'non_fonctionnel'` signifie « CGPE existe mais ne fonctionne pas ». `existe = true, statut = NULL` signifie « CGPE existe, statut inconnu ».
- **`id_ouvrage` est nullable.** Un CGPE peut être créé au niveau d'une localité sans être rattaché à un ouvrage précis. C'est le cas le plus courant dans les fichiers ONEP.
- **`nb_membres`** : nombre de membres du comité. Optionnel.
- **La table est vide au MVP.** C'est normal.

---

##### `projet_financement`

**Rôle** : projet de financement porté par un **bailleur** (UNICEF, BAD) ou par l'**État**. Permet de tracer quels ouvrages ont été financés par quel projet, avec quel montant.

**Colonnes**

| Nom                   | Type            | Null | Défaut  | Contrainte                                          |
|-----------------------|-----------------|------|---------|-----------------------------------------------------|
| `id_projet`           | `bigserial`     | non  | —       | PK                                                  |
| `nom_projet`          | `varchar(255)`  | non  | —       | —                                                   |
| `annee`               | `integer`       | oui  | —       | —                                                   |
| `id_source_financeur` | `integer`       | non  | —       | FK `source.id_source`, `ON DELETE RESTRICT`         |
| `type_financement`    | `varchar(20)`   | non  | —       | CHECK `IN ('etat','prive','partenariat','inconnu')` |
| `montant`             | `numeric(18,2)` | oui  | —       | —                                                   |
| `devise`              | `varchar(3)`    | oui  | `'XOF'` | —                                                   |
| `commentaire`         | `text`          | oui  | —       | —                                                   |
| `created_at`          | `timestamptz`   | non  | `now()` | —                                                   |
| `updated_at`          | `timestamptz`   | non  | `now()` | —                                                   |

**Contraintes**
- `projet_financement_type_check` : `type_financement IN ('etat','prive','partenariat','inconnu')`
- FK `id_source_financeur` avec `ON DELETE RESTRICT` : on ne supprime pas une source qui finance des projets.

**Index**
- `idx_projet_annee` (btree sur `annee`)
- `idx_projet_source` (btree sur `id_source_financeur`)

**Règles de remplissage**
- **Non implémenté au MVP.** Aucun endpoint ne crée de `projet_financement`.
- V2 : UI de gestion, ou import depuis un fichier de projets.
- Pour le MVP, la table existe mais reste vide.

**Points d'attention**
- **`type_financement`** : `'etat'` (financement public), `'prive'` (financement privé), `'partenariat'` (mixte), `'inconnu'`. Attention : ce n'est **pas** le même concept que `source.type_source`. Une source `UNICEF` (type `bailleur`) peut financer un projet de type `'partenariat'`.
- **`devise`** : par défaut `'XOF'` (franc CFA). Si un projet est en USD ou EUR, on le précise.
- **La table est vide au MVP.** C'est normal.

---

##### `ouvrage_projet`

**Rôle** : table de jointure N..N entre `ouvrage` et `projet_financement`. Permet de tracer quels ouvrages ont été financés par quel projet, avec un **rôle** (`principal` ou `co_financement`).

**Colonnes**

| Nom                | Type          | Null | Défaut        | Contrainte                                             |
|--------------------|---------------|------|---------------|--------------------------------------------------------|
| `id_ouvrage`       | `bigint`      | non  | —             | FK `ouvrage.id_ouvrage`, `ON DELETE CASCADE`           |
| `id_projet`        | `bigint`      | non  | —             | FK `projet_financement.id_projet`, `ON DELETE CASCADE` |
| `role_financement` | `varchar(20)` | non  | `'principal'` | CHECK `IN ('principal','co_financement')`              |

**Contraintes**
- PK composite `(id_ouvrage, id_projet)`.
- `ouvrage_projet_role_check` : `role_financement IN ('principal','co_financement')`
- FK `id_ouvrage` avec `ON DELETE CASCADE` : si on supprime un ouvrage, ses liens partent.
- FK `id_projet` avec `ON DELETE CASCADE` : si on supprime un projet, ses liens partent.

**Index**
- `idx_ouvrage_projet_projet` (btree sur `id_projet`)

**Règles de remplissage**
- **Non implémenté au MVP.** Aucun endpoint ne crée de `ouvrage_projet`.
- V2 : UI de gestion, ou import.

**Points d'attention**
- **`role_financement`** : `'principal'` (bailleur principal du projet), `'co_financement'` (partenaire secondaire). Un ouvrage peut avoir plusieurs projets `'principal'` si plusieurs bailleurs ont financé le même ouvrage (cas rare mais possible).
- **La table est vide au MVP.** C'est normal.

---

#### Récapitulatif 2.2.C

| Table                | Volumétrie attendue (MVP)     | Écriture           |
|----------------------|-------------------------------|--------------------|
| `ouvrage`            | ~1000-3000 par fichier ingéré | `consolidation.py` |
| `cgpe`               | 0 (V1) puis croissance (V2)   | V2                 |
| `projet_financement` | 0 (V1) puis croissance (V2)   | V2                 |
| `ouvrage_projet`     | 0 (V1) puis croissance (V2)   | V2                 |

---

#### 2.2.D — Vues

Les vues sont en **lecture seule**. Elles simplifient les requêtes de l'API et de l'UI (carto, qualité) en pré-joignant les tables.

---

##### `v_points_par_fichier`

**Rôle** : points **bruts** d'un fichier, pour le mode « Par fichier » de la carte. Part de `ligne_ingeree`, joint `feuille`, `fichier`, `source`. **Exclut les feuilles de localités.**

**Colonnes**

| Nom                     | Type                   | Null | Source                                |
|-------------------------|------------------------|------|---------------------------------------|
| `id_fichier`            | `bigint`               | non  | `fichier.id_fichier`                  |
| `nom_fichier_original`  | `varchar(255)`         | non  | `fichier.nom_fichier_original`        |
| `date_ingestion`        | `timestamptz`          | oui  | `fichier.date_ingestion`              |
| `source`                | `varchar(100)`         | non  | `source.nom`                          |
| `id_feuille`            | `bigint`               | non  | `feuille.id_feuille`                  |
| `nom_feuille`           | `varchar(150)`         | non  | `feuille.nom_feuille`                 |
| `id_ligne`              | `bigint`               | non  | `ligne_ingeree.id_ligne`              |
| `num_ligne_source`      | `integer`              | non  | `ligne_ingeree.num_ligne_source`      |
| `type_ouvrage_brut`     | `varchar(50)`          | oui  | `ligne_ingeree.type_ouvrage_brut`     |
| `etat_ouvrage_brut`     | `varchar(50)`          | oui  | `ligne_ingeree.etat_ouvrage_brut`     |
| `annee_projet`          | `integer`              | oui  | `ligne_ingeree.annee_projet`          |
| `bailleur_brut`         | `varchar(150)`         | oui  | `ligne_ingeree.bailleur_brut`         |
| `type_financement_brut` | `varchar(50)`          | oui  | `ligne_ingeree.type_financement_brut` |
| `statut_qualite`        | `varchar(30)`          | non  | `ligne_ingeree.statut_qualite`        |
| `latitude_decimal`      | `double precision`     | oui  | `ligne_ingeree.latitude_decimal`      |
| `longitude_decimal`     | `double precision`     | oui  | `ligne_ingeree.longitude_decimal`     |
| `geom`                  | `geometry(Point,4326)` | oui  | `ligne_ingeree.geom`                  |

**Filtres** :
- `WHERE li.geom IS NOT NULL`
- **`AND NOT _est_feuille_localites(fe.nom_feuille)`** — exclusion des feuilles de localités.

**Implémentation du filtre localités** : la vue doit exclure les feuilles dont le nom matche `localité`, `village` ou `campement`. Comme on ne peut pas appeler une fonction Python depuis SQL, on utilise un `NOT (lower(nom_feuille) LIKE ...)` ou une expression équivalente :

```sql
AND NOT (
    lower(fe.nom_feuille) LIKE '%localite%'
    OR lower(fe.nom_feuille) LIKE '%localité%'
    OR lower(fe.nom_feuille) LIKE '%village%'
    OR lower(fe.nom_feuille) LIKE '%campement%'
)
```

Note : `unaccent(lower(fe.nom_feuille)) LIKE '%localite%'` serait plus propre (accents ignorés), mais `nom_feuille` est en `varchar` et `unaccent` est disponible. Utiliser `unaccent(lower(fe.nom_feuille))` pour être robuste.

**Règles d'usage**
- Alimente le mode « Par fichier » de la carte (`GET /carto/fichiers/{id}/points`).
- Les feuilles de localités ne sont **pas affichées** sur la carte (décision « centroïdes non affichés »).
- Les colonnes exposées sont volontairement limitées : pas de `donnees_brutes` (trop gros), pas de `metadata`. C'est pour l'affichage carto.

**Points d'attention**
- **Cette vue expose des lignes brutes**, pas des ouvrages consolidés. Une même localité peut avoir 5 lignes (5 ouvrages), la carte affichera 5 points. C'est le comportement attendu en mode « Par fichier ».
- **`statut_qualite` est exposé** pour que l'UI puisse colorer/filtrer (ex. `geom_invalide` en rouge, `localite_non_resolue` en orange).

---

##### `v_points_consolides`

**Rôle** : points **consolidés** (un par ouvrage), pour le mode « Tous » de la carte. Part de `ouvrage`, joint `localite` et `ref_geo_admin` (hiérarchie **4 niveaux : Region -> departement -> sous-préfecture → localité**). Expose `metadata` et `qualite_eau` pour les popups.

**Colonnes**

| Nom                 | Type                   | Null | Source                                         |
|---------------------|------------------------|------|------------------------------------------------|
| `id_ouvrage`        | `bigint`               | non  | `ouvrage.id_ouvrage`                           |
| `code_ouvrage`      | `varchar(100)`         | oui  | `ouvrage.code_ouvrage`                         |
| `etat`              | `varchar(20)`          | non  | `ouvrage.etat`                                 |
| `nature_ouvrage`    | `varchar(20)`          | oui  | `ouvrage.nature_ouvrage`                       |
| `type_alimentation` | `varchar(20)`          | oui  | `ouvrage.type_alimentation`                    |
| `realisation_par`   | `varchar(20)`          | oui  | `ouvrage.realisation_par`                      |
| `annee_realisation` | `integer`              | oui  | `ouvrage.annee_realisation`                    |
| `localite`          | `varchar(150)`         | non  | `localite.nom_usage`                           |
| `sous_prefecture`   | `varchar(150)`         | oui  | `ref_geo_admin.nom` (niveau `sous_prefecture`) |
| `departement`       | `varchar(150)`         | oui  | `ref_geo_admin.nom` (niveau `departement`)     |
| `region`            | `varchar(150)`         | oui  | `ref_geo_admin.nom` (niveau `region`)          |
| `latitude_decimal`  | `double precision`     | oui  | `ouvrage.latitude_decimal`                     |
| `longitude_decimal` | `double precision`     | oui  | `ouvrage.longitude_decimal`                    |
| `geom`              | `geometry(Point,4326)` | oui  | `ouvrage.geom`                                 |
| `metadata`          | `jsonb`                | non  | `ouvrage.metadata`                             |
| `qualite_eau`       | `jsonb`                | oui  | `ouvrage.qualite_eau`                          |

**Jointures** :
- `JOIN localite ON localite.id_localite = ouvrage.id_localite`
- `JOIN ref_geo_admin g ON g.id_geo = localite.id_geo` (niveau `localite`)
- `LEFT JOIN ref_geo_admin gp ON gp.id_geo = g.parent_id` (niveau `sous_prefecture`)
- `LEFT JOIN ref_geo_admin gr ON gr.id_geo = gp.parent_id` (niveau `departement`)
- `LEFT JOIN ref_geo_admin gd ON gd.id_geo = gr.parent_id` (niveau `region`)

**Pas de district** dans la vue. Le district n'est pas un niveau de filtre pertinent (réforme territoriale, seuls Abidjan et Yamoussoukro sont concernés, hors scope rural).

**Filtre** : `WHERE o.geom IS NOT NULL`.

**Règles d'usage**
- Alimente le mode « Tous » de la carte (`GET /carto/tous/points`).
- Ne doit **pas** exposer `geom_centre` de `localite`.
- Expose `metadata` et `qualite_eau` pour les popups `<details>` de la carte.

**Points d'attention**
- **La vue expose 4 niveaux** (sous-préfecture, département, région, localité). Si l'UI veut afficher le district, elle devra faire une requête supplémentaire ou on ajoutera le district en V2.
- **`metadata` et `qualite_eau` sont exposés bruts (JSONB)**. Le router `carto.py` doit les inclure dans les `properties` du GeoJSON sans les modifier.
- **Pas de `type_ouvrage` (legacy)**, remplacé par `nature_ouvrage`, `type_alimentation`, `realisation_par`.

---

##### `v_qualite_par_fichier`

**Rôle** : tableau de bord qualité par fichier. Compte les lignes par `statut_qualite` **stocké**, et calcule `nb_rejetes` par **différence** (les lignes rejetées ne sont pas stockées). Alimente la page **Qualité**.

**Colonnes**

| Nom                       | Type           | Null | Source                                                               |
|---------------------------|----------------|------|----------------------------------------------------------------------|
| `id_fichier`              | `bigint`       | non  | `fichier.id_fichier`                                                 |
| `nom_fichier_original`    | `varchar(255)` | non  | `fichier.nom_fichier_original`                                       |
| `source`                  | `varchar(100)` | non  | `source.nom`                                                         |
| `statut`                  | `varchar(20)`  | non  | `fichier.statut`                                                     |
| `nb_lignes_total`         | `integer`      | non  | `fichier.nb_lignes_total`                                            |
| `nb_ok`                   | `bigint`       | —    | `COUNT(*) FILTER (WHERE li.statut_qualite = 'ok')`                   |
| `nb_localite_non_resolue` | `bigint`       | —    | `COUNT(*) FILTER (WHERE li.statut_qualite = 'localite_non_resolue')` |
| `nb_geom_invalide`        | `bigint`       | —    | `COUNT(*) FILTER (WHERE li.statut_qualite = 'geom_invalide')`        |
| `nb_type_inconnu`         | `bigint`       | —    | `COUNT(*) FILTER (WHERE li.statut_qualite = 'type_ouvrage_inconnu')` |
| `nb_rejetes`              | `bigint`       | —    | `(fichier.nb_lignes_total - COUNT(li.id_ligne)) AS nb_rejetes`       |
| `nb_doublon_suspect`      | `bigint`       | —    | `COUNT(*) FILTER (WHERE li.statut_qualite = 'doublon_suspect')`      |

**Jointures** :
- `JOIN source ON source.id_source = fichier.id_source`
- `LEFT JOIN feuille ON feuille.id_fichier = fichier.id_fichier`
- `LEFT JOIN ligne_ingeree li ON li.id_feuille = feuille.id_feuille`

**Group by** : `fichier.id_fichier, fichier.nom_fichier_original, source.nom, fichier.statut, fichier.nb_lignes_total`

**Expression SQL de `nb_rejetes`** :
```sql
(fichier.nb_lignes_total - COUNT(li.id_ligne)) AS nb_rejetes
```

**Pourquoi par différence et non** `COUNT(*) FILTER (WHERE statut_qualite = 'rejete')` :
**les lignes rejetées (totaux, sous-totaux) ne sont pas stockées** dans `ligne_ingeree` (cf. 3.1.6). Un `COUNT(*) FILTER` retournerait donc toujours `0`, 
et la cohérence `nb_ok + ... + nb_rejetes = nb_lignes_total` serait fausse dès qu'un fichier contient des rejets. 
La différence `nb_lignes_total - COUNT(ligne_ingeree)` est la seule façon correcte de compter les rejets sans les stocker.


**Règles d'usage**
- Alimente `GET /qualite/fichiers/{id}` et la page Qualité.
- **Cohérence attendue** : `nb_ok + nb_localite_non_resolue + nb_geom_invalide + nb_type_inconnu + nb_doublon_suspect + nb_rejetes = nb_lignes_total`.

**Points d'attention**
- `nb_lignes_total` peut être faux si le fichier a été ingéré partiellement (`statut = 'partiel'`) ou si l'ingestion a échoué avant la mise à jour finale. À vérifier dans l'UI.

- `nb_rejetes` **peut être négatif si** `nb_lignes_total` a été mal calculé (ex. mis à `COUNT(ligne_ingeree)` **au lieu de stockées + rejetées**). C'est un symptôme de bug d'ingestion, à surveiller. La vue ne doit pas clamper à `0` : **un négatif signale une incohérence**.

- `nb_doublon_suspect` et `nb_type_inconnu` sont implémentés au MVP (cf. 3.1.6). Ils peuvent être non nuls.

- `nb_rejetes` **inclut aussi les lignes vides** (lignes Excel entièrement vides, ignorées à l'ingestion). C'est volontaire : elles font partie de `nb_lignes_total` et **ne sont pas stockées**, donc elles tombent dans la différence. Si on veut les distinguer, il faudra ajouter un compteur dédié en V2.

---

#### Récapitulatif 2.2.D

| Vue                     | Usage              | Complexité                           |
|-------------------------|--------------------|--------------------------------------|
| `v_points_par_fichier`  | Carto mode Fichier | Simple + filtre localités            |
| `v_points_consolides`   | Carto mode Tous    | Moyenne (4 jointures + JSONB)        |
| `v_qualite_par_fichier` | Page Qualité       | Moyenne (agrégats + doublon_suspect) |

---

Parfait. **2.3 — Règles métier transverses.** C'est la dernière partie de la section 2. Elle rassemble tout ce qui ne se lit pas dans une seule fiche de table : les fonctions PostgreSQL, les triggers, les contraintes transverses, les conventions, et les règles d'intégrité qui lient plusieurs tables.

---

### 2.3 Règles métier transverses

Cette section rassemble les règles qui ne se lisent pas dans une seule fiche de table :
- les **fonctions PostgreSQL** (calculs, triggers),
- les **triggers** (maintien automatique de `updated_at`, cohérence de `localite.id_geo`),
- les **contraintes d'intégrité inter-tables** (règles qui lient plusieurs tables),
- les **conventions de nommage** (colonnes, clés, JSONB, dates),
- les **règles de gestion** qui ne sont pas des contraintes SQL mais des invariants du pipeline.

---

#### 2.3.1 Fonctions PostgreSQL

Trois fonctions sont créées à l'initialisation de la base. Elles sont **indispensables** au fonctionnement du schéma (colonnes générées, triggers).

##### `geom_from_latlon(lat double precision, lon double precision) → geometry(Point, 4326)`

**Rôle** : convertit un couple latitude/longitude décimal en `geometry(Point, 4326)`.

**Comportement** :
- Retourne `NULL` si `lat` ou `lon` est `NULL`.
- Retourne `NULL` si `lat` hors `[-90, 90]` ou `lon` hors `[-180, 180]`.
- Retourne `NULL` si `(lat, lon) = (0, 0)` (coordonnée nulle par défaut, généralement une erreur de saisie).
- Sinon, retourne `ST_SetSRID(ST_MakePoint(lon, lat), 4326)` — **attention à l'ordre** : `lon` en X, `lat` en Y (convention PostGIS).

**Propriétés** : `IMMUTABLE STRICT`. Immutable car utilisée dans des colonnes générées (contrainte PostgreSQL). Strict car si un argument est NULL, elle retourne NULL sans exécuter le corps.

**Utilisée par** :
- `localite.geom_centre` (colonne générée)
- `ouvrage.geom` (colonne générée)
- `ligne_ingeree.geom` (colonne générée)

**Point d'attention** : c'est la **seule** façon dont `geom` est calculé. On n'écrit jamais `geom` directement. Si on veut mettre à jour `geom`, on met à jour `lat`/`lon`, et PostgreSQL recalcule `geom` automatiquement.

##### `trg_set_updated_at() → trigger`

**Rôle** : trigger générique qui met `NEW.updated_at = now()` à chaque `UPDATE`.

**Comportement** : simple, pas de logique conditionnelle.

**Utilisée par** (7 tables) :
- `source`
- `ref_geo_admin`
- `localite`
- `fichier`
- `ouvrage`
- `cgpe`
- `projet_financement`

**Point d'attention** : la fonction est **générique**, le trigger est créé table par table. Ajouter une nouvelle table avec `updated_at` = ajouter un trigger dans la migration. Pas de trigger global.

##### `trg_check_localite_geo() → trigger`

**Rôle** : vérifie que `localite.id_geo` pointe bien vers un nœud `ref_geo_admin` de niveau `localite`.

**Comportement** :
- Sur `INSERT` ou `UPDATE OF id_geo` sur `localite`.
- Récupère le `niveau` du nœud cible.
- Si `niveau != 'localite'` → `RAISE EXCEPTION` avec message explicite.

**Utilisée par** : `localite` uniquement.

**Point d'attention** : ce trigger **empêche les erreurs de rattachement**. Sans lui, on pourrait rattacher une localité à une région ou un département, ce qui casserait la hiérarchie. C'est une sécurité métier, pas une simple validation.

---

#### 2.3.2 Triggers

| Trigger              | Table                | Événement                           | Fonction                   |
|----------------------|----------------------|-------------------------------------|----------------------------|
| `set_updated_at`     | `source`             | `BEFORE UPDATE`                     | `trg_set_updated_at()`     |
| `set_updated_at`     | `ref_geo_admin`      | `BEFORE UPDATE`                     | `trg_set_updated_at()`     |
| `set_updated_at`     | `localite`           | `BEFORE UPDATE`                     | `trg_set_updated_at()`     |
| `set_updated_at`     | `fichier`            | `BEFORE UPDATE`                     | `trg_set_updated_at()`     |
| `set_updated_at`     | `ouvrage`            | `BEFORE UPDATE`                     | `trg_set_updated_at()`     |
| `set_updated_at`     | `cgpe`               | `BEFORE UPDATE`                     | `trg_set_updated_at()`     |
| `set_updated_at`     | `projet_financement` | `BEFORE UPDATE`                     | `trg_set_updated_at()`     |
| `check_localite_geo` | `localite`           | `BEFORE INSERT OR UPDATE OF id_geo` | `trg_check_localite_geo()` |

**Point d'attention** : les triggers ne sont **pas** gérés par Alembic automatiquement (SQLAlchemy ne les connaît pas). Ils sont créés en SQL brut dans la migration initiale. Si un jour on ajoute une table avec `updated_at`, il faudra ajouter le trigger manuellement dans une migration.

---

#### 2.3.3 Contraintes d'intégrité inter-tables

Ce sont des règles qui lient **plusieurs tables** et qui ne peuvent pas être exprimées par une simple FK ou un CHECK. Elles sont garanties par :
- **le pipeline** (ingestion → rapprochement → consolidation),
- **les services Python** (ex. `_consolider_ligne` refuse les lignes sans localité),
- **des requêtes de vérification** (à exécuter périodiquement ou en test).

##### R1 — `ouvrage.id_localite` doit pointer vers un nœud de niveau `localite`

**Garanti par** : FK `ouvrage.id_localite → localite.id_localite` + trigger `check_localite_geo` sur `localite`. On ne peut pas créer un `ouvrage` qui pointe vers une localité mal rattachée.

**Vérification** :
```sql
SELECT o.id_ouvrage
FROM ouvrage o
JOIN localite l ON l.id_localite = o.id_localite
JOIN ref_geo_admin g ON g.id_geo = l.id_geo
WHERE g.niveau != 'localite';
-- Attendu : 0 ligne
```

##### R2 — `cgpe.id_ouvrage` doit pointer vers un ouvrage de la **même localité** que le CGPE

**Garanti par** : **rien** en SQL (pas de contrainte composite). Le pipeline doit respecter cette règle. Un CGPE rattaché à l'ouvrage X doit avoir `cgpe.id_localite = ouvrage.id_localite`.

**Pourquoi pas une FK composite** : on pourrait ajouter `FOREIGN KEY (id_ouvrage, id_localite) REFERENCES ouvrage(id_ouvrage, id_localite)`, mais cela obligerait `ouvrage` à avoir une UNIQUE `(id_ouvrage, id_localite)` (redondant avec la PK). C'est faisable mais coûteux.

**Vérification** :
```sql
SELECT c.id_cgpe
FROM cgpe c
JOIN ouvrage o ON o.id_ouvrage = c.id_ouvrage
WHERE c.id_localite != o.id_localite;
-- Attendu : 0 ligne
```

**Au MVP** : pas de CGPE créés, donc pas de risque. La règle est **à implémenter en V2** quand on créera des CGPE.

##### R3 — Une ligne `ligne_ingeree` consolidée doit avoir `id_localite` non NULL

**Garanti par** : `_consolider_ligne` (Python) refuse les lignes avec `id_localite IS NULL`. En SQL, rien n'empêche `id_ouvrage_consolide NOT NULL` avec `id_localite NULL`. C'est une règle du pipeline, pas du schéma.

**Vérification** :
```sql
SELECT id_ligne
FROM ligne_ingeree
WHERE id_ouvrage_consolide IS NOT NULL AND id_localite IS NULL;
-- Attendu : 0 ligne
```

##### R4 — Une ligne `ligne_ingeree` consolidée doit avoir `statut_qualite = 'ok'`

**Garanti par** : `_consolider_ligne` refuse les lignes avec `statut_qualite != 'ok'`. Même remarque que R3.

**Vérification** :
```sql
SELECT id_ligne
FROM ligne_ingeree
WHERE id_ouvrage_consolide IS NOT NULL AND statut_qualite != 'ok';
-- Attendu : 0 ligne
```

##### R5 — Un ouvrage consolidé doit avoir `geom IS NOT NULL`

**Garanti par** : `_consolider_ligne` refuse les lignes avec `lat`/`lon` NULL. La colonne `geom` est calculée, donc si `lat`/`lon` sont non NULL, `geom` est non NULL (sauf si `geom_from_latlon` rejette les bornes, mais le pipeline a déjà filtré).

**Vérification** :
```sql
SELECT id_ouvrage FROM ouvrage WHERE geom IS NULL;
-- Attendu : 0 ligne
```

##### R6 — `fichier.nb_lignes_total` est supérieur ou égal au COUNT de `ligne_ingeree`

**Garanti par** : `ingestion.py` met à jour `nb_lignes_total = nb_lignes_stockees + nb_lignes_rejetees`. L**es lignes rejetées (totaux, sous-totaux, lignes vides)** ne sont pas stockées dans `ligne_ingeree` (cf. 3.1.6). Donc `nb_lignes_total >= COUNT(ligne_ingeree`) **toujours**.

**Vérification (inégalité, testable en SQL) :** :
```sql
SELECT f.id_fichier, f.nb_lignes_total, COUNT(li.id_ligne) AS stockees
FROM fichier f
         LEFT JOIN feuille fe ON fe.id_fichier = f.id_fichier
         LEFT JOIN ligne_ingeree li ON li.id_feuille = fe.id_feuille
GROUP BY f.id_fichier, f.nb_lignes_total
HAVING f.nb_lignes_total < COUNT(li.id_ligne);
-- Attendu : 0 ligne (nb_lignes_total >= stockées toujours vrai)

```
**Vérification d'égalité stricte (test Python, pas SQL)** : l'égalité 
`nb_lignes_total = nb_lignes_stockees + nb_lignes_rejetees` **ne peut pas être vérifiée en SQL seul**, car `nb_lignes_rejetees` n'est pas stocké. **Elle doit être vérifiée dans un test d'intégration Python qui** :

1 - Lance `ingestion.py` sur un fichier de test.

2 - Récupère le retour de `ingerer_feuille (qui contient nb_stockees et nb_rejetees)`.

3 - Vérifie que `fichier.nb_lignes_total == nb_stockees + nb_rejetees`.

4 - `Vérifie que nb_stockees == COUNT(ligne_ingeree WHERE id_feuille = ...)`.

Point d'attention : si nb_lignes_total < COUNT(ligne_ingeree), c'est un bug d'ingestion (le compteur n'a pas été mis à jour, ou des lignes ont été insérées après coup). À surveiller dans les tests.

##### R7 — `feuille.nb_lignes` doit correspondre au COUNT de `ligne_ingeree`

Idem R6, pour chaque feuille.

**Vérification** :
```sql
SELECT fe.id_feuille, fe.nb_lignes, COUNT(li.id_ligne) AS reel
FROM feuille fe
LEFT JOIN ligne_ingeree li ON li.id_feuille = fe.id_feuille
GROUP BY fe.id_feuille, fe.nb_lignes
HAVING fe.nb_lignes != COUNT(li.id_ligne);
-- Attendu : 0 ligne
```

##### R8 — Un `ouvrage` sans `qualite_eau` a `qualite_eau IS NULL`, pas `'{}'`

**Garanti par** : `consolidation.py` utilise `None` pour `qualite_eau` quand aucun indicateur n'est trouvé. La colonne est nullable, donc `NULL` est stocké. `'{}'::jsonb` serait une erreur de convention.

**Vérification** :
```sql
SELECT id_ouvrage FROM ouvrage WHERE qualite_eau = '{}'::jsonb;
-- Attendu : 0 ligne (NULL est autorisé, '{}' ne l'est pas)
```

---

#### 2.3.4 Conventions de nommage

##### Tables et colonnes

- **Tables** : `snake_case`, au singulier (`source`, `localite`, `ouvrage`, `cgpe`). Une table représente un concept, pas une collection.
- **Colonnes** : `snake_case` (`id_ouvrage`, `nature_ouvrage`, `created_at`).
- **PK** : `id_<table_au_singulier>` (`id_source`, `id_localite`, `id_ouvrage`). Sauf `ouvrage_projet` qui a une PK composite `(id_ouvrage, id_projet)`.
- **FK** : même nom que la PK cible (`id_localite` dans `ouvrage` pointe vers `localite.id_localite`).
- **Booléens** : préfixe `est_` ou `a_` (`est_reingestion`, `a_cgpe`, `existe`). Exceptions : `actif` sur `source`.
- **Dates** : suffixe `_at` pour les timestamps (`created_at`, `updated_at`, `finished_at`), préfixe `date_` pour les `date` (`date_reception`, `date_creation`).
- **JSONB** : nom simple (`metadata`, `qualite_eau`). La colonne s'appelle `metadata` en base, mais l'attribut Python est `metadata_` (pour éviter le conflit avec `Base.metadata` de SQLAlchemy).

##### Clés JSONB

**Convention MVP** : les clés des attributs bruts sont préfixées par `brut_` (`brut_Type_Pompe`, `brut_Prof_Totale`). Le suffixe est **l'entête Excel d'origine**, tel quel (avec ses espaces, ses accents, sa casse). Cette convention est utilisée pour `metadata`, `qualite_eau` (partie brute), `localite.metadata`, `cgpe.metadata`, `ouvrage.metadata`.

**Pas de normalisation `snake_case` au MVP.** La normalisation des clés (`profondeur_forage_m`, `debit_l_s`...) est un travail **V2** (cf. `metadata_conventions.md` section 4, et promotion en attributs de première classe via `attribut_definition` + `ouvrage_attribut`). Au MVP, on préserve l'entête brut.

**`qualite_eau`** : deux types de clés coexistent :
- **Normalisées** : `onchocercose`, `vers_de_guinee`, `eau_salee`, `qualite_eau` (codes canoniques, `snake_case`, sans accents).
- **Brutes** : `brut_<entête>` (comme pour metadata).
- **Convention** : une valeur normalisée est **toujours** aussi présente en brut. Si on a `{"onchocercose": "Non", "brut_Onchocercose": "Non"}`, les deux clés coexistent.

**`mapping_feuille.champ_cible`** : la colonne stocke soit **un champ cible standard** (`region_brute`, `localite_brute`, `type_ouvrage_brut`...), soit une destination métadonnée explicite, soit NULL. Les trois cas :

| Valeur de champ_cible	                    | Effet à la consolidation	                                                                                                                                 | Cas d'usage                                                                                                                   |
|:------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------|
| <champ_standard> (ex. type_ouvrage_brut)	 | La valeur est extraite dans la colonne brute correspondante de ligne_ingeree (ex. ligne_ingeree.type_ouvrage_brut).	Colonne reconnue par COLUMN_PATTERNS. |
| metadata.ouvrage.<clé>	                   | La valeur est stockée dans ouvrage.metadata[<clé>] (préfixe brut_ non ajouté, la clé est explicite).	                                                     | L'utilisateur veut une clé stable et normalisée pour une exploitation ciblée (V2 : promotion en attribut de première classe). |
| metadata.localite.<clé>	                  | Idem, dans localite.metadata[<clé>].	                                                                                                                     | Idem.                                                                                                                         |
| metadata.cgpe.<clé>	                      | Idem, dans cgpe.metadata[<clé>].	                                                                                                                         | Idem.                                                                                                                         |
| NULL	                                     | La colonne va dans donnees_brutes uniquement (pas de normalisation, pas de métadonnée explicite).	                                                        | L'utilisateur a explicitement ignoré la colonne.                                                                              |

---

**Convention de clé pour `metadata.<entité>.<clé>`** :

* `<clé>` est en snake_case (ex. `profondeur_forage_m`, `nom_prestataire`).

* La clé est **stable** (pas de renommage une fois utilisée en production).

* La clé doit être **documentée** dans `metadata_conventions`.md (section 4) avant utilisation. Une PR qui ajoute une clé met à jour le doc.

* La valeur est typée : nombre pour les numériques, booléen pour les oui/non, chaîne ISO 8601 pour les dates. Pas de `null` : si la valeur est absente, la clé n'est pas écrite.

`metadata.<entité>.<clé>` vs `brut_<entête>` : les deux coexistent dans `metadata`. 
Une colonne mappée vers `metadata.ouvrage.profondeur_forage_m` produit à la fois `metadata["profondeur_forage_m"]` (clé explicite) et `metadata["brut_Prof_Totale"]` (clé brute, car `donnees_brutes` est toujours stocké). 
C'est volontaire : la clé explicite sert à l'exploitation, la clé brute sert à la traçabilité.

`donnees_brutes` **reste la source de vérité** : même si une colonne est mappée vers metadata.ouvrage.<clé>, sa valeur brute reste dans ligne_ingeree.donnees_brutes[<entête>]. On peut donc rejouer la consolidation avec un mapping différent sans réingérer.

**Exemple** : colonne Excel `Prof_Totale` mappée vers `metadata.ouvrage.profondeur_forage_m` :

* `ligne_ingeree.donnees_brutes["Prof_Totale"] = 58.5`

* `ouvrage.metadata["profondeur_forage_m"] = 58.5`

* `ouvrage.metadata["brut_Prof_Totale"] = 58.5`

##### Index

- **Format** : `idx_<table>_<colonne>` (`idx_ouvrage_etat`, `idx_ligne_statut_qualite`).
- **GIN** : suffixe `_trgm` pour les index trigram (`idx_localite_nom_trgm`).
- **Partiels** : suffixe `_not_null` (`idx_ouvrage_code` est partiel : `WHERE code_ouvrage IS NOT NULL`).

##### Contraintes

- **CHECK** : `<table>_<colonne>_check` (`ouvrage_nature_check`, `fichier_statut_check`).
- **UNIQUE** : `uq_<table>_<colonnes>` (`uq_alias_localite`, `uq_ref_geo_parent_nom_niveau`).
- **FK** : `<table>_<colonne>_fkey` (`ouvrage_id_localite_fkey`).
- **PK** : `<table>_pkey` (`ouvrage_pkey`).

##### Vues

- **Préfixe** : `v_<nom>` (`v_points_par_fichier`, `v_points_consolides`).
- **Suffixe descriptif** : `_par_fichier`, `_consolides`, `_par_fichier` (qualité).

##### Migrations

- **Format** : `<revision>_<description>.py` (ex. `0001_initial.py`).
- **Revision** : `0001_initial` pour la migration unique (on n'utilise plus les hashes Alembic).
- **Numérotation** : `0001`, `0002`, ... pour les suivantes.

---

#### 2.3.5 Règles de gestion (invariants du pipeline)

Ces règles ne sont **pas** des contraintes SQL, mais des invariants que le pipeline doit respecter. Elles sont testées manuellement (ou via des requêtes de vérification, cf. 2.3.3).

##### G1 — Ordre d'exécution du pipeline

```
import_localites → ingestion → rapprochement → consolidation
```

Chaque étape **dépend** de la précédente :
- `ingestion` a besoin de `localite` (pour rien, en fait — l'ingestion ne fait pas de rapprochement, elle stocke juste la ligne brute).
- `rapprochement` a besoin de `localite` peuplée (sinon 100% non résolu).
- `consolidation` a besoin de `ligne_ingeree.id_localite` rempli (sinon 0 ligne consolidée).

##### G2 — Un `ouvrage` est toujours créé à partir d'une `ligne_ingeree` **unique**

Le pipeline ne crée pas d'ouvrage "hors ligne". Chaque ouvrage est tracé par au moins une `ligne_ingeree` (`ligne_ingeree.id_ouvrage_consolide = ouvrage.id_ouvrage`). C'est ce qui permet de rejouer la consolidation.

**Exception** : si une ligne est supprimée après consolidation (`ON DELETE SET NULL` sur `ligne_ingeree.id_ouvrage_consolide`), l'ouvrage survit orphelin. C'est accepté (V2 : nettoyage).

##### G3 — Les feuilles de localités sont **ingérées** mais **ignorées** à la consolidation

Une feuille `Localités` est une feuille comme les autres : ses lignes sont stockées dans `ligne_ingeree`. Mais `consolidation.py` les ignore (`_est_feuille_localites`). Raison : une ligne de `Localités` n'est pas un ouvrage, c'est une localité. On garde la trace pour le debug, mais on ne la consolide pas.

**Impact carto** : ces lignes doivent aussi être exclues de la carte en mode Fichier (cf. 2.2.D, `v_points_par_fichier`).

##### G4 — Un `ouvrage` peut être mis à jour par plusieurs consolidations

Si deux fichiers mentionnent le même ouvrage (même `code_ouvrage` ou même tuple `(id_localite, nature, alimentation, annee)`), la consolidation **met à jour** l'ouvrage existant au lieu d'en créer un nouveau. Les champs vides sont complétés, les metadata et qualite_eau sont fusionnés.

##### G5 — `fichier.hash_sha256` n'est pas unique : la réingestion est légitime

Un même fichier peut être réingéré (correction de bug, changement de mapping). Le pipeline crée un nouveau `fichier` avec `est_reingestion = true`. Les anciennes lignes ne sont **pas** supprimées : les deux runs coexistent. C'est à l'utilisateur de décider lequel il garde (V2 : UI de gestion des versions).

##### G6 — `statut_qualite = 'ok'` est requis pour la consolidation

Une ligne avec `statut_qualite != 'ok'` n'est **jamais** consolidée. Les valeurs possibles :
- `'ok'` : ligne valide (coordonnées OK, localité résolue).
- `'localite_non_resolue'` : la localité n'a pas été trouvée au rapprochement. Non consolidée.
- `'geom_invalide'` : les coordonnées sont manquantes ou invalides. Non consolidée.
- `'type_ouvrage_inconnu'` : (V2) le type d'ouvrage n'a pas pu être déduit. Non consolidée.
- `'rejete'` : (V2) la ligne a été explicitement rejetée. Non consolidée.
- `'doublon_suspect'` : (V2) la ligne ressemble à une autre. Non consolidée.

##### G7 — Rejouer la consolidation nécessite un reset préalable

Pour rejouer la consolidation sur un run :
```sql
UPDATE ligne_ingeree SET id_ouvrage_consolide = NULL;
DELETE FROM ouvrage;
```
Sans ce reset, les lignes déjà consolidées ne seront pas retraitées (`id_ouvrage_consolide IS NOT NULL`).

**Attention** : `DELETE FROM ouvrage` supprime aussi les CGPE (`ON DELETE SET NULL` sur `cgpe.id_ouvrage`) et les liens `ouvrage_projet` (`ON DELETE CASCADE`). Au MVP, CGPE et ouvrage_projet sont vides, donc pas de perte.

##### G8 — Le pipeline est **idempotent** par run, pas par fichier

Réingérer le même fichier crée un nouveau `fichier` + un nouveau `run`. Les `ligne_ingeree` du run sont uniques (`UNIQUE (id_feuille, id_run, num_ligne_source)`), mais celles du run précédent existent toujours. C'est voulu : on peut comparer deux runs.

**Conséquence** : `SELECT COUNT(*) FROM ligne_ingeree` augmente à chaque réingestion. Pour ne compter que le dernier run :
```sql
SELECT COUNT(*) FROM ligne_ingeree WHERE id_run = (SELECT MAX(id_run) FROM ingestion_run);
```

##### G9 — Un `ouvrage` n'est jamais supprimé automatiquement

Pas de `DELETE FROM ouvrage` dans le pipeline. Les ouvrages ne sont supprimés que manuellement (reset). En V2, un mécanisme de "soft delete" (`actif = false`) pourra être ajouté.

##### G10 — Les coordonnées sont **toujours** en WGS84

`geom` est en `geometry(Point, 4326)` — WGS84, le standard GPS. Aucune autre projection n'est supportée. Si un fichier fournit des coordonnées dans un autre système (UTM, Lambert...), la conversion est de la responsabilité du service `coordonnees.py` (V2).

##### G11 — C'est le statut du run qui fait foi pour l'ingestion.**

> `fichier.statut` est un résumé (mis à jour à la fin du dernier run), mais c'est `ingestion_run.statut` qui est la source de vérité. 
> Pour savoir si un fichier a été correctement ingéré, on regarde le **dernier run** (`SELECT * FROM ingestion_run WHERE id_fichier = X ORDER BY started_at DESC LIMIT 1`). 
> Si ce run est `'termine'`, l'ingestion est valide. Si `'erreur'`, elle a échoué.

---

#### 2.3.6 Règles de validation (à implémenter en test)

Ces règles sont **testables** et doivent être vérifiées à chaque déploiement. Elles sont listées ici pour être transformées en tests dans la Phase 7.

| Code | Règle                                                                                                                                 | Vérification SQL                                                                                                                                                                       |
|------|---------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| R1   | `ouvrage.id_localite` pointe vers un nœud `localite`                                                                                  | cf. 2.3.3                                                                                                                                                                              |
| R2   | `cgpe.id_ouvrage` est de la même localité que `cgpe.id_localite`                                                                      | cf. 2.3.3                                                                                                                                                                              |
| R3   | Ligne consolidée → `id_localite` non NULL                                                                                             | cf. 2.3.3                                                                                                                                                                              |
| R4   | Ligne consolidée → `statut_qualite = 'ok'`                                                                                            | cf. 2.3.3                                                                                                                                                                              |
| R5   | Ouvrage → `geom` non NULL                                                                                                             | cf. 2.3.3                                                                                                                                                                              |
| R6   | `fichier.nb_lignes_total >= COUNT(ligne_ingeree)` (égalité stricte testée en Python)                                                  | cf. 2.3.3                                                                                                                                                                              |
| R7   | `feuille.nb_lignes` = COUNT `ligne_ingeree`                                                                                           | cf. 2.3.3                                                                                                                                                                              |
| R8   | `ouvrage.qualite_eau` n'est jamais `'{}'`                                                                                             | cf. 2.3.3                                                                                                                                                                              |
| R9   | Un `ouvrage` créé par consolidation a au moins une `ligne_ingeree.id_ouvrage_consolide`                                               | `SELECT id_ouvrage FROM ouvrage WHERE id_ouvrage NOT IN (SELECT id_ouvrage_consolide FROM ligne_ingeree WHERE id_ouvrage_consolide IS NOT NULL)` → 0 ligne (sauf données manuelles V2) |
| R10  | Pas de doublon `(id_localite, nature_ouvrage, type_alimentation, annee_realisation)` dans `ouvrage` (avec au moins un champ non NULL) | `SELECT id_localite, nature_ouvrage, type_alimentation, annee_realisation, COUNT(*) FROM ouvrage GROUP BY 1,2,3,4 HAVING COUNT(*) > 1` → 0 ligne                                       |

**Note R9** : cet invariant peut être violé si on supprime manuellement des `ligne_ingeree`. Au MVP, pas de suppression de lignes, donc R9 est valide. V2 : ajouter une contrainte ou un cleanup.

**Note R10** : la consolidation dédoublonne par `code_ouvrage` en priorité, puis par `(id_localite, nature_ouvrage, type_alimentation, annee_realisation)`. Donc deux ouvrages avec le même tuple ne devraient pas coexister, **sauf** si :
- L'un a un `code_ouvrage`, l'autre non.
- Les deux ont des `nature`/`alimentation`/`annee` NULL (et donc ne sont pas dédoublonnés par le tuple).

C'est un cas connu, accepté au MVP.

---

## 3. Pipeline d'ingestion

### 3.1 Vue d'ensemble et les 5 étapes

#### 3.1.1 Les 5 étapes

Le pipeline transforme un fichier Excel hétérogène en ouvrages consolidés, en 5 étapes **séquentielles** :

```text
┌─────────────────────────────────────────────────────────────────────┐
│  ÉTAPE 1 — IMPORT DES LOCALITÉS                                     │
│  (une seule fois, ou à chaque nouveau référentiel)                  │
│                                                                     │
│  Script   : scripts/import_localites.py <fichier.xlsx>              │
│  Service  : services/import_localites.py                            │
│                                                                     │
│  Entrée   : fichier Excel (feuille "Localités")                     │
│  Sortie   : ref_geo_admin (hiérarchie) + localite (noms + GPS)      │
│                                                                     │
│  Pré-requis : aucun                                                 │
│  Utilisé par : rapprochement (étape 3)                              │
└─────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────┐
│  ÉTAPE 2 — INGESTION                                                │
│  (à chaque nouveau fichier)                                         │
│                                                                     │
│  Endpoint : POST /fichiers (upload) + POST /fichiers/{id}/runs      │
│  Script   : scripts/test_ingestion_reelle.py <fichier.xlsx>         │
│  Service  : services/ingestion.py + services/coordonnees.py         │
│                                                                     │
│  Entrée   : fichier Excel (multi-feuilles)                          │
│  Sortie   : fichier, feuille, ingestion_run, ligne_ingeree          │
│             (donnees_brutes JSONB + coordonnées décimales)          │
│                                                                     │
│  Pré-requis : source seedée                                         │
│  Utilisé par : rapprochement (étape 3)                              │
└─────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────┐
│  ÉTAPE 3 — RAPPROCHEMENT                                            │
│  (par run, après ingestion)                                         │
│                                                                     │
│  Script   : scripts/test_rapprochement.py <id_run>                  │
│  Service  : services/rapprochement.py                               │
│                                                                     │
│  Entrée   : ligne_ingeree (localite_brute, statut_qualite='ok')     │
│  Sortie   : ligne_ingeree.id_localite (match exact/alias/trigram)   │
│             ligne_ingeree.statut_qualite (ok / localite_non_resolue)│
│                                                                     │
│  Pré-requis : localite peuplée (étape 1)                            │
│  Utilisé par : consolidation (étape 4)                              │
└─────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────┐
│  ÉTAPE 4 — CONSOLIDATION                                            │
│  (par run, après rapprochement)                                     │
│                                                                     │
│  Script   : scripts/consolidation.py <id_run>                       │
│  Service  : services/consolidation.py                               │
│                                                                     │
│  Entrée   : ligne_ingeree (statut_qualite='ok', id_localite rempli) │
│  Sortie   : ouvrage (dédoublonné, nature/alimentation/réalisation)  │
│             ligne_ingeree.id_ouvrage_consolide                      │
│                                                                     │
│  Pré-requis : ligne_ingeree.id_localite rempli (étape 3)            │
│  Utilisé par : lecture/export/carto (étape 5)                       │
└─────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────┐
│  ÉTAPE 5 — LECTURE / EXPORT / CARTO                                 │
│                                                                     │
│  Endpoints : GET /ouvrages, /ouvrages/export,                       │
│              /carto/tous/points, /carto/fichiers/{id}/points,       │
│              /qualite/fichiers/{id}                                 │
│                                                                     │
│  Source   : ouvrage (consolidé) + ligne_ingeree (brut)              │
└─────────────────────────────────────────────────────────────────────┘
```

**Point clé** : les étapes 1 à 4 sont **indépendantes** et **rejouables**. Chaque étape lit ce que la précédente a produit. Si on améliore le mapping, on rejoue l'ingestion (étape 2) puis le rapprochement (étape 3) puis la consolidation (étape 4). Si on améliore le rapprochement, on rejoue les étapes 3 et 4. Si on améliore la consolidation, on rejoue l'étape 4.

#### 3.1.2 Le pipeline automatique (production)

En production, l'utilisateur lance **un seul appel** :

```http
POST /fichiers/{id}/runs?mode=complet
```

Le service `run.py` orchestre **les étapes 2, 3 et 4** en séquence (asynchrone, BackgroundTask) :

```
1. ingerer_fichier()          → ligne_ingeree
2. rapprocher_lignes_run()    → id_localite
3. consolider_lignes_run()    → ouvrage
```

L'étape 1 (import localités) reste **manuelle** au MVP (script CLI). En V2, elle pourra être intégrée à l'upload si la feuille `Localités` est détectée.

#### 3.1.3 Le pipeline manuel (scripts CLI)

Pour le **développement**, le **débogage** et l'**administration**, chaque étape est exposée par un script CLI :

| Script                             | Étape | Rôle                   |
|------------------------------------|-------|------------------------|
| `scripts/import_localites.py`      | 1     | Import des localités   |
| `scripts/test_ingestion_reelle.py` | 2     | Ingestion d'un fichier |
| `scripts/test_rapprochement.py`    | 3     | Rapprochement d'un run |
| `scripts/consolidation.py`         | 4     | Consolidation d'un run |

Ces scripts **restent disponibles** après la mise en production. Ils servent à :
- Tester un fichier avant de l'uploader.
- Rejouer une étape après un changement de code.
- Débloquer un run (ex. rapprochement manuel après ajout de localités).
- Diagnostiquer un problème (stats par run).

**Pré-requis** : les scripts doivent être exécutés **dans le conteneur backend** (`docker compose exec backend python ...`) pour avoir accès à la base et aux fichiers.

#### 3.1.4 Les modes d'ingestion

L'étape 2 (ingestion) supporte **3 modes**, contrôlés par `ingestion_run.mode` :

| Mode          | Paramètres                       | Usage                                                  |
|---------------|----------------------------------|--------------------------------------------------------|
| `complet`     | aucun                            | Ingérer tout le fichier (par défaut)                   |
| `echantillon` | `limite_lignes` (int)            | Ingérer seulement les N premières lignes (test rapide) |
| `plage`       | `ligne_debut`, `ligne_fin` (int) | Ingérer une plage de lignes (debug, reprise)           |

**Contrainte** : `chk_run_mode_params` (cf. 2.2.B) vérifie la cohérence entre `mode` et les paramètres.

**Au MVP** : seul le mode `complet` est utilisé en production. Les modes `echantillon` et `plage` sont disponibles via les scripts CLI (utiles pour tester un nouveau fichier sans ingérer 10 000 lignes).

#### 3.1.5 Les états du fichier et du run

**`fichier.statut`** :

| Statut       | Signification                               | Transition                                        |
|--------------|---------------------------------------------|---------------------------------------------------|
| `en_attente` | Fichier uploadé, pas encore ingéré          | → `en_cours` quand un run démarre                 |
| `en_cours`   | Ingestion en cours                          | → `ingere` / `partiel` / `erreur`                 |
| `ingere`     | Toutes les feuilles ingérées avec succès    | État final                                        |
| `partiel`    | Certaines feuilles ont échoué, d'autres non | État final (V2 : relancer les feuilles en erreur) |
| `erreur`     | Aucune feuille n'a pu être ingérée          | État final                                        |

**`ingestion_run.statut`** :

| Statut     | Signification                                 | Transition                     |
|------------|-----------------------------------------------|--------------------------------|
| `en_cours` | Run en cours                                  | → `termine` / `erreur`         |
| `termine`  | Run terminé, lignes ingérées > 0              | État final                     |
| `erreur`   | Run terminé, 0 lignes ingérées (ou exception) | État final                     |
| `annule`   | Run annulé par l'utilisateur                  | **Non implémenté au MVP** (V2) |

**Point d'attention** : un run peut être en `erreur` alors que le fichier est en `ingere` (si les autres runs ont réussi). C'est le fichier qui fait foi pour l'état global.

Parfait, on met la Bible à jour. Voici la **section 3.1.6 révisée** avec les règles précises pour les 6 statuts de qualité, à substituer à la version actuelle.

---

#### 3.1.6 Les statuts de qualité

Chaque `ligne_ingeree` porte un `statut_qualite` qui évolue au fil du pipeline. Ce statut qualifie la ligne **individuellement** (pas le run, pas le fichier). Il est agrégé dans `v_qualite_par_fichier` pour le tableau de bord.

**Récapitulatif des compteurs** :
- `nb_lignes_total` = `nb_lignes_stockees` + `nb_lignes_rejetees`.
- `nb_lignes_stockees` = `COUNT(ligne_ingeree)` pour le fichier.
- `nb_lignes_rejetees` = lignes de total/sous-total (détectées, non stockées).
- `nb_lignes_vides` = lignes entièrement vides (ignorées, non comptées).

##### Les 6 statuts

| Statut                   | Écrit par     | Signification                                         | Consolidé ?       |
|--------------------------|---------------|-------------------------------------------------------|-------------------|
| `'ok'`                   | ingestion     | Ligne valide à toutes les étapes                      | Oui               |
| `'geom_invalide'`        | ingestion     | Coordonnées GPS manquantes ou invalides               | Non               |
| `'localite_non_resolue'` | rapprochement | Localité non trouvée dans le référentiel              | Non               |
| `'type_ouvrage_inconnu'` | consolidation | Ouvrage créé, mais attributs métier indéterminés      | Oui (mais marqué) |
| `'rejete'`               | ingestion     | Ligne manifestement inexploitable (total, sous-total) | Non (non stockée) |
| `'doublon_suspect'`      | consolidation | Code ouvrage déjà vu, coordonnées très différentes    | Non               |


##### Détail des règles

**`'ok'`**
- **Quand** : la ligne a des coordonnées valides, sa localité est résolue, et ses attributs métier sont exploitables.
- **Écrit par** : `ingestion.py` (valeur par défaut si lat/lon valides), puis confirmé par `rapprochement.py` (si la localité est trouvée), puis par `consolidation.py` (si les attributs ne sont pas tous indéterminés).
- **Consolidé** : oui.
- **C'est le cas normal** : la grande majorité des lignes d'un fichier sain.

**`'geom_invalide'`**
- **Quand** : `latitude_decimal` ou `longitude_decimal` est NULL après `parser_coordonnees`. Cela couvre :
  - Cellule vide.
  - Valeur non numérique.
  - Valeur hors bornes (`lat` hors [-90, 90], `lon` hors [-180, 180]).
  - `(0, 0)` (coordonnée nulle par défaut).
- **Écrit par** : `ingestion.py` (à l'extraction).
- **Consolidé** : non. Un ouvrage sans coordonnées n'existe pas.
- **Message** : `message_qualite = "Coordonnées manquantes ou invalides"`.

**`'localite_non_resolue'`**
- **Quand** : la ligne a des coordonnées valides, mais `rapprochement.py` n'a pas trouvé de localité correspondante (`exact match`, `alias`, ni `trigram > 0.6`).
- **Écrit par** : `rapprochement.py`.
- **Consolidé** : non. Un ouvrage sans localité ne peut pas être rattaché à la hiérarchie administrative.
- **Message** : `message_qualite = "Localité non résolue : <localite_brute>"`.

**`'type_ouvrage_inconnu'`**
- **Quand** : la ligne est valide (coordonnées OK, localité résolue), mais **après consolidation**, les 3 attributs métier sont indéterminés :
  - `nature_ouvrage = 'inconnu'`
  - `type_alimentation = 'AUTRE'`
  - `realisation_par = 'inconnu'`
- **Écrit par** : `consolidation.py`, **après** création ou mise à jour de l'ouvrage.
- **Consolidé** : **oui**, l'ouvrage est créé avec ses attributs `inconnu`/`AUTRE`/`inconnu`, mais la ligne est marquée pour signaler qu'elle est à qualifier.
- **Pourquoi consolider quand même** : l'ouvrage existe physiquement (coordonnées OK, localité OK), c'est juste ses attributs qui manquent. On le crée pour qu'il apparaisse sur la carte, et on le marque pour que l'utilisateur puisse le requalifier (V2).
- **Message** : `message_qualite = "Attributs métier indéterminés (nature, alimentation, réalisation)"`.

**`'rejete'`**
- **Quand** : la ligne est **manifestement inexploitable**. Détection automatique dans `ingestion.py` :
  - La ligne contient un des mots-clés suivants dans l'une de ses cellules texte (insensible à la casse et aux accents) : `"total"`, `"sous-total"`, `"somme"`, `"cumul"`.
  - C'est une ligne de total ou sous-total d'un tableau.
- **Écrit par** : `ingestion.py`, **avant** la tentative d'insertion.
- **Consolidé** : non. **La ligne n'est pas stockée du tout** (pas de `ligne_ingeree` créée). On incrémente juste le compteur `nb_rejetes` dans `v_qualite_par_fichier`.
- **Pourquoi ne pas stocker** : les lignes de total polluent la base (`donnees_brutes` rempli de `"TOTAL"`, `"12345"`...). Elles n'ont aucune valeur métier. Les compter dans la vue Qualité suffit pour savoir combien ont été rejetées.
- **Exception V2** : si l'utilisateur veut voir les lignes rejetées pour les corriger manuellement, on pourra les stocker. Au MVP, non.

**`'doublon_suspect'`**
- **Quand** : la ligne a un `code_ouvrage`, un ouvrage existe déjà avec ce code dans la base, **mais** les coordonnées de la ligne sont à plus de **1 km** de celles de l'ouvrage existant.
- **Écrit par** : `consolidation.py`, **avant** la consolidation.
- **Consolidé** : non. On ne fusionne pas, on ne crée pas. On signale.
- **Pourquoi** : si deux lignes ont le même `code_ouvrage` mais sont à des endroits très différents, c'est probablement une erreur (mauvais code, code réutilisé par erreur, mauvaise coordonnée). Il vaut mieux ne pas consolider et laisser l'utilisateur décider (V2 : UI de résolution).
- **Seuil** : `1 km` (distance géodésique, via `ST_Distance` de PostGIS).
- **Message** : `message_qualite = "Code ouvrage <code> déjà utilisé à <distance> km"`.

##### Priorité des statuts (ordre d'évaluation)

Une ligne peut remplir plusieurs conditions. L'ordre d'évaluation est :

1. '`rejete`'               (ingestion — avant tout)
2. '`geom_invalide`'        (ingestion — après coordonnées)
3. '`localite_non_resolue`' (rapprochement)
4. '`doublon_suspect`'      (consolidation — avant création)
5. '`type_ouvrage_inconnu`' (consolidation — après création)
6. '`ok`'                   (défaut, si aucune autre condition)


Une ligne `'rejete'` **n'est pas stockée**, donc elle ne peut pas être `'geom_invalide'` aussi. Une ligne `'geom_invalide'` ne peut pas être `'localite_non_resolue'` (le rapprochement ne la traite pas). Une ligne `'localite_non_resolue'` ne peut pas être `'doublon_suspect'` (la consolidation l'ignore). Une ligne `'doublon_suspect'` ne peut pas être `'type_ouvrage_inconnu'` (elle n'est pas consolidée).

**Les seuls cas cumulables** :
- Une ligne peut être `'ok'` à l'ingestion et au rapprochement, puis `'type_ouvrage_inconnu'` à la consolidation. C'est le cas normal d'une ligne valide mais aux attributs incomplets.
- Une ligne `'type_ouvrage_inconnu'` reste `'type_ouvrage_inconnu'` (elle n'est pas "améliorée" en `'ok'`).

##### Récapitulatif visuel

```text

        Ingestion          Rapprochement       Consolidation
        ─────────          ─────────────       ─────────────
        
        Ligne de total
        │
        ▼
        'rejete' (non stockée)
        
        Ligne normale
        │
        ▼
        lat/lon valides ?
        │
        ├── NON ──▶ 'geom_invalide' (non consolidé)
        │
        └── OUI ──▶ 'ok'
        │
        ▼
        localité trouvée ?
        │
        ├── NON ──▶ 'localite_non_resolue' (non consolidé)
        │
        └── OUI ──▶ 'ok'
        │
        ▼
        code déjà vu à > 1 km ?
        │
        ├── OUI ──▶ 'doublon_suspect' (non consolidé)
        │
        └── NON ──▶ (création/update ouvrage)
        │
        ▼
        nature+alim+réal tous inconnus ?
        │
        ├── OUI ──▶ 'type_ouvrage_inconnu' (consolidé, marqué)
        │
        └── NON ──▶ 'ok' (consolidé)
```

##### Effet sur `v_qualite_par_fichier`

La vue compte les lignes par statut. **Cohérence attendue** :

```text
nb_ok + nb_localite_non_resolue + nb_geom_invalide + nb_type_inconnu + nb_rejetes + nb_doublon_suspect = nb_lignes_total
```

**Attention** : `nb_rejetes` compte les lignes **non stockées**. Donc `nb_lignes_total` doit être mis à jour pour inclure les rejetées. Sinon la somme ne sera pas cohérente.

**Solution** : `ingestion.py` met à jour `fichier.nb_lignes_total = nb_lignes_stockees + nb_lignes_rejetees`. La vue `v_qualite_par_fichier` fait `COUNT(ligne_ingeree)` pour les 5 statuts stockés, et `nb_lignes_total - COUNT(ligne_ingeree)` pour `nb_rejetes`. Ou plus simple : `nb_rejetes = fichier.nb_lignes_total - COUNT(ligne_ingeree)`.

**Décision** : je recommande `nb_rejetes = fichier.nb_lignes_total - COUNT(ligne_ingeree)` dans la vue. C'est cohérent et ne nécessite pas de stocker les lignes rejetées.

##### Effet sur les scripts CLI

Les scripts `test_ingestion_reelle.py`, `test_rapprochement.py`, `consolidation.py` doivent afficher les stats **par statut** à la fin de chaque étape :

```text
Ingestion :
Lignes lues : 1307
Lignes stockées : 1300
Lignes rejetées (total/sous-total) : 7
Lignes 'ok' : 1250
Lignes 'geom_invalide' : 50

Rapprochement :
Total lignes 'ok' : 1250
Exact match : 900
Alias : 0
Trigram : 200
Non résolu : 150  → 'localite_non_resolue'

Consolidation :
Lignes à consolider : 1100
Ouvrages créés : 800
Ouvrages mis à jour : 250
Doublons suspects : 50  → 'doublon_suspect'
Attributs indéterminés : 30  → 'type_ouvrage_inconnu'
```

---

#### 3.1.7 Les tables impactées à chaque étape

| Étape                   | Tables lues                                       | Tables écrites                                         |
|-------------------------|---------------------------------------------------|--------------------------------------------------------|
| **1. Import localités** | —                                                 | `ref_geo_admin`, `localite`, `localite_alias` (V2)     |
| **2. Ingestion**        | `source`, `fichier`, `feuille`, `mapping_feuille` | `fichier`, `feuille`, `ingestion_run`, `ligne_ingeree` |
| **3. Rapprochement**    | `ligne_ingeree`, `localite`, `localite_alias`     | `ligne_ingeree` (id_localite, statut_qualite)          |
| **4. Consolidation**    | `ligne_ingeree`, `localite`, `fichier`, `feuille` | `ouvrage`, `ligne_ingeree` (id_ouvrage_consolide)      |
| **5. Lecture**          | `ouvrage`, `ligne_ingeree`, `localite`            | —                                                      |

**Aucune étape n'écrit dans** :
- `source` (seedé une fois)
- `cgpe` (V2)
- `projet_financement` (V2)
- `ouvrage_projet` (V2)

---

### 3.2 Détail de chaque étape

Cette section décrit, pour chaque étape du pipeline, l'**algorithme**, les **fonctions**, les **règles de décision**, les **cas limites** et les **messages produits**. Elle fait autorité sur le code des services (`services/*.py`).

Chaque sous-section suit la même structure :
- **Rôle** : ce que fait l'étape.
- **Entrées / Sorties** : tables lues et écrites.
- **Algorithme** : déroulé précis.
- **Règles de décision** : comment on choisit un statut, une valeur, un message.
- **Cas limites** : ce qui est géré, ce qui ne l'est pas.
- **Erreurs** : ce qui fait échouer l'étape.

---

#### 3.2.1 Ingestion (`services/ingestion.py`)

**Rôle** : lire un fichier Excel multi-feuilles, extraire les lignes brutes, les normaliser partiellement (coordonnées, localité, attributs standardisés), et les insérer dans `ligne_ingeree`. C'est l'étape 2 du pipeline.

**Entrées**
- `fichier` (chemin, id_source, id_fichier) — déjà créé par `upload.py`.
- `feuille` (1..N) — déjà créées par `upload.py`.
- `mapping_feuille` — mapping validé par l'utilisateur (prioritaire), sinon mapping auto (recalculé via `COLUMN_PATTERNS`).
- `ingestion_run` — créé par `run.py`, porte `mode` (`complet` / `echantillon` / `plage`) et ses paramètres.

**Sorties**
- `ligne_ingeree` — une ligne par ligne Excel non vide et non rejetée.
- `feuille.nb_lignes` — nombre de lignes **extraites** (hors rejets et hors lignes vides).
- `feuille.nb_lignes_valides` — nombre de lignes avec `statut_qualite = 'ok'` (donc lat/lon valides).
- `feuille.statut_ingestion` — `'ingere'` ou `'erreur'`.
- `fichier.nb_lignes_total` — **`nb_lignes_stockees + nb_lignes_rejetees`** (cf. décision C4).
- `ingestion_run.nb_lignes_ingerees` — nombre total de lignes stockées.

**Ce que l'ingestion NE fait PAS**
- Elle **ne met pas à jour `fichier.statut`** (c'est `run.py` qui le fait en fin de pipeline, cf. décision A3).
- Elle **ne fait pas de rapprochement** (pas de résolution `localite_brute` → `id_localite`).
- Elle **ne fait pas de consolidation** (pas de création d'`ouvrage`).
- Elle **ne détecte pas les doublons** (c'est la consolidation).

##### Algorithme

Pour chaque `feuille` du `fichier` :

1. **Ouvrir le classeur** (`openpyxl.load_workbook`, `read_only=True`, `data_only=True`).
2. **Détecter la ligne d'entête** (`_detecter_header_row`) :
    - Parcourt les 30 premières lignes.
    - Retient la ligne avec le **plus grand nombre de cellules non vides uniques** (`>= 5`).
    - Ignore les lignes de séparateurs (`---`, `___`, `===`).
    - S'arrête dès qu'une ligne a `>= 10` colonnes uniques.
    - Retourne l'index (1-based) de la meilleure ligne.
3. **Charger le mapping** (`charger_mapping_pour_ingestion`) :
    - Priorité 1 : mappings `valide_par_utilisateur = true` en base.
    - Priorité 2 : mapping auto via `_analyser_entetes` + `COLUMN_PATTERNS`.
    - Retourne `{idx_col: champ_cible}`.
4. **Extraire les lignes** (`_extraire_lignes`) — une seule passe sur `ws.iter_rows` :
    - Ignorer les lignes **entièrement vides** (toutes cellules `None` ou `""`).
    - **Détecter les rejets** (cf. règles ci-dessous) → **ne pas stocker**, incrémenter `nb_rejetes`.
    - Pour chaque ligne non rejetée :
        - Construire `record` avec les champs mappés.
        - Parser les coordonnées (`parser_coordonnees`) → `latitude_decimal`, `longitude_decimal`.
        - Sérialiser **toutes** les cellules dans `donnees_brutes` (clé = entête brut, valeur sérialisée ISO pour les dates).
        - Extraire `type_ouvrage_brut` (fallback : code déduit du nom de feuille si `PMH`/`HVA`/`PEA`/`HV` présent).
        - Extraire `usage_ouvrage_brut` (P12).
        - Extraire `a_cgpe` via `_to_bool` (`oui`/`non`/`1`/`0`/`true`/`false`).
5. **Insérer** chaque `record` dans `ligne_ingeree` :
    - `statut_qualite = 'geom_invalide'` si `latitude_decimal` ou `longitude_decimal` est `NULL`.
    - `statut_qualite = 'ok'` sinon.
    - `message_qualite = "Coordonnées manquantes ou invalides"` si `geom_invalide`, sinon `NULL`.
    - `id_localite = NULL` (rempli plus tard par le rapprochement).
    - `id_ouvrage_consolide = NULL` (rempli plus tard par la consolidation).
6. **Mettre à jour `feuille`** :
    - `nb_lignes = len(lignes_stockees)`.
    - `nb_lignes_valides = count(statut_qualite = 'ok')`.
    - `statut_ingestion = 'ingere'` (ou `'erreur'` si exception, avec `message_erreur = str(e)`).
7. **Mettre à jour `fichier.nb_lignes_total = nb_lignes_stockees + nb_rejetees`** (décision C4).
8. **Mettre à jour `ingestion_run.nb_lignes_ingerees`** (cumul des feuilles).

##### Règles de décision

**Détection des rejets** (statut `'rejete'`, **ligne non stockée**) :
- Une ligne est rejetée si **l'une de ses cellules texte** contient (insensible à la casse et aux accents) un des mots-clés : `total`, `sous-total`, `somme`, `cumul`.
- La détection se fait **avant** l'insertion. La ligne n'est **jamais** stockée dans `ligne_ingeree`.
- `nb_rejetes` est incrémenté et reporté dans `fichier.nb_lignes_total` (mais **pas** dans `ligne_ingeree`).
- **Pourquoi ne pas stocker** : les lignes de total polluent la base (`donnees_brutes` rempli de `"TOTAL"`, `"12345"`). Aucune valeur métier. V2 : possibilité de les stocker pour correction manuelle.

**Détection des lignes vides** :
- Une ligne est vide si **toutes** ses cellules sont `None` ou `""`.
- Elle est **ignorée** (ni stockée, ni comptée dans `nb_rejetes`). Elle **n'est pas comptée** dans `nb_lignes_total` non plus (elle ne fait pas partie du fichier utile).

**Statut `'geom_invalide'`** :
- Écrit à l'ingestion si `latitude_decimal IS NULL` OU `longitude_decimal IS NULL`.
- Couvre : cellule vide, valeur non numérique, valeur hors bornes (`lat` hors `[-90, 90]`, `lon` hors `[-180, 180]`), `(0, 0)`.
- `message_qualite = "Coordonnées manquantes ou invalides"`.
- **Consolidé** : non (la consolidation ignore `statut_qualite != 'ok'`).

**Statut `'ok'`** :
- Écrit à l'ingestion si lat/lon valides.
- **Confirmé** par le rapprochement (si localité trouvée) et la consolidation (si attributs non tous indéterminés).
- Peut devenir `'localite_non_resolue'` (rapprochement) ou `'type_ouvrage_inconnu'` (consolidation).

**Fallback `type_ouvrage_brut` depuis nom de feuille** :
- Si le nom de la feuille contient `PMH`, `HVA`, `PEA` ou `HV` (insensible à la casse), et que la colonne `type_ouvrage_brut` est vide, alors `type_ouvrage_brut = <code>`.
- Ce fallback est **prioritaire** sur une éventuelle valeur de colonne (le nom de feuille est plus fiable, cf. 1.6 contrainte 2). En pratique, on écrit le code feuille **dans `type_ouvrage_brut`** avant la consolidation.

##### Cas limites gérés

| Cas                                        | Comportement                                                                                                 |
|--------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| Fichier avec une seule feuille             | Traité normalement.                                                                                          |
| Fichier avec feuille `Localités`           | Ingérée normalement (les lignes sont stockées). Ignorée à la consolidation (`_est_feuille_localites`).       |
| Feuille vide (0 ligne)                     | `nb_lignes = 0`, `statut_ingestion = 'ingere'`. Pas d'erreur.                                                |
| Feuille sans entête détectable             | `_detecter_header_row` retourne 1 par défaut. Les lignes sont lues à partir de la ligne 2.                   |
| Colonne `Type_Ouvrage` avec `"Forage ADM"` | Stockée brute dans `type_ouvrage_brut`. Interprétée à la consolidation (`_map_nature` + `_map_realisation`). |
| DMS compact (`075225`)                     | Parsé par `parser_coordonnees` (via `coordonnees.py`), signe forcé pour la CI.                               |
| DMS corrompu (1 ligne)                     | `latitude_decimal = NULL` → `statut_qualite = 'geom_invalide'`. Cas normal.                                  |
| Virgule décimale (`7,0291`)                | Parsée par `parser_coordonnees`.                                                                             |
| Inversion lat/lon                          | Corrigée par `parser_coordonnees` (via `_corriger_ci`).                                                      |

##### Erreurs

- **Fichier introuvable** : `HTTPException(404)`.
- **Feuille introuvable dans le classeur** : `HTTPException(404)`.
- **Exception à l'ouverture** (fichier corrompu) : `HTTPException(400)`.
- **Exception dans `ingerer_feuille`** : `db.rollback()` + `feuille.statut_ingestion = 'erreur'` + `feuille.message_erreur = str(e)`. Le pipeline continue sur les autres feuilles (comportement `'partiel'`).
- **Toutes les feuilles en erreur** : `fichier.statut = 'erreur'` (mis à jour par `run.py`).

---

#### 3.2.2 Rapprochement (`services/rapprochement.py`)

**Rôle** : résoudre `ligne_ingeree.localite_brute` (texte libre) vers `localite.id_localite` (référentiel). C'est l'étape 3 du pipeline.

**Entrées**
- `ligne_ingeree` avec `statut_qualite = 'ok'` et `id_localite IS NULL`.
- `localite` (référentiel peuplé par `import_localites.py`).
- `localite_alias` (V2, vide au MVP).

**Sorties**
- `ligne_ingeree.id_localite` — rempli si résolu.
- `ligne_ingeree.statut_qualite` — passe à `'localite_non_resolue'` si non résolu.
- `ligne_ingeree.message_qualite` — `"Localité non résolue : <localite_brute>"` si non résolu.

**Ce que le rapprochement NE fait PAS**
- Il **ne traite pas** les lignes `geom_invalide` (elles n'ont pas de coordonnées, mais elles pourraient avoir une localité — décision MVP : on ne les rapproche pas, elles ne seront jamais consolidées).
- Il **ne crée pas** de localité (V2 : création manuelle ou UI de correction).
- Il **n'écrit pas** dans `localite_alias` (V2 : apprentissage sur correction).

##### Algorithme

Pour chaque ligne à rapprocher, dans l'ordre :

1. **Normaliser** `localite_brute` (`_normaliser`) :
    - `strip()`, `lower()`.
    - Suppression des accents (`unicodedata.normalize("NFD")` + filtre `Mn`).
    - Compactage des espaces / tirets / underscores en un seul espace.
    - Résultat : `nom_norm`.

2. **Match exact** sur `localite.nom_usage` normalisé :
    - `SELECT id_localite FROM localite WHERE unaccent(lower(regexp_replace(nom_usage, '[\s\-_]+', ' ', 'g'))) = :nom_norm LIMIT 1`.
    - Si trouvé → `id_localite`, méthode `'exact'`.

3. **Match alias** (V2, table vide au MVP) :
    - `SELECT id_localite FROM localite_alias WHERE unaccent(lower(alias)) = :nom_norm LIMIT 1`.
    - Si trouvé → `id_localite`, méthode `'alias'`.

4. **Match trigram** (similarité `> 0.6`) :
    - `SELECT id_localite, similarity(unaccent(lower(nom_usage)), :nom_norm) AS score FROM localite WHERE similarity(...) > :seuil ORDER BY score DESC LIMIT 1`.
    - Si trouvé → `id_localite`, méthode `'trigram'`.

5. **Aucun match** :
    - `statut_qualite = 'localite_non_resolue'`.
    - `message_qualite = "Localité non résolue : <localite_brute>"` (format **strict**, sans suffixe debug — décision A2).
    - Méthode `'non_resolu'`.

##### Règles de décision

- **Seuil trigram** : `0.6` (paramétrable via `seuil_trigram`). Au MVP, `0.6` est utilisé partout.
- **Priorité** : exact > alias > trigram. Dès qu'un match est trouvé, on s'arrête.
- **Pas de filtre par sous-préfecture** : le match se fait sur `nom_usage` global. Risque de faux positif si deux localités homonymes dans des sous-préfectures différentes. Accepté au MVP (cf. 1.6 contrainte 6). V2 : utiliser `sous_prefecture_brute` pour désambiguïser.
- **`message_qualite`** : format strict `"Localité non résolue : <localite_brute>"`. Pas de suffixe `(méthode: ...)`. Le détail de la méthode n'est pas exposé (V2 : champ séparé si besoin).
- **`localite_brute` vide** (`NULL` ou `""`) : traité comme `'localite_non_resolue'` avec message `"Localité non résolue : ''"`. Pas d'exception.

##### Cas limites gérés

| Cas                                           | Comportement                                                                                                     |
|-----------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| `localite_brute = NULL`                       | `statut_qualite = 'localite_non_resolue'`, message avec `''`.                                                    |
| `localite_brute = "Camp X"` (alias non connu) | Trigram > 0.6 → match. Sinon → non résolu.                                                                       |
| Deux localités homonymes                      | Le premier match (exact ou trigram) gagne. Risque de faux positif accepté.                                       |
| `localite_brute = "ABIDJAN-COCODY"`           | Normalisation → `"abidjan cocody"`. Pas de match exact. Trigram peut matcher `"Cocody"` si présente.             |
| Feuille `Localités`                           | Les lignes sont rapprochées normalement (elles ont un `localite_brute` qui pointe vers elles-mêmes). Idempotent. |

##### Erreurs

- **Aucune exception** n'est levée par le rapprochement. Les lignes non résolues sont marquées, pas rejetées.
- **Base non peuplée** (0 localité) : 100 % des lignes passent en `'localite_non_resolue'`. ces lignes ne seront jamais **consolidées** (elles restent `'localite_non_resolue'`).
 Cas normal si `import_localites.py` n'a pas été lancé.

---

#### 3.2.3 Consolidation (`services/consolidation.py`)

**Rôle** : transformer les `ligne_ingeree` valides (statut `'ok'`, `id_localite` rempli) en `ouvrage` dédoublonnés, avec attributs normalisés (`nature_ouvrage`, `type_alimentation`, `realisation_par`, `etat`), `metadata` et `qualite_eau`. C'est l'étape 4 du pipeline.

**Entrées**
- `ligne_ingeree` avec `statut_qualite = 'ok'` et `id_localite IS NOT NULL`.
- `localite`, `feuille`, `fichier` (pour le nom de feuille et l'exclusion des feuilles `Localités`).
- `ouvrage` existants (pour le dédoublonnage).

**Sorties**
- `ouvrage` — créé ou mis à jour.
- `ligne_ingeree.id_ouvrage_consolide` — rempli.
- `ligne_ingeree.statut_qualite` — peut passer à `'doublon_suspect'` (avant création) ou `'type_ouvrage_inconnu'` (après création).

**Ce que la consolidation NE fait PAS**
- Elle **ne crée pas** de `cgpe` (V2).
- Elle **ne crée pas** de `projet_financement` ni `ouvrage_projet` (V2).
- Elle **ne modifie pas** `localite` (pas de mise à jour de `metadata` de localité).
- Elle **ne supprime jamais** d'`ouvrage` (G9).

##### Algorithme

Pour chaque ligne à consolider :

1. **Filtrer** :
    - `statut_qualite != 'ok'` → ignorer.
    - `id_localite IS NULL` → ignorer.
    - `latitude_decimal IS NULL` ou `longitude_decimal IS NULL` → ignorer (déjà `geom_invalide`, mais ceinture et bretelles).
    - `_est_feuille_localites(nom_feuille)` → ignorer (feuille `Localités`, `Village`, `Campement`).

2. **Calculer les attributs normalisés** :
    - `nature_ouvrage = _map_nature(type_ouvrage_brut, nom_feuille)`.
    - `type_alimentation = _map_alimentation(type_ouvrage_brut, usage_ouvrage_brut, nom_feuille)`.
    - `realisation_par = _map_realisation(donnees_brutes, type_ouvrage_brut)`.
    - `etat = _map_etat(etat_ouvrage_brut)`.

3. **Chercher un `ouvrage` existant** (`_trouver_ouvrage_existant`) :
    - **Priorité 1** : `code_ouvrage` identique (extrait de `donnees_brutes` ou de `code_ouvrage_brut`).
    - **Priorité 2** : `(id_localite, nature_ouvrage, type_alimentation, annee_realisation)` identiques, **avec au moins un champ non NULL** (sinon on ne peut pas dédoublonner).
    - Si trouvé → **mise à jour** (champs vides complétés, `metadata` et `qualite_eau` fusionnés).
    - Si non trouvé → **création**.

4. **Détection `doublon_suspect`** (avant création/mise à jour) :
    - Si `code_ouvrage` est renseigné **et** qu'un `ouvrage` existe déjà avec ce code **et** que la distance entre la ligne et l'ouvrage existant est **> 1 km** (`ST_Distance` en géodésique).
    - Alors : `statut_qualite = 'doublon_suspect'`, `message_qualite = "Code ouvrage <code> déjà utilisé à <distance> km"`. **Ne pas consolider** (ne pas créer, ne pas mettre à jour).
    - Seuil : `1 km`. Constante `SEUIL_DOUBLON_KM = 1.0`.

5. **Extraire `metadata`** :
    - Toutes les colonnes de `donnees_brutes` non mappées vers un champ standard.
    - Convention : `brut_<entête Excel d'origine>` (décision B1).
    - Ne pas mettre de valeur `None`.

6. **Extraire `qualite_eau`** (`_extraire_qualite_eau`) :
    - Parcourir les entêtes de `donnees_brutes`.
    - Si un entête matche un pattern de `INDICATEURS_SANITAIRES` (`patterns.py`) → clé normalisée (`onchocercose`, `vers_de_guinee`, `eau_salee`, `qualite_eau`).
    - Si un entête matche `SANITAIRE_MOTS_CLES` (mais aucun indicateur précis) → clé `brut_<entête>` uniquement.
    - Si aucun indicateur trouvé → `qualite_eau = NULL` (pas `'{}'`).

7. **Créer ou mettre à jour `ouvrage`** (cf. 2.2.C pour la fiche complète).

8. **Écrire `type_ouvrage_inconnu`** (après création/mise à jour) :
    - Si `nature_ouvrage = 'inconnu'` **ET** `type_alimentation = 'AUTRE'` **ET** `realisation_par = 'inconnu'`.
    - Alors : `ligne.statut_qualite = 'type_ouvrage_inconnu'`, `message_qualite = "Attributs métier indéterminés (nature, alimentation, réalisation)"`.
    - **L'ouvrage est créé quand même** (il existe physiquement, coordonnées OK, localité OK). On le marque pour requalification V2.

9. **Remplir `ligne_ingeree.id_ouvrage_consolide`** avec l'`id_ouvrage` créé ou mis à jour.

##### Règles de décision (`_map_nature`, `_map_alimentation`, `_map_realisation`, `_map_etat`)

**`_map_nature(type_ouvrage_brut, nom_feuille)`** — retourne `'puits'`, `'forage'` ou `'inconnu'` :
1. Si `type_ouvrage_brut` contient `puits` (insensible casse/accents) → `'puits'`.
2. Si `type_ouvrage_brut` contient `forage` → `'forage'`.
3. Si `type_ouvrage_brut` contient `sondage` → `'forage'` (un sondage est un type de forage).
4. Si nom de feuille contient `puits` → `'puits'`.
5. Si nom de feuille contient `forage` → `'forage'`.
6. Sinon → `'inconnu'`.

**`_map_alimentation(type_ouvrage_brut, usage_ouvrage_brut, nom_feuille)`** — retourne `PMH` / `HVA` / `PEA` / `HV` / `AUTRE` :
1. **Priorité 1 : nom de feuille** (le plus fiable, cf. 1.6 contrainte 2). Si la feuille contient `PMH` → `PMH`, `HVA` → `HVA`, `PEA` → `PEA`, `HV` → `HV`.
2. **Priorité 2 : `type_ouvrage_brut`**. Patterns :
    - `pmh` ou `motricite` ou `pompe` → `PMH`.
    - `hva` ou `villageoise amelioree` → `HVA`.
    - `hv` ou `villageoise` → `HV`.
    - `pea` ou `autonome` → `PEA`.
3. **Priorité 3 : `usage_ouvrage_brut`**. Mêmes patterns.
4. Sinon → `AUTRE`.

**`_map_realisation(donnees_brutes, type_ouvrage_brut)`** — retourne `'public'`, `'prive'` ou `'inconnu'` :
1. Chercher dans `donnees_brutes` une clé contenant `type de forage` (insensible casse). Si valeur contient `public` ou `administratif` → `'public'`. Si `prive` → `'prive'`.
2. Sinon, `type_ouvrage_brut` :
    - Contient `ADM`, `Administratif`, `ONEP`, `Etat` → `'public'`.
    - Contient `SODECI`, `prive`, `ONG` → `'prive'`.
3. Sinon → `'inconnu'`.

**`_map_etat(etat_ouvrage_brut)`** — retourne `'fonctionnel'`, `'en_panne'`, `'abandonne'` ou `'inconnu'` :
1. Si `etat_ouvrage_brut` contient `fonctionnel`, `bon`, `marche`, `utilise`, `exploite` → `'fonctionnel'`.
2. Si contient `panne`, `mauvais`, `dysfonction`, `non fonctionnel` → `'en_panne'`.
3. Si contient `abandon`, `detruit`, `inexistant` → `'abandonne'`.
4. Sinon → `'inconnu'`.

##### Dédoublonnage (`_trouver_ouvrage_existant`)

**Priorité 1 — `code_ouvrage`** :
- Extraire `code_ouvrage` de `donnees_brutes` (clés `Code ouvrage`, `Code_Ouvrage`, `CODE OUVRAGE`, `code_ouvrage`).
- `SELECT * FROM ouvrage WHERE code_ouvrage = :code LIMIT 1`.
- Si trouvé → c'est l'ouvrage existant.
- **Attention** : ne **pas** filtrer sur `id_localite`. Deux localités différentes avec le même code peuvent être fusionnées à tort. Risque accepté au MVP (cf. 2.2.C points d'attention).

**Priorité 2 — tuple** :
- `SELECT * FROM ouvrage WHERE id_localite = :id_localite AND nature_ouvrage = :nature AND type_alimentation = :alim AND annee_realisation = :annee LIMIT 1`.
- **Condition** : au moins un des champs `nature_ouvrage`, `type_alimentation`, `annee_realisation` doit être **non NULL**. Sinon le tuple est trop vague (tout `NULL` matcherait tout), on ne dédoublonne pas.

**Fusion en cas de mise à jour** :
- Champs vides de l'existant complétés par les valeurs de la ligne (`annee_realisation`, `latitude_decimal`, `longitude_decimal`, `etat`, `nature_ouvrage`, `type_alimentation`, `realisation_par`).
- `metadata` : ajouter les clés `brut_*` absentes (ne pas écraser les valeurs existantes).
- `qualite_eau` : idem (fusion par clé).
- `code_ouvrage` : si l'existant n'en a pas et la ligne oui, on le renseigne.

##### Cas limites gérés

| Cas                                         | Comportement                                                                                             |
|---------------------------------------------|----------------------------------------------------------------------------------------------------------|
| Feuille `Localités`                         | Ignorée (`_est_feuille_localites`). Les lignes restent dans `ligne_ingeree` sans `id_ouvrage_consolide`. |
| Ligne `geom_invalide`                       | Ignorée (pas de coordonnées).                                                                            |
| Ligne `localite_non_resolue`                | Ignorée (pas de localité).                                                                               |
| `code_ouvrage` partagé entre deux localités | Fusion à tort (risque accepté MVP). V2 : ajouter `id_localite` au dédoublonnage.                         |
| `code_ouvrage` partagé + coordonnées > 1 km | `doublon_suspect`, non consolidé.                                                                        |
| Tous attributs métier inconnus              | `type_ouvrage_inconnu`, **consolidé quand même**.                                                        |
| `donnees_brutes` avec colonnes sanitaires   | `qualite_eau` rempli (clés normalisées + `brut_*`).                                                      |
| `donnees_brutes` sans colonne sanitaire     | `qualite_eau = NULL`.                                                                                    |
| Même ouvrage dans deux fichiers             | Mise à jour (fusion). Pas de doublon.                                                                    |

##### Erreurs

- **Exception dans `_consolider_ligne`** : `logger.error`, `stats["erreurs"] += 1`, la ligne est ignorée (pas de rollback global). Le pipeline continue.
- **`ST_Distance` indisponible** (PostGIS non installé) : la détection `doublon_suspect` échoue silencieusement (log warning), la consolidation continue sans détection.

##### Statistiques retournées

`consolider_lignes_run` retourne :
```python
{
    "total_lignes": int,
    "ouvrages_crees": int,
    "ouvrages_mis_a_jour": int,
    "lignes_ignorees": int,           # statut != ok, id_localite NULL, feuille localités
    "lignes_localites_ignorees": int, # sous-ensemble de lignes_ignorees
    "doublons_suspects": int,
    "attributs_indetermines": int,    # type_ouvrage_inconnu
    "erreurs": int,
}
```

---

#### 3.2.4 Orchestration (`services/run.py`)

**Rôle** : orchestrer les étapes 2, 3, 4 du pipeline en séquence, de façon asynchrone (BackgroundTask FastAPI), et mettre à jour `fichier.statut` et `ingestion_run.statut`.

**Entrées**
- `ingestion_run` (créé par `POST /fichiers/{id}/runs`, `statut = 'en_cours'`).

**Sorties**
- `ligne_ingeree`, `ouvrage` (via les étapes).
- `ingestion_run.statut` : `'termine'` ou `'erreur'`.
- `ingestion_run.finished_at`, `nb_lignes_ingerees`, `message`.
- `fichier.statut` : `'ingere'`, `'partiel'` ou `'erreur'` (mis à jour **en fin de pipeline**, décision A3).
- `fichier.date_ingestion`.

##### Algorithme

```
1. Charger run, fichier.
2. try:
     a. ingerer_fichier()          → ligne_ingeree
     b. rapprocher_lignes_run()    → id_localite, statut_qualite
     c. consolider_lignes_run()    → ouvrage, id_ouvrage_consolide
3. Mettre à jour run :
     - statut = 'termine' si total_lignes > 0, sinon 'erreur'
     - finished_at = now()
     - nb_lignes_ingerees = total
4. Mettre à jour fichier :
     - statut = 'ingere' (toutes feuilles OK)
              | 'partiel' (certaines feuilles en erreur)
              | 'erreur' (aucune feuille OK)
     - date_ingestion = now()
5. except Exception:
     - db.rollback()
     - run.statut = 'erreur', run.message = str(e), run.finished_at = now()
     - fichier.statut = 'erreur'
     - raise
```

**Règles de décision**

- **`fichier.statut`** est mis à jour **par `run.py` uniquement**, en fin de pipeline (décision A3). Pas par `ingestion.py`.
- **`'ingere'`** : au moins une feuille a `statut_ingestion = 'ingere'` **et** aucune feuille n'a `'erreur'`.
- **`'partiel'`** : au moins une feuille `'erreur'` **et** au moins une feuille `'ingere'`.
- **`'erreur'`** : toutes les feuilles sont `'erreur'`, ou exception globale.
- **`ingestion_run.statut = 'termine'`** si `total_lignes > 0` (même si certaines feuilles ont échoué — le run global a produit des lignes).
- **`ingestion_run.statut = 'erreur'`** si `total_lignes = 0` ou exception.

##### Cas limites gérés

| Cas                             | Comportement                                                                                                                                  |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| Une feuille échoue              | Les autres continuent. `fichier.statut = 'partiel'`.                                                                                          |
| Toutes les feuilles échouent    | `fichier.statut = 'erreur'`.                                                                                                                  |
| Exception dans le rapprochement | Pipeline interrompu, rollback, `statut = 'erreur'`.                                                                                           |
| Exception dans la consolidation | Pipeline interrompu (rollback de l'étape), `statut = 'erreur'`. Les lignes déjà consolidées dans le run restent (V2 : transaction par ligne). |
| Run sur un fichier déjà ingéré  | Nouveau `fichier` (si `force=true`) ou 409. Pas de mise à jour du run précédent.                                                              |

##### Erreurs

- **Run introuvable** : `ValueError`.
- **Fichier introuvable** : `ValueError`.
- **Exception pipeline** : rollback, run et fichier en `'erreur'`, exception relancée.

---

#### 3.2.5 Tableau récapitulatif des 6 statuts

Cette section complète 3.1.6 avec les **transitions** observées dans le pipeline.

| Statut                   | Écrit par     | Étape               | Consolidé                 | Message                                                               |
|--------------------------|---------------|---------------------|---------------------------|-----------------------------------------------------------------------|
| `'ok'`                   | ingestion     | 2                   | Oui (confirmé par 3 et 4) | `NULL`                                                                |
| `'geom_invalide'`        | ingestion     | 2                   | Non                       | `"Coordonnées manquantes ou invalides"`                               |
| `'localite_non_resolue'` | rapprochement | 3                   | Non                       | `"Localité non résolue : <localite_brute>"`                           |
| `'doublon_suspect'`      | consolidation | 4 (avant création)  | Non                       | `"Code ouvrage <code> déjà utilisé à <distance> km"`                  |
| `'type_ouvrage_inconnu'` | consolidation | 4 (après création)  | **Oui**                   | `"Attributs métier indéterminés (nature, alimentation, réalisation)"` |
| `'rejete'`               | ingestion     | 2 (avant insertion) | Non (non stocké)          | Jamais écrit en base                                                  |

**Transitions possibles** :
- `'ok'` → `'localite_non_resolue'` (si rapprochement échoue).
- `'ok'` → `'doublon_suspect'` (si code + distance > 1 km).
- `'ok'` → `'type_ouvrage_inconnu'` (si attributs tous inconnus).
- **Jamais** de retour en arrière (`'localite_non_resolue'` ne redevient pas `'ok'` sans rejouer le rapprochement).

---

#### 3.2.6 Cas limites transverses et décisions

| Cas                                               | Décision                                                                                                                                                                           |
|---------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **DMS corrompu** (1 ligne sur un fichier)         | `geom_invalide`. Cas normal, accepté.                                                                                                                                              |
| **Feuille `Localités`**                           | Ingérée, mais ignorée à la consolidation et exclue de la carto (`v_points_par_fichier`).                                                                                           |
| **`code_ouvrage` partagé entre sous-préfectures** | Fusion à tort acceptée MVP. V2 : ajouter `id_localite`.                                                                                                                            |
| **Coordonnées à (0, 0)**                          | Rejetées par `geom_from_latlon` → `geom_invalide`.                                                                                                                                 |
| **`localite_brute` vide**                         | `localite_non_resolue`.                                                                                                                                                            |
| **Deux localités homonymes**                      | Le premier match gagne (risque de faux positif). V2 : utiliser `sous_prefecture_brute`.                                                                                            |
| **Fichier réingéré**                              | Nouveau `fichier` + nouveau `run`. Les anciennes lignes survivent (G5, G8).                                                                                                        |
| **Rejouer la consolidation**                      | `UPDATE ligne_ingeree SET id_ouvrage_consolide = NULL; DELETE FROM ouvrage;` (G7).                                                                                                 |
| **Rejouer le rapprochement**                      | `UPDATE ligne_ingeree SET id_localite = NULL, statut_qualite = 'ok', message_qualite = NULL WHERE statut_qualite = 'localite_non_resolue';` puis relancer `rapprocher_lignes_run`. |
| **Rejouer l'ingestion**                           | Nouveau `fichier` (force) ou 409. Les anciennes lignes restent.                                                                                                                    |

---

## 4. Contrat d'API

Cette section fixe les **règles transverses** du contrat d'API. Elle fait autorité sur l'`openapi.yaml`, qui reste la **spécification technique détaillée** (schémas complets, exemples). En cas de conflit entre cette section et l'openapi, **c'est la Bible qui gagne** ; l'openapi est corrigé en Phase D (cf. 7.2).

### 4.1 Principes généraux

**P-API-1 — Versioning par préfixe.**
Tous les endpoints sont préfixés par `/v1`. Pas de versioning par header. Un changement cassant = `/v2`. Les ajouts non cassants (nouveaux champs, nouveaux endpoints) se font dans `/v1`.

**P-API-2 — Authentification à deux niveaux.**
- **Lecture** : header `X-API-Key`. Une seule clé (`API_KEY_READ`) pour tout le monde au MVP. Pas de notion d'utilisateur en lecture.
- **Écriture** : header `Authorization: Bearer <jwt>`. JWT manuel généré via `create_access_token` (script CLI), pas de login au MVP. Le JWT porte `sub` (identifiant) et `role` (`ingesteur` par défaut, `admin` pour les opérations sensibles).

**P-API-3 — Séparation lecture/écriture.**
Les endpoints de lecture (`GET`) exigent `X-API-Key`. Les endpoints d'écriture (`POST`, `PUT`, `PATCH`, `DELETE`) exigent `Authorization: Bearer`. Un endpoint d'écriture **peut aussi** exiger `X-API-Key` si on veut une double vérification (V2). Au MVP, `Bearer` seul suffit pour l'écriture.

**P-API-4 — Format d'erreur unique (RFC 7807).**
Toutes les erreurs suivent **Problem Details** :

```json
{
  "type": "https://api.dhr.local/errors/conflict",
  "title": "Conflict",
  "status": 409,
  "detail": "Un fichier avec le même hash existe déjà. Utilisez ?force=true pour réingérer.",
  "instance": "/v1/fichiers",
  "errors": [
    { "field": "hash_sha256", "message": "déjà présent" }
  ]
}
```

Le champ `errors` est **optionnel** (présent uniquement pour les erreurs de validation `422`). `type` est une URI stable (documentée en 4.4). `instance` est le chemin de la requête.

**P-API-5 — Pagination : offset pour les petites listes, cursor pour les volumineuses.**
- **Offset** (`?offset=0&limit=100`) : `sources`, `ref-geo`, `localites`, `fichiers`, `feuilles`, `runs`. Volumes modestes (< 10 000 lignes par liste). `limit` max = 1000.
- **Cursor** (`?cursor=<opaque>&limit=100`) : `ouvrages`, `lignes`. Volumes potentiellement grands (dizaines de milliers). Le curseur est opaque (base64 d'un `(id, date)`), stable dans le temps, et permet une pagination sans `OFFSET` coûteux.
- **Réponse** : `{ "data": [...], "pagination": {...} }` avec `pagination` = `PaginationOffset` (offset, limit, total) ou `PaginationCursor` (limit, next_cursor, has_more).

**P-API-6 — `?include=` pour les champs coûteux.**
Les champs `metadata` (JSONB) et `donnees_brutes` (JSONB) sont **exclus par défaut** des réponses (payload trop gros, indexation GIN non gratuite). On les inclut explicitement :
- `?include=metadata` : ajoute `metadata` sur les entités qui en ont (`localite`, `ouvrage`, `cgpe`).
- `?include=brut` : ajoute `donnees_brutes` sur `ligne_ingeree` (endpoint détail uniquement, `/lignes/{id}`).
- Les deux peuvent être combinés : `?include=metadata,brut` (V2, au MVP un seul à la fois).

**P-API-7 — Dates en ISO 8601 UTC.**
Toutes les dates sont sérialisées en `YYYY-MM-DDTHH:MM:SSZ` (UTC). Les colonnes `date` (sans heure) sont en `YYYY-MM-DD`. Pas de timestamp Unix.

**P-API-8 — GeoJSON conforme RFC 7946.**
Les réponses carto sont des `FeatureCollection` GeoJSON. Les coordonnées sont `[longitude, latitude]` (ordre RFC 7946, **pas** lat/lon). Le CRS est WGS84 (EPSG:4326), **jamais** déclaré dans le GeoJSON (RFC 7946 l'impose implicitement).

**P-API-9 — Identifiants en `int64`.**
Tous les IDs (`id_ouvrage`, `id_fichier`, etc.) sont des entiers 64 bits. Pas d'UUID, pas de string. Cohérent avec P8 (section 2.1.2).

**P-API-10 — Pas de PATCH au MVP.**
Les mises à jour sont des `PUT` complets (remplacement) ou des actions explicites (`POST /fichiers/{id}/runs`). Pas de `PATCH` partiel au MVP. V2 : introduire `PATCH` si besoin.

---

### 4.2 Authentification

| Type             | Header                                          | Endpoints                         | Erreur si absent   |
|------------------|-------------------------------------------------|-----------------------------------|--------------------|
| Lecture          | `X-API-Key: <API_KEY_READ>`                     | Tous les `GET`                    | `401 Unauthorized` |
| Écriture         | `Authorization: Bearer <jwt>`                   | Tous les `POST`, `PUT`            | `401 Unauthorized` |
| Écriture (admin) | `Authorization: Bearer <jwt>` avec `role=admin` | `PUT /fichiers/{id}/mapping` (V2) | `403 Forbidden`    |

**Génération du JWT (MVP)** : via script CLI, dans le conteneur backend :

```bash
docker compose exec backend python -c \
  "from app.auth import create_access_token; print(create_access_token('test', 'admin'))"
```

**Pas de login, pas de refresh token, pas de logout au MVP.** Le JWT expire après `JWT_EXPIRE_MIN` (60 min par défaut). L'utilisateur le colle dans l'UI (page Paramètres, cf. section 5).

**Sécurité** : l'API key est un secret partagé. En production (V2), on passera à des clés par utilisateur + rotation. Au MVP, une seule clé, stockée en `.env`.

---

### 4.3 Liste des endpoints (27)

Les endpoints sont groupés par tag (cf. `openapi.yaml`). Pour chaque endpoint : méthode, chemin, auth, résumé. Le détail des schémas est dans l'`openapi.yaml` (section 4.5 pour les schémas clés).

#### 4.3.1 Référentiels (`/sources`, `/ref-geo`, `/localites`)

| Méthode | Chemin                 | Auth    | Résumé                                                                                 |
|---------|------------------------|---------|----------------------------------------------------------------------------------------|
| `GET`   | `/sources`             | API key | Liste paginée des sources (offset).                                                    |
| `GET`   | `/ref-geo`             | API key | Nœuds du référentiel administratif (filtres `niveau`, `parent_id`). Pagination offset. |
| `GET`   | `/ref-geo/{id}/chemin` | API key | Chaîne hiérarchique district → localité pour un nœud.                                  |
| `GET`   | `/localites`           | API key | Liste paginée (filtres `id_geo`, `q` pour recherche floue). Offset.                    |
| `GET`   | `/localites/{id}`      | API key | Détail d'une localité. `?include=metadata` pour le JSONB.                              |

**Note** : `/types-ouvrage` **n'existe plus** (table supprimée, décision 3). Ne pas recréer.

#### 4.3.2 Fichiers (`/fichiers`)

| Méthode | Chemin                            | Auth    | Résumé                                                                               |
|---------|-----------------------------------|---------|--------------------------------------------------------------------------------------|
| `GET`   | `/fichiers`                       | API key | Liste paginée (filtres `id_source`, `statut`). Offset.                               |
| `POST`  | `/fichiers`                       | JWT     | Upload d'un fichier Excel. Crée `fichier` + `feuille`. `?force=true` pour réingérer. |
| `GET`   | `/fichiers/{id}`                  | API key | Détail d'un fichier.                                                                 |
| `GET`   | `/fichiers/{id}/feuilles`         | API key | Feuilles d'un fichier. Offset.                                                       |
| `GET`   | `/fichiers/{id}/mapping-proposal` | API key | Proposition de mapping auto (par feuille, par entête).                               |
| `PUT`   | `/fichiers/{id}/mapping`          | JWT     | Sauvegarde du mapping validé par l'utilisateur.                                      |

#### 4.3.3 Ingestion (`/fichiers/{id}/runs`, `/runs`, `/lignes`)

| Méthode | Chemin                  | Auth    | Résumé                                                                                          |
|---------|-------------------------|---------|-------------------------------------------------------------------------------------------------|
| `POST`  | `/fichiers/{id}/runs`   | JWT     | Lance un run (asynchrone, BackgroundTask). Body : `RunComplet` / `RunEchantillon` / `RunPlage`. |
| `GET`   | `/fichiers/{id}/runs`   | API key | Historique des runs d'un fichier. Offset.                                                       |
| `GET`   | `/runs/{id}`            | API key | Suivi d'un run (statut, `finished_at`, `message`). Polling 2s côté UI.                          |
| `GET`   | `/runs/{id}/lignes`     | API key | Lignes d'un run. Cursor. Filtre `statut_qualite`.                                               |
| `GET`   | `/feuilles/{id}/lignes` | API key | Lignes d'une feuille. Cursor. Filtres `id_run`, `statut_qualite`.                               |
| `GET`   | `/lignes/{id}`          | API key | Détail d'une ligne. `?include=brut` pour `donnees_brutes`.                                      |

**Note** : `POST /fichiers/{id}/runs` retourne `202 Accepted` avec `{id_run, id_fichier, statut: "en_cours", started_at, poll_url}`. L'UI poll `GET /runs/{id}`.

#### 4.3.4 Ouvrages & CGPE (`/ouvrages`, `/cgpe`)

| Méthode | Chemin                 | Auth    | Résumé                                                                                                                                                                                                        |
|---------|------------------------|---------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `GET`   | `/ouvrages`            | API key | Liste des ouvrages consolidés. Cursor. Filtres : `nature_ouvrage`, `type_alimentation`, `realisation_par`, `etat`, `region`, `departement`, `sous_prefecture`, `annee_min`, `annee_max`. `?include=metadata`. |
| `GET`   | `/ouvrages/{id}`       | API key | Détail d'un ouvrage. `?include=metadata`.                                                                                                                                                                     |
| `GET`   | `/ouvrages/export`     | API key | Export Excel streamé (feuille Synthèse KPI incluse par défaut). Mêmes filtres que `/ouvrages`. `?include=metadata`, `?with_summary=false`, `?columns=...` (V2).                                               |
| `GET`   | `/ouvrages/export.csv` | API key | Export CSV streamé (UTF-8, séparateur `;`). Mêmes filtres.                                                                                                                                                    |
| `GET`   | `/cgpe/{id}`           | API key | Détail d'un CGPE. `?include=metadata`.                                                                                                                                                                        |

**Note** : les filtres `type_ouvrage` et `district` **n'existent pas** (remplacés par `nature_ouvrage` + `type_alimentation` + `realisation_par` ; `district` retiré, décision 6). Le KPI `par_district` reste dans la feuille Synthèse de l'export Excel (cf. 1.4 décision 6).

#### 4.3.5 Carto (`/carto`)

| Méthode | Chemin                                        | Auth    | Résumé                                                                                                                                                                                                                             |
|---------|-----------------------------------------------|---------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `GET`   | `/carto/fichiers/{id_fichier}/points`         | API key | GeoJSON des points bruts d'un fichier (mode « Par fichier »). Filtres : `id_feuille`, `id_run`, `statut_qualite`, `type_ouvrage`. Source : `v_points_par_fichier`.                                                                 |
| `GET`   | `/carto/fichiers/{id_fichier}/points.geojson` | API key | Téléchargement GeoJSON des points bruts (Content-Disposition: attachment).                                                                                                                                                         |
| `GET`   | `/carto/tous/points`                          | API key | GeoJSON des ouvrages consolidés (mode « Tous »). Filtres : `nature_ouvrage`, `type_alimentation`, `realisation_par`, `etat`, `region`, `departement`, `sous_prefecture`, `annee_min`, `annee_max`. Source : `v_points_consolides`. |

**Note** : pas de `district` dans les filtres. Les feuilles de localités sont **exclues** par `v_points_par_fichier` (cf. 2.2.D).

#### 4.3.6 Qualité (`/qualite`)

| Méthode | Chemin                   | Auth    | Résumé                                                                  |
|---------|--------------------------|---------|-------------------------------------------------------------------------|
| `GET`   | `/qualite/fichiers/{id}` | API key | Tableau de bord qualité d'un fichier. Source : `v_qualite_par_fichier`. |

**Total : 27 endpoints** (dont 1 supprimé : `/types-ouvrage`).

---

### 4.4 Codes d'erreur

Tous les codes d'erreur suivent RFC 7807 (cf. P-API-4). Les `type` sont stables (URI documentée ci-dessous).

| Code HTTP | `type` (URI)                   | Cas                                | Exemple                              |
|-----------|--------------------------------|------------------------------------|--------------------------------------|
| `400`     | `.../errors/bad-request`       | Paramètre invalide, body mal formé | `mode=invalide`                      |
| `401`     | `.../errors/unauthorized`      | API key ou JWT manquant/invalide   | `X-API-Key` absent                   |
| `403`     | `.../errors/forbidden`         | Rôle JWT insuffisant               | `role=ingesteur` sur endpoint admin  |
| `404`     | `.../errors/not-found`         | Ressource inexistante              | `id_fichier=999`                     |
| `409`     | `.../errors/conflict`          | Conflit métier                     | Hash déjà présent sans `?force=true` |
| `413`     | `.../errors/payload-too-large` | Export > `MAX_EXPORT_ROWS`         | 150 000 lignes, limite 100 000       |
| `422`     | `.../errors/validation`        | Validation Pydantic                | `ligne_debut > ligne_fin`            |
| `500`     | `.../errors/internal`          | Erreur serveur                     | Exception non gérée                  |

**Exemples concrets** :

**409 Conflict** (upload sans `force`) :
```json
{
  "type": "https://api.dhr.local/errors/conflict",
  "title": "Conflict",
  "status": 409,
  "detail": "Un fichier avec le même hash existe déjà (id_fichier=42). Utilisez ?force=true pour réingérer.",
  "instance": "/v1/fichiers"
}
```

**413 Payload Too Large** (export) :
```json
{
  "type": "https://api.dhr.local/errors/payload-too-large",
  "title": "Payload Too Large",
  "status": 413,
  "detail": "Trop de lignes à exporter (150000 > 100000). Affinez vos filtres.",
  "instance": "/v1/ouvrages/export"
}
```

**422 Validation** (run `plage` invalide) :
```json
{
  "type": "https://api.dhr.local/errors/validation",
  "title": "Validation Error",
  "status": 422,
  "detail": "Le body de la requête est invalide.",
  "instance": "/v1/fichiers/12/runs",
  "errors": [
    { "field": "ligne_fin", "message": "doit être >= ligne_debut" }
  ]
}
```

---

### 4.5 Schémas clés (résumé)

Cette section donne un **résumé** des schémas les plus utilisés. Le détail complet (types, nullabilité, exemples) est dans `openapi.yaml` (section `components.schemas`). En cas de divergence, **l'openapi fait foi pour la forme**, la Bible pour la sémantique.

#### `Source`

```
id_source: int
nom: str (UNIQUE)
type_source: enum[public, prive, bailleur, etat, autre]
actif: bool
```

#### `Ouvrage` (consolidé)

```
id_ouvrage: int64
code_ouvrage: str | null
nature_ouvrage: enum[puits, forage, inconnu] | null
type_alimentation: enum[PMH, HVA, PEA, HV, AUTRE] | null
realisation_par: enum[public, prive, inconnu] | null
etat: enum[fonctionnel, en_panne, abandonne, inconnu]
annee_realisation: int | null
localite: LocaliteResume
geom: GeoJSONPoint | null
metadata: object | null   (uniquement si ?include=metadata)
qualite_eau: object | null
financements: Financement[] | null
cgpe: {existe: bool, statut: str | null} | null
```

**Note** : **pas de `type_ouvrage`** (supprimé), remplacé par `nature_ouvrage` + `type_alimentation` + `realisation_par`.

#### `LigneIngeree` (brute)

```
id_ligne: int64
id_feuille: int64
num_ligne_source: int
localite_brute: str | null
type_ouvrage_brut: str | null
latitude_decimal: float | null
longitude_decimal: float | null
geom: GeoJSONPoint | null
statut_qualite: enum[ok, localite_non_resolue, geom_invalide, type_ouvrage_inconnu, rejete, doublon_suspect]
annee_projet: int | null
bailleur_brut: str | null
donnees_brutes: object   (uniquement si ?include=brut, endpoint détail)
```

**Note** : `usage_ouvrage_brut` est **ajouté** au schéma (écart O4, à corriger en Phase D).

#### `QualiteFichier`

```
id_fichier: int64
nom_fichier: str
source: str
statut: str
nb_lignes_total: int
qualite: {
  ok: int,
  localite_non_resolue: int,
  geom_invalide: int,
  type_ouvrage_inconnu: int,
  rejete: int,
  doublon_suspect: int
}
taux_reussite: float   (= ok / nb_lignes_total)
```

**Note** : `rejete` est calculé par différence (`nb_lignes_total - COUNT(ligne_ingeree)`), pas par `COUNT(*) FILTER`. Cf. 2.2.D et 3.1.6.

#### `FeatureCollection` (GeoJSON)

```
type: "FeatureCollection"
features: Feature[]
meta: {count: int, id_fichier?: int64, nom_fichier?: str}
```

Chaque `Feature` :
```
type: "Feature"
id: str
geometry: GeoJSONPoint | null
properties: object   (inclut statut_qualite, nature_ouvrage, etc.)
```

**Note** : `meta` est un champ **non standard** ajouté par le backend (RFC 7946 autorise les champs supplémentaires). Il donne le nombre de features et le contexte.

#### `Problem` (RFC 7807)

```
type: str (URI)
title: str
status: int
detail: str | null
instance: str | null
errors: [{field: str, message: str}] | null
```

#### `PaginationOffset` / `PaginationCursor`

```
PaginationOffset:  {offset: int, limit: int, total: int | null}
PaginationCursor:  {limit: int, next_cursor: str | null, has_more: bool}
```

---

### 4.6 Écarts avec l'`openapi.yaml` (à corriger en Phase D)

L'`openapi.yaml` v1.2.0 **n'est pas encore aligné** sur la Bible. Les écarts sont listés en 7.2 (O1–O5, OI1–OI2). Rappel :

| #   | Écart                                                   | Correction                                                               |
|-----|---------------------------------------------------------|--------------------------------------------------------------------------|
| O1  | `/types-ouvrage` présent                                | Retirer (supprimé)                                                       |
| O2  | `Ouvrage.type_ouvrage` (objet)                          | Remplacer par `nature_ouvrage` + `type_alimentation` + `realisation_par` |
| O3  | Filtre `district` sur `/ouvrages`, `/carto/tous/points` | Retirer                                                                  |
| O4  | `LigneIngeree` sans `usage_ouvrage_brut`                | Ajouter                                                                  |
| O5  | Filtre `type_ouvrage` sur `/ouvrages`                   | Remplacer par les 3 nouveaux filtres                                     |
| OI1 | `FeatureCollectionPoints` a un `type: object` en double | Corriger la syntaxe YAML                                                 |
| OI2 | `/types-ouvrage` référencé dans tags et description     | Retirer                                                                  |

**Ces corrections sont faites en Phase D** (alignement des services). L'openapi sera **régénéré** à partir de la Bible et du code aligné, pas patché.

---

### 4.7 Ce qui n'est **pas** dans l'API au MVP

| Endpoint                              | Raison                              | V2              |
|---------------------------------------|-------------------------------------|-----------------|
| `POST /ouvrages` (création manuelle)  | Hors scope (1.3)                    | UI de création  |
| `PATCH /ouvrages/{id}` (édition)      | Hors scope                          | UI d'édition    |
| `DELETE /ouvrages/{id}`               | Pas de suppression au MVP (G9)      | Soft delete     |
| `POST /localites` (création manuelle) | Hors scope                          | UI de création  |
| `POST /cgpe` (création manuelle)      | Hors scope                          | UI de gestion   |
| `POST /projets` (création manuelle)   | Hors scope                          | UI de gestion   |
| `POST /login` (auth)                  | JWT manuel au MVP                   | Login + refresh |
| `GET /metrics` (Prometheus)           | Pas de monitoring au MVP            | V2              |
| `GET /health`                         | **Présent** (hors scope mais utile) | Déjà là         |

**Note** : `GET /health` existe déjà (healthcheck DB). Il n'est pas dans la liste des 27 endpoints métier, mais il est **conservé** (utile pour le monitoring et le démarrage Docker).

---

## 5. Frontend

Cette section décrit l'**UI cible** et l'**état actuel** du frontend. Elle fait autorité sur le code `frontend/src/`. Pour chaque page, un encart distingue **ce qui existe déjà** et **ce qui reste à faire** (Phase D).

### 5.1 Stack et architecture

**Stack** (figée, cohérente avec le handoff et le code existant) :

| Couche        | Technologie                  | Version |
|---------------|------------------------------|---------|
| Framework     | React                        | 18      |
| Build         | Vite                         | 5.4     |
| Langage       | TypeScript                   | 5.x     |
| Styles        | Tailwind CSS                 | 3.4     |
| Composants UI | shadcn/ui (basé sur Radix)   | —       |
| Carto         | Leaflet + Esri World Imagery | 1.9     |
| État serveur  | TanStack Query               | 5.59    |
| Routing       | React Router                 | 6.x     |
| Toasts        | Sonner                       | —       |
| Icônes        | Lucide                       | —       |

**Structure des dossiers** :

```text
frontend/src/
├── pages/                  # 1 fichier par page
│   ├── Fichiers.tsx        # ✅ existante
│   ├── Mapping.tsx         # ✅ existante
│   ├── Carte.tsx           # ✅ existante
│   ├── Liste.tsx           # ⏳ stub (6.5)
│   ├── Qualite.tsx         # ⏳ stub (6.6)
│   └── Parametres.tsx      # ✅ existante
├── components/             # composants transverses
│   ├── FiltersPanel.tsx    # ✅ existant
│   ├── MapView.tsx         # ✅ existant
│   ├── RunStatus.tsx       # ✅ existant
│   ├── UploadDialog.tsx    # ✅ existant
│   └── ui/                 # primitives shadcn (Button, Input, Dialog, Badge, ...)
├── lib/
│   └── api.ts              # client HTTP + types TS + setJwt/getJwt
└── App.tsx                 # routes + layout
```

**Pas de state management global** (pas de Redux, pas de Zustand). TanStack Query suffit pour l'état serveur. Le state local (`useState`) suffit pour l'UI (filtres, sélection de fichier, etc.).

**Layout** : sidebar (navigation) + header (titre + actions) + contenu. Le layout est défini dans `App.tsx` (hors scope de cette section).

### 5.2 Client API (`src/lib/api.ts`)

Le client HTTP est un **wrapper `fetch`** qui :
- Injecte `X-API-Key: <VITE_API_KEY>` sur **tous** les appels (lecture et écriture).
- Injecte `Authorization: Bearer <jwt>` sur les appels d'écriture (si `localStorage.dhr_jwt` est présent).
- Parse la réponse JSON (ou `Problem` en cas d'erreur 4xx/5xx).
- Expose `setJwt(jwt: string | null)` et `getJwt(): string | null` (stockage `localStorage`).

**Fonctions exposées** (signatures) :

```ts
// Référentiels
api.sources(): Promise<PaginationResponse<Source>>
api.refGeo(params?: { niveau?: string; parent_id?: number }): Promise<PaginationResponse<RefGeoAdmin>>
api.localites(params?: { q?: string; id_geo?: number }): Promise<PaginationResponse<LocaliteResume>>

// Fichiers
api.fichiers(params?: { id_source?: number; statut?: string }): Promise<PaginationResponse<Fichier>>
api.fichier(id: number): Promise<Fichier>
api.feuilles(idFichier: number): Promise<PaginationResponse<Feuille>>
api.upload(file: File, idSource: number, commentaire?: string, force?: boolean): Promise<UploadResponse>
api.mappingProposal(idFichier: number): Promise<MappingProposalFeuille[]>
api.saveMapping(idFichier: number, idFeuille: number, colonnes: MappingValidationColonne[]): Promise<MappingProposalFeuille>

// Ingestion
api.lancerRun(idFichier: number, mode?: 'complet' | 'echantillon' | 'plage', params?: RunParams): Promise<LancerRunResponse>
api.run(idRun: number): Promise<IngestionRun>
api.lignes(idRun: number, params?: { statut_qualite?: string; cursor?: string }): Promise<PaginationResponse<LigneIngeree>>

// Ouvrages
api.ouvrages(params?: OuvrageFilters): Promise<PaginationResponse<Ouvrage>>
api.ouvrage(id: number): Promise<Ouvrage>

// Carto
api.cartoTous(params?: CartoFilters): Promise<FeatureCollection>
api.cartoFichier(idFichier: number, params?: CartoFichierFilters): Promise<FeatureCollection>

// Qualité
api.qualiteFichier(idFichier: number): Promise<QualiteFichier>
```

**Gestion des erreurs** : toute erreur 4xx/5xx est convertie en objet `Problem` et levée comme `Error` avec un message lisible. Les composants appelants (`useQuery`, `useMutation`) attrapent et affichent un `toast.error` (Sonner).

**Types TS** : miroir des schémas de la section 4.5. Ils sont définis dans `src/lib/api.ts` (ou un fichier `types.ts` séparé). Ils **doivent** rester alignés sur l'openapi (Phase D).

### 5.3 Authentification (MVP)

| Type    | Stockage                       | Injection                                                       |
|---------|--------------------------------|-----------------------------------------------------------------|
| API key | `.env` (`VITE_API_KEY`)        | Header `X-API-Key` sur **tous** les appels                      |
| JWT     | `localStorage` (clé `dhr_jwt`) | Header `Authorization: Bearer` sur les **écritures** uniquement |

**Page Paramètres** (✅ existante) : textarea pour coller le JWT, bouton « Sauvegarder » (appelle `setJwt`). Pas de login, pas de logout, pas de refresh.

**Gestion du 401** : si un appel retourne 401 (JWT absent/expiré, API key invalide), l'UI affiche un toast et **redirige vers `/parametres`** (à implémenter en Phase D — actuellement, seul le toast est affiché).

### 5.4 Pages

#### 5.4.1 Fichiers (`/fichiers`)

**État actuel** : ✅ **implémentée** (`pages/Fichiers.tsx`).

**Fonctionnalités** :
- Liste des fichiers (tableau) : nom, source, statut (badge), nombre de lignes, date de réception, actions.
- Bouton **Uploader** → ouvre `UploadDialog`.
- Bouton **Run** (par fichier) → lance `POST /fichiers/{id}/runs` (`mode=complet`), affiche `RunStatus` (polling 2s).
- Bouton **Mapping** → lien vers `/fichiers/{id}/mapping`.
- État vide : icône + message « Aucun fichier. Uploadez votre premier fichier. »
- Loading : `isLoading` → texte « Chargement... » (à remplacer par un skeleton en Phase D).

**Cible Phase D** :
- Remplacer les textes de loading par des `Skeleton` (shadcn/ui).
- Ajouter un filtre par `id_source` et `statut` (déjà supporté côté API, pas encore dans l'UI).
- Afficher le nombre de feuilles détectées (déjà dans la réponse upload).

#### 5.4.2 Mapping (`/fichiers/:id/mapping`)

**État actuel** : ✅ **implémentée** (`pages/Mapping.tsx`).

**Fonctionnalités** :
- Onglets par feuille (une feuille = un onglet, avec compteur de colonnes).
- Tableau : entête Excel | destination | champ/clé | confiance.
- **Destinations** (5 options) :
    - **Standard** : dropdown des champs cibles (`CHAMPS_STANDARDS`).
    - **Métadonnée Ouvrage** : input texte pour la clé (`metadata.ouvrage.<clé>`).
    - **Métadonnée Localité** : input texte pour la clé (`metadata.localite.<clé>`).
    - **Métadonnée CGPE** : input texte pour la clé (`metadata.cgpe.<clé>`).
    - **Ignorer** : `champ_cible = NULL`.
- Confiance affichée si le mapping auto a proposé quelque chose.
- Bouton **Sauvegarder** → `PUT /fichiers/{id}/mapping`.

**Cible Phase D** :
- **Ajouter `usage_ouvrage_brut`** à `CHAMPS_STANDARDS` (écart F2). Liste complète : `region_brute`, `departement_brute`, `sous_prefecture_brute`, `localite_brute`, `type_localite_brut`, `latitude_decimal`, `longitude_decimal`, `type_ouvrage_brut`, `usage_ouvrage_brut`, `etat_ouvrage_brut`, `annee_projet`, `bailleur_brut`, `type_financement_brut`, `a_cgpe`.
- **Valider la clé** de `metadata.<entité>.<clé>` : `snake_case`, non vide, pas de doublon dans la même entité. La validation est côté frontend (UX) **et** côté backend (422 si invalide).
- **Avertir** si la clé n'est pas documentée dans `metadata_conventions.md` (avertissement non bloquant).
- **Afficher la convention** en placeholder (`ex. profondeur_forage_m`).
- Remplacer les `toast.error` par des messages inline (UX).

#### 5.4.3 Carte (`/carte`)

**État actuel** : ✅ **implémentée** (`pages/Carte.tsx` + `components/MapView.tsx`).

**Fonctionnalités** :
- Mode **Tous** (`/carto/tous/points`) / **Par fichier** (`/carto/fichiers/{id}/points`).
- En mode Fichier : sélecteur de fichier + sélecteur de feuille (optionnel).
- `FiltersPanel` : cascade géographique (région → département → sous-préfecture) + recherche localité (autocomplete) + filtres métier (alimentation, nature, réalisation, état, année min/max).
- `MapView` : Leaflet + Esri World Imagery (`maxNativeZoom: 16`, `maxZoom: 19`), `circleMarker` colorés par `type_alimentation`, popup avec `<details>` pour `metadata`.
- Légende couleur = `type_alimentation` (PMH bleu, HVA vert, PEA orange, HV violet, AUTRE gris).
- Compteur de points affichés.

**Cible Phase D** :
- **Forme = `nature_ouvrage`** : cercle plein = forage, carré = puits, losange = inconnu. Actuellement, le code utilise `dashArray: '3,3'` pour distinguer les puits (approximation). Remplacer par de vraies formes (`L.divIcon` avec SVG, ou `L.circleMarker` + `L.rectangle`).
- **Légende à 2 blocs** : bloc « Couleur = Alimentation » + bloc « Forme = Nature ».
- **Popup** : afficher `qualite_eau` en `<details>` (déjà fait pour `metadata`, à ajouter pour `qualite_eau`).
- **Filtres** : ajouter `localite` à la cascade (actuellement, c'est un champ texte avec autocomplete ; la cible est un dropdown après sous-préfecture, mais l'autocomplete reste acceptable au MVP).
- **Performance** : si > 5000 points, regrouper par `circleMarker` (déjà géré par Leaflet).

#### 5.4.4 Liste (`/liste`)

**État actuel** : ⏳ **stub** (`pages/Liste.tsx` → « Page Liste — à implémenter (6.5) »).

**Cible** :
- Tableau paginé (cursor) des ouvrages : code, nature, alimentation, réalisation, état, localité, sous-préfecture, département, région, année, actions.
- Filtres : mêmes que `FiltersPanel` (cascade géo + métier + année).
- Bouton **Exporter Excel** → `window.open('/v1/ouvrages/export?...')` avec les filtres courants.
- Bouton **Exporter CSV** → idem avec `/ouvrages/export.csv`.
- Pagination : bouton « Charger plus » (cursor).
- Loading : `Skeleton`.
- État vide : message + icône.

#### 5.4.5 Qualité (`/qualite`)

**État actuel** : ⏳ **stub** (`pages/Qualite.tsx` → « Page Qualité — à implémenter (6.6) »).

**Cible** :
- Liste des fichiers avec leur tableau de bord qualité (`GET /qualite/fichiers/{id}` pour chaque fichier, ou un endpoint agrégé — V2).
- Pour chaque fichier : nom, source, statut, `nb_lignes_total`, taux de réussite (= `ok / nb_lignes_total`), répartition par statut (barre de progression + compteurs).
- Clic sur un fichier → détail (liste des lignes par statut, avec lien vers `/lignes/{id}` — V2).
- Filtres : par `id_source`, par `statut`.

**Alternative MVP** : afficher un tableau simple par fichier (sans détail ligne). Le détail ligne est V2.

#### 5.4.6 Paramètres (`/parametres`)

**État actuel** : ✅ **implémentée** (`pages/Parametres.tsx`).

**Fonctionnalités** :
- Textarea pour coller le JWT.
- Bouton « Sauvegarder » → `setJwt` (`localStorage`).
- Placeholder expliquant comment générer le JWT (`docker compose exec backend python -c ...`).

**Cible Phase D** :
- Afficher l'état du JWT (présent / absent, date d'expiration si décodable).
- Bouton « Supprimer le JWT » (`setJwt(null)`).
- Afficher/masquer la valeur du textarea (toggle `type="password"` / `type="text"`).
- Afficher l'API key (masquée, avec bouton « copier »).

### 5.5 Composants clés

#### `FiltersPanel`

**État actuel** : ✅ **existant** (`components/FiltersPanel.tsx`).

**Props** : `filters: Filters`, `onChange: (f: Filters) => void`, `showGeographic?: boolean` (défaut `true`).

**Filtres** :
- **Métier** : `type_alimentation` (PMH/HVA/PEA/HV/AUTRE), `nature_ouvrage` (forage/puits), `realisation_par` (public/prive), `etat` (fonctionnel/en_panne/abandonne/inconnu).
- **Année** : `annee_min`, `annee_max` (inputs number).
- **Géographique** (si `showGeographic`) : cascade `region` → `departement` → `sous_prefecture` (dropdowns alimentés par `/ref-geo`), `localite` (input texte avec autocomplete via `/localites?q=`).

**Cible Phase D** :
- Ajouter un bouton « Réinitialiser les filtres ».
- Désactiver `departement` si `region` vide (déjà fait), `sous_prefecture` si `departement` vide (déjà fait), `localite` si `sous_prefecture` vide (à ajouter).
- Afficher un compteur « N filtres actifs ».

#### `MapView`

**État actuel** : ✅ **existant** (`components/MapView.tsx`).

**Props** : `data: FeatureCollection | null`, `height?: string`.

**Rendu** :
- Leaflet + Esri World Imagery (2 couches : satellite + référentiel).
- `pointToLayer` : `circleMarker` coloré par `type_alimentation` (palette existante).
- `onEachFeature` : `bindPopup` avec HTML construit par `buildPopupHtml` (localité, hiérarchie, nature, alimentation, réalisation, état, année, `<details>` metadata).
- `_escape` : échappement HTML basique (protection XSS).

**Cible Phase D** :
- **Forme = `nature_ouvrage`** (voir 5.4.3).
- **Popup** : ajouter `<details>` pour `qualite_eau` (déjà dans `metadata`).
- **Performance** : `preferCanvas: true` pour les gros volumes.
- **Zoom sur un point** : clic sur un point → zoom + ouverture du popup (à ajouter).

#### `RunStatus`

**État actuel** : ✅ **existant** (`components/RunStatus.tsx`).

**Props** : `idRun: number`, `onDone?: () => void`.

**Fonctionnement** :
- `useQuery` sur `api.run(idRun)` avec `refetchInterval: 2000` tant que `statut = 'en_cours'`.
- Quand `statut = 'termine'` ou `'erreur'` → appelle `onDone()` et arrête le polling.
- Affiche : badge statut + nombre de lignes ingérées.

**Cible Phase D** : RAS (conforme).

#### `UploadDialog`

**État actuel** : ✅ **existant** (`components/UploadDialog.tsx`).

**Props** : `open: boolean`, `onClose: () => void`, `onSuccess: (idFichier: number) => void`.

**Fonctionnement** :
- Sélection de fichier (`.xlsx`, `.xls`).
- Dropdown source (alimenté par `api.sources()`).
- Commentaire optionnel.
- Bouton Uploader → `api.upload(file, idSource, commentaire)`.
- Toast succès/erreur.

**Cible Phase D** :
- Ajouter une case à cocher `force` (réingestion).
- Afficher la progression de l'upload (barre de progression) — V2 si fichier gros.
- Valider la taille max du fichier (côté frontend, ex. 50 Mo).

### 5.6 Règles de rendu carto

**Couleur = `type_alimentation`** (palette existante, à conserver) :

| Alimentation | Couleur | Code      |
|--------------|---------|-----------|
| PMH          | Bleu    | `#2563eb` |
| HVA          | Vert    | `#16a34a` |
| PEA          | Orange  | `#ea580c` |
| HV           | Violet  | `#9333ea` |
| AUTRE        | Gris    | `#6b7280` |

**Forme = `nature_ouvrage`** (cible Phase D) :

| Nature  | Forme        | Implémentation                               |
|---------|--------------|----------------------------------------------|
| Forage  | Cercle plein | `L.circleMarker` (défaut)                    |
| Puits   | Carré        | `L.divIcon` avec SVG carré, ou `L.rectangle` |
| Inconnu | Losange      | `L.divIcon` avec SVG losange                 |

**Taille** : fixe (`radius: 6`), pas de data-driven au MVP.

**Popup** :
- En-tête : `type_alimentation` (bold).
- Corps : nature, réalisation, état, localité, code, année, `statut_qualite` (pour mode Fichier).
- `<details>` : `metadata` (table clé/valeur), `qualite_eau` (table clé/valeur).
- Échappement HTML systématique (`_escape`).

**Légende** :
- 2 blocs : « Couleur = Alimentation » (5 entrées) + « Forme = Nature » (3 entrées).
- Position : coin inférieur gauche de la carte (ou sous la carte, comme actuellement).

**Zoom** : Esri `maxNativeZoom: 16`, `maxZoom: 19`, centre par défaut `[7.5, -5.5]` (Côte d'Ivoire), zoom initial `7`.

**Feuilles de localités** : **jamais affichées**. Le filtrage est fait côté API par `v_points_par_fichier` (`NOT _est_feuille_localites`). L'UI ne fait rien de spécial.

### 5.7 Règles UX transverses

- **Polling** : `RunStatus` poll `GET /runs/{id}` toutes les 2s tant que `statut = 'en_cours'`. Arrêt automatique sur `termine` ou `erreur`.
- **Pas de pagination UI sur la carte** : tous les points de la vue sont chargés (pas de pagination). Si > 5000 points, `preferCanvas` (Phase D).
- **Pagination cursor sur la Liste** : bouton « Charger plus » (implémentation Phase D). `PaginationCursor` retourne `next_cursor` et `has_more`.
- **Export** : bouton → `window.open('/v1/ouvrages/export?...&X-API-Key=...')`. **Attention** : `window.open` ne permet pas d'envoyer de header custom. Solution : générer une URL signée (V2) ou faire un `fetch` + `blob` + `a.download` (Phase D). Au MVP, si `window.open` ne marche pas, utiliser `fetch` + `blob`.
- **Toasts** : Sonner (`toast.success`, `toast.error`). Messages courts, en français.
- **Loading skeletons** : `Skeleton` (shadcn/ui) sur les listes. Remplacer les textes « Chargement... » (Phase D).
- **État vide** : icône + message explicite (ex. « Aucun fichier. Uploadez votre premier fichier. »).
- **Erreurs 4xx/5xx** : toast avec `Problem.title` + `Problem.detail` (si présent).
- **Redirection 401** : si un appel retourne 401, toast + redirection vers `/parametres` (Phase D).

### 5.8 Frontend hors scope (V2)

| Fonction                                                 | Raison                                    |
|----------------------------------------------------------|-------------------------------------------|
| Édition manuelle d'ouvrages / localités / CGPE / projets | Hors scope (1.3)                          |
| Authentification (login, refresh token, logout)          | JWT manuel au MVP                         |
| Page détail fichier (`/fichiers/:id`)                    | La liste + Mapping + Run suffisent au MVP |
| Page détail ligne (`/lignes/:id`)                        | V2 (consultation des `donnees_brutes`)    |
| Détail qualité par ligne (liste des lignes en erreur)    | V2                                        |
| Analytics avancée (KPI historiques, cartes de chaleur)   | V2                                        |
| i18n (multi-langue)                                      | V2 (français uniquement au MVP)           |
| Mode sombre                                              | V2                                        |
| PWA (offline)                                            | V2                                        |
| Tests frontend (vitest + testing-library)                | Phase D (avec le reste des tests)         |

### 5.9 Écarts code ↔ Bible (frontend, à corriger en Phase D)

| #  | Écart                                                  | Correction                               |
|----|--------------------------------------------------------|------------------------------------------|
| F1 | `CHAMPS_STANDARDS` sans `usage_ouvrage_brut`           | Ajouter (cf. 5.4.2)                      |
| F2 | `MapView` : forme = nature approximée par `dashArray`  | Remplacer par vraies formes (cf. 5.4.3)  |
| F3 | `window.open` pour l'export (header custom impossible) | Remplacer par `fetch` + `blob` (cf. 5.7) |
| F4 | `OLD_Carte.tsx` traîne dans `pages/`                   | Supprimer                                |
| F5 | Pas de redirection 401                                 | Ajouter (cf. 5.7)                        |
| F6 | Textes « Chargement... » au lieu de skeletons          | Remplacer par `Skeleton`                 |
| F7 | `Liste.tsx` et `Qualite.tsx` sont des stubs            | Implémenter (cf. 5.4.4 et 5.4.5)         |
| F8 | Pas de page détail fichier                             | V2 (accepté)                             |
| F9 | `Parametres.tsx` : pas de bouton « Supprimer le JWT »  | Ajouter (cf. 5.4.6)                      |

**Ces corrections sont faites en Phase D** (alignement frontend). La section 5 fixe la **cible**, pas l'existant.

---

# Vérification — Section 5 appliquée

J'ai relu la section 5. **Tout est conforme.** Les 6 pages (4 existantes + 2 stubs), les 4 composants clés, les règles de rendu carto (couleur + forme), les règles UX transverses et les 9 écarts frontend (F1–F9) sont en place.

**La section 5 est validée.** On peut avancer sur la section 6.

---

## Petites remarques éditoriales (non bloquantes, à traiter en passe finale)

| # | Détail                                                                                                                                                                                                                                 | Impact                  |
|---|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------|
| 1 | 5.3 : le tableau `Type / Stockage / Injection` a une ligne « API key » qui dépasse un peu à droite (alignement Markdown).                                                                                                              | Cosmétique              |
| 2 | 5.4.3 : `MapView` mentionne `maxNativeZoom: 16` et `maxZoom: 19` — cohérent avec le code. RAS.                                                                                                                                         | RAS                     |
| 3 | 7.3 : la ligne M6 est vide (placeholder). À remplir avec la nouvelle convention `metadata.<entité>.<clé>` (M6 = « `metadata_conventions.md` ne documente pas `metadata.<entité>.<clé>` comme destination possible de `champ_cible` »). | À corriger              |
| 4 | Table des matières : la ligne `6. Décisions d'architecture (ADR) *(à venir)*` est toujours marquée à venir. À mettre à jour après la section 6.                                                                                        | À faire en passe finale |

---

## 6. Décisions d'architecture (ADR)

Cette section formalise les **décisions d'architecture** (Architecture Decision Records) actées dans la Bible et le code. Chaque ADR suit le même format :
- **Contexte** : pourquoi la question s'est posée.
- **Décision** : ce qu'on a choisi.
- **Conséquences** : impacts positifs et négatifs.
- **Alternatives écartées** : ce qu'on n'a pas choisi et pourquoi.

Les ADR sont **immuables** : une décision peut être **remplacée** par une nouvelle ADR (qui référence l'ancienne), mais jamais modifiée. Les ADR sont numérotées séquentiellement (`ADR-001`, `ADR-002`, ...).

**Index** :

| #       | Sujet                                                   | Statut   |
|---------|---------------------------------------------------------|----------|
| ADR-001 | PostgreSQL + PostGIS                                    | Acceptée |
| ADR-002 | JSONB pour les attributs non mappés                     | Acceptée |
| ADR-003 | Colonnes générées pour `geom`                           | Acceptée |
| ADR-004 | Trigram + unaccent pour le rapprochement                | Acceptée |
| ADR-005 | `serial` / `bigserial` (pas d'UUID)                     | Acceptée |
| ADR-006 | FastAPI + SQLAlchemy 2.0 + Pydantic 2                   | Acceptée |
| ADR-007 | React + Vite + TypeScript + shadcn/ui                   | Acceptée |
| ADR-008 | Leaflet + Esri World Imagery                            | Acceptée |
| ADR-009 | TanStack Query                                          | Acceptée |
| ADR-010 | Authentification MVP = API key + JWT manuel             | Acceptée |
| ADR-011 | Pagination offset + cursor                              | Acceptée |
| ADR-012 | RFC 7807 pour les erreurs                               | Acceptée |
| ADR-013 | `metadata.<entité>.<clé>` pour les attributs explicites | Acceptée |
| ADR-014 | Suppression de `type_ouvrage` (refactoring sémantique)  | Acceptée |
| ADR-015 | 6 statuts de qualité (règles conservatrices)            | Acceptée |
| ADR-016 | Dédoublonnage par `code_ouvrage` puis tuple             | Acceptée |
| ADR-017 | Pas de filtre `district`                                | Acceptée |
| ADR-018 | Migration initiale unique                               | Acceptée |

---

### ADR-001 — PostgreSQL + PostGIS

**Contexte** : la DHR a besoin de stocker des ouvrages géolocalisés (points GPS) et de faire des requêtes spatiales (carte, distance entre points, centroïdes de localités). Les fichiers sources contiennent des coordonnées en WGS84. Le volume est modeste (quelques dizaines de milliers de points), mais la carte est l'usage principal.

**Décision** : utiliser **PostgreSQL 16** avec l'extension **PostGIS 3.4**. Toutes les géométries sont en `geometry(Point, 4326)` (WGS84).

**Conséquences** :
- ✅ Type `geometry` natif, index GIST, fonctions spatiales (`ST_Distance`, `ST_MakePoint`, `ST_SetSRID`).
- ✅ Cohabitation SQL relationnel (tables, FK, contraintes) + spatial dans un seul SGBD.
- ✅ PostGIS est mature, standard de facto, bien supporté par GeoAlchemy2.
- ❌ Complexité opérationnelle (image Docker `postgis/postgis`, extensions à installer).
- ❌ Courbe d'apprentissage PostGIS pour l'équipe.

**Alternatives écartées** :
- **MySQL + extension spatiale** : moins riche que PostGIS, pas de `ST_Distance` géodésique performant, pas de `geom_from_latlon` custom.
- **MongoDB + GeoJSON** : pas de FK, pas de contraintes, pas de jointures. Inadapté au besoin relationnel (référentiels, ouvrages, CGPE, projets).
- **SQLite + SpatiaLite** : pas de serveur, pas de concurrence. Inadapté au déploiement Docker.

---

### ADR-002 — JSONB pour les attributs non mappés

**Contexte** : les fichiers Excel sources ont des colonnes hétérogènes (profondeur, débit, bailleur, observations, etc.). Certaines sont mappées vers des champs standard (`region_brute`, `type_ouvrage_brut`...), d'autres non. On veut **conserver** les colonnes non mappées sans figer le schéma à chaque nouveau fichier.

**Décision** : stocker les attributs non mappés dans des colonnes **JSONB** (`ouvrage.metadata`, `localite.metadata`, `cgpe.metadata`). Convention : `brut_<entête Excel>` pour la traçabilité, plus des clés explicites (`metadata.ouvrage.<clé>`) pour les attributs métier stables (ADR-013).

**Conséquences** :
- ✅ Aucune migration à chaque nouveau fichier.
- ✅ Indexation GIN possible (`idx_ouvrage_metadata`).
- ✅ Requêtes JSONB (`metadata->>'profondeur_forage_m'`).
- ✅ Traçabilité (`brut_<entête>` toujours présent).
- ❌ Pas de contrainte de type sur les clés JSONB (une clé peut changer de type d'une ligne à l'autre).
- ❌ Requêtes moins lisibles que des colonnes classiques.
- ❌ Pas de FK, pas de CHECK sur les valeurs JSONB (au MVP).

**Alternatives écartées** :
- **Table EAV (`attribut_definition` + `ouvrage_attribut`)** : plus rigoureux, mais complexe (jointures N..N, pas de typage fort sans efforts). **Reporté en V2** (promotion des clés critiques en attributs de première classe).
- **Colonnes dédiées pour chaque attribut** : schéma figé, migration à chaque nouveau fichier. Rejeté.
- **Texte brut (une colonne `notes`)** : pas de structure, pas d'indexation, pas de requêtes ciblées. Rejeté.

---

### ADR-003 — Colonnes générées pour `geom`

**Contexte** : `geom` (point GPS) est calculé à partir de `latitude_decimal` et `longitude_decimal`. On veut garantir qu'il est **toujours** cohérent avec les lat/lon (pas de désynchronisation), et éviter d'écrire `geom` manuellement dans le code Python.

**Décision** : `geom` est une **colonne générée** (`GENERATED ALWAYS AS geom_from_latlon(lat, lon) STORED`). On n'écrit **jamais** `geom` directement. Si on met à jour `lat`/`lon`, PostgreSQL recalcule `geom` automatiquement.

**Conséquences** :
- ✅ Cohérence garantie (impossible de désynchroniser `geom` et `lat`/`lon`).
- ✅ Pas de code Python pour calculer `geom`.
- ✅ Index GIST possible sur `geom`.
- ❌ La fonction `geom_from_latlon` doit être `IMMUTABLE` (contrainte PostgreSQL sur les colonnes générées). Cela interdit les appels à `now()` ou à des fonctions non déterministes.
- ❌ La fonction doit être créée **avant** les tables (ordre des migrations).
- ❌ Plus difficile à débugger (on ne peut pas insérer `geom` directement pour tester).

**Alternatives écartées** :
- **Trigger `BEFORE INSERT/UPDATE`** : fonctionne, mais moins déclaratif, et le trigger peut être oublié sur une nouvelle table. Rejeté.
- **Calcul en Python** : désynchronisation possible si on oublie de recalculer, et duplication de la logique. Rejeté.
- **Colonne `geom` écrite manuellement** : idem, risque de désynchronisation. Rejeté.

---

### ADR-004 — Trigram + unaccent pour le rapprochement

**Contexte** : les localités dans les fichiers Excel sont mal orthographiées (`"Camp X"` au lieu de `"Campement de X"`, `"Abidjan-Cocody"` au lieu de `"Cocody"`, accents manquants, etc.). On veut un rapprochement **tolérant aux fautes** sans être trop permissif (faux positifs).

**Décision** : utiliser **`pg_trgm`** (similarité trigram, seuil `0.6`) + **`unaccent`** (suppression des accents) + **`lower()`** pour la normalisation. Priorité : exact > alias > trigram.

**Conséquences** :
- ✅ Rattrape les fautes de frappe courantes (une ou deux lettres).
- ✅ `unaccent` gère les accents (`"Cocody"` vs `"Cocodÿ"`).
- ✅ Seuil `0.6` configurable (paramètre `seuil_trigram`).
- ❌ Faux positifs possibles (deux localités homonymes dans des sous-préfectures différentes → le premier match gagne).
- ❌ Pas de filtre par sous-préfecture au MVP (V2 : utiliser `sous_prefecture_brute` pour désambiguïser).
- ❌ `levenshtein` et `soundex` (de `fuzzystrmatch`) ne sont pas utilisés au MVP (V2).

**Alternatives écartées** :
- **Levenshtein** (`fuzzystrmatch`) : coûteux en CPU sur de gros volumes, et moins adapté aux transpositions que le trigram. Rejeté au MVP.
- **Soundex** : adapté à l'anglais, moins bon sur le français et les langues africaines. Rejeté.
- **Pas de rapprochement flou (exact seulement)** : trop de lignes `localite_non_resolue`. Rejeté.
- **Rapprochement manuel (UI)** : chronophage, pas viable pour des milliers de lignes. Reporté en V2 (UI de correction).

---

### ADR-005 — `serial` / `bigserial` (pas d'UUID)

**Contexte** : les IDs des tables (`id_ouvrage`, `id_fichier`, etc.) peuvent être des entiers auto-incrémentés (`serial` / `bigserial`) ou des UUID v4 (aléatoires) ou v7 (triés par date).

**Décision** : utiliser **`serial`** (petites tables) et **`bigserial`** (tables volumineuses). Pas d'UUID.

**Conséquences** :
- ✅ Jointures plus rapides sur des entiers.
- ✅ Débogage manuel plus simple (IDs courts, lisibles).
- ✅ Pas de collision (auto-incrément).
- ❌ IDs prévisibles (pas de sécurité par obscurité). Acceptable, car l'API est protégée par API key + JWT.
- ❌ Pas de génération côté client (les IDs sont attribués par la base). Acceptable, car l'UI ne crée pas d'entités au MVP (sauf via upload, qui génère un `id_fichier` côté serveur).

**Alternatives écartées** :
- **UUID v4** : IDs non prévisibles, mais plus lents en jointure, plus difficiles à déboguer, et inutiles pour un volume modeste. Rejeté.
- **UUID v7** : triés par date, meilleurs que v4, mais toujours plus lourds que `bigserial`. Complexité inutile au MVP. Rejeté.
- **`identity` (SQL standard)** : équivalent à `serial`, mais `serial` est plus courant dans l'écosystème PostgreSQL. Rejeté.

---

### ADR-006 — FastAPI + SQLAlchemy 2.0 + Pydantic 2

**Contexte** : il faut un framework backend Python pour l'API REST (lecture/écriture), avec ORM (SQLAlchemy), validation (Pydantic), migrations (Alembic), et support async (BackgroundTask pour les runs).

**Décision** : **FastAPI 0.115** + **SQLAlchemy 2.0** (sync, psycopg 3) + **Pydantic 2.9** + **Alembic 1.13**.

**Conséquences** :
- ✅ FastAPI : rapide, typé, OpenAPI auto-généré, BackgroundTask natif, dépendances injectables.
- ✅ SQLAlchemy 2.0 : API moderne (`select()`, `Session`), compatible GeoAlchemy2.
- ✅ Pydantic 2 : validation rapide, schémas JSON Schema, `Field`, `field_validator`.
- ✅ Alembic : migrations versionnées, compatible SQLAlchemy.
- ❌ Pas d'async natif sur SQLAlchemy au MVP (sync, `psycopg 3`). Acceptable, car les volumes sont modestes et le BackgroundTask suffit pour les runs.
- ❌ Pas de Django Admin (pas d'UI CRUD auto). Acceptable, car l'UI est React.

**Alternatives écartées** :
- **Django + DRF** : plus lourd, ORM Django moins flexible que SQLAlchemy pour PostGIS. Rejeté.
- **Flask + SQLAlchemy** : pas de BackgroundTask natif, pas d'OpenAPI auto, plus de code boilerplate. Rejeté.
- **FastAPI + SQLModel** : SQLModel est moins mature que SQLAlchemy + Pydantic séparés, et moins compatible avec GeoAlchemy2. Rejeté.
- **Async SQLAlchemy (`asyncpg`)** : complexité inutile au MVP (volumes modestes, BackgroundTask suffit). Rejeté.

---

### ADR-007 — React + Vite + TypeScript + shadcn/ui

**Contexte** : il faut une UI web pour la carte, la liste, le mapping, la qualité et les paramètres. L'UI doit être rapide, typée, et facile à maintenir.

**Décision** : **React 18** + **Vite 5.4** + **TypeScript 5** + **Tailwind CSS 3.4** + **shadcn/ui** (basé sur Radix).

**Conséquences** :
- ✅ React : écosystème mature, composants réutilisables, TanStack Query compatible.
- ✅ Vite : build rapide, HMR instantané, config simple.
- ✅ TypeScript : typage fort, refactoring sûr, meilleure DX.
- ✅ Tailwind : styles utilitaires, pas de CSS à maintenir, cohérent avec shadcn/ui.
- ✅ shadcn/ui : composants accessibles (Radix), personnalisables, pas de dépendance à une lib de composants (on copie le code).
- ❌ Pas de SSR (Vite est SPA). Acceptable, car l'UI est interne (pas de SEO).
- ❌ Pas de framework full-stack (pas de Next.js). Acceptable, car le backend est FastAPI séparé.

**Alternatives écartées** :
- **Next.js** : SSR inutile (UI interne), complexité accrue (routing, API routes redondantes avec FastAPI). Rejeté.
- **Vue 3 + Nuxt** : écosystème plus petit pour la carto (Leaflet + React est mieux supporté), équipe plus familière avec React. Rejeté.
- **Svelte + SvelteKit** : excellent, mais moins de composants prêts (shadcn/ui est React-only), et l'équipe est React. Rejeté.
- **Angular** : trop lourd pour une UI interne, courbe d'apprentissage élevée. Rejeté.

---

### ADR-008 — Leaflet + Esri World Imagery

**Contexte** : il faut une carte interactive avec fond satellite, marqueurs colorés, popups, filtres.

**Décision** : **Leaflet 1.9** + **Esri World Imagery** (tuiles satellite) + **Esri World Boundaries and Places** (tuiles référentiel). Pas de Mapbox, pas de Google Maps.

**Conséquences** :
- ✅ Leaflet : léger, open source, écosystème riche, compatible React (`react-leaflet` ou wrapper manuel).
- ✅ Esri World Imagery : gratuit (avec attribution), haute résolution, `maxNativeZoom: 16`, `maxZoom: 19`.
- ✅ Deux couches : satellite + référentiel (frontières, noms de lieux).
- ❌ Pas de 3D, pas de vue oblique. Acceptable pour l'usage (points 2D).
- ❌ Dépendance à un service externe (Esri). Si Esri tombe, la carte n'a plus de fond. Acceptable au MVP, V2 : cache local ou alternative (OSM, Mapbox).

**Alternatives écartées** :
- **Mapbox GL JS** : payant au-delà du quota gratuit, dépendance à Mapbox. Rejeté.
- **Google Maps** : payant, dépendance à Google, conditions d'utilisation restrictives. Rejeté.
- **OpenStreetMap** : gratuit, mais fond moins lisible pour la végétation (rural). Complément possible en V2.
- **Leaflet + OSM** : fond moins adapté au rural ivoirien (Esri satellite est meilleur). Rejeté au MVP.

---

### ADR-009 — TanStack Query

**Contexte** : l'UI doit gérer l'état serveur (listes, détails, mutations) avec cache, invalidation, polling, et gestion d'erreur.

**Décision** : **TanStack Query 5.59** (ex-React Query). Pas de Redux, pas de Zustand.

**Conséquences** :
- ✅ Cache automatique (les données ne sont pas re-fetchées inutilement).
- ✅ Invalidation ciblée (`invalidateQueries` après mutation).
- ✅ Polling natif (`refetchInterval: 2000` sur `RunStatus`).
- ✅ Gestion d'erreur centralisée (`onError`, `throwOnError`).
- ✅ State local (`useState`) suffit pour l'UI (filtres, sélection).
- ❌ Pas de state global persistant (localStorage, etc.). Acceptable, car l'UI n'a pas besoin de state global persistant au MVP (sauf le JWT, géré séparément).
- ❌ Pas de DevTools aussi puissants que Redux DevTools. Acceptable (TanStack Query DevTools existent, à activer en dev).

**Alternatives écartées** :
- **Redux Toolkit** : trop lourd pour l'état serveur (Redux est fait pour l'état client). Redondant avec TanStack Query. Rejeté.
- **Zustand** : excellent pour l'état client, mais l'UI n'a pas de state client complexe au MVP. Reporté en V2 si besoin.
- **SWR** : similaire à TanStack Query, mais moins de fonctionnalités (pas de mutations optimistes natives). Rejeté.

---

### ADR-010 — Authentification MVP = API key + JWT manuel

**Contexte** : il faut protéger l'API (lecture et écriture) sans mettre en place un système d'authentification complet (login, refresh token, rôles).

**Décision** : **API key** (`X-API-Key`) pour la lecture, **JWT manuel** (`Authorization: Bearer`) pour l'écriture. Pas de login, pas de refresh token, pas de logout au MVP. Le JWT est généré via un script CLI (`create_access_token`) et collé dans l'UI (page Paramètres).

**Conséquences** :
- ✅ Simple à implémenter (pas de flow OAuth, pas de gestion de sessions).
- ✅ Suffisant pour un MVP local (Docker Compose, une seule équipe).
- ✅ API key partagée (`API_KEY_READ`) pour la lecture.
- ✅ JWT signé (`HS256`), expiration `60 min`.
- ❌ Pas de gestion utilisateurs (pas de table `utilisateur` au MVP). Reporté en V2.
- ❌ Pas de rotation de clé. V2.
- ❌ Le JWT expire au bout de 60 min, l'utilisateur doit le régénérer. Acceptable au MVP.
- ❌ Sécurité par obscurité (API key partagée, JWT manuel). Acceptable pour un MVP local.

**Alternatives écartées** :
- **OAuth 2.0 / OpenID Connect** : complexité inutile au MVP (pas de fournisseur d'identité, pas d'utilisateurs). Reporté en V2.
- **Basic Auth** : moins sécurisé que JWT (pas de signature, pas d'expiration). Rejeté.
- **Pas d'authentification** : inacceptable (l'API est accessible en réseau). Rejeté.
- **Session cookies** : incompatible avec une API REST stateless. Rejeté.

---

### ADR-011 — Pagination offset + cursor

**Contexte** : les listes de l'API doivent être paginées. Deux stratégies : offset (`?offset=0&limit=100`) ou cursor (`?cursor=<opaque>&limit=100`).

**Décision** : **offset** pour les petites listes (`sources`, `ref-geo`, `localites`, `fichiers`, `feuilles`, `runs`), **cursor** pour les volumineuses (`ouvrages`, `lignes`).

**Conséquences** :
- ✅ Offset : simple, permet de compter (`total`), adapté aux petites listes.
- ✅ Cursor : performant sur les grosses listes (pas de `OFFSET` coûteux), stable dans le temps (pas de doublons/sauts si des lignes sont insérées).
- ✅ Le client choisit le type de pagination selon l'endpoint (pas de paramètre global).
- ❌ Deux schémas de réponse (`PaginationOffset` vs `PaginationCursor`). Acceptable, car les deux sont bien typés.
- ❌ Le cursor est opaque (base64), pas lisible. Acceptable (c'est voulu).

**Alternatives écartées** :
- **Cursor partout** : inutile pour les petites listes (pas de `total`, pas de saut de page). Rejeté.
- **Offset partout** : coûteux sur les grosses listes (`OFFSET 100000` scanne 100 000 lignes). Rejeté.
- **GraphQL** : trop complexe pour le besoin (une API REST suffit). Rejeté.

---

### ADR-012 — RFC 7807 pour les erreurs

**Contexte** : l'API doit retourner des erreurs **structurées** et **cohérentes** pour que l'UI puisse les afficher (toasts) et les déboguer.

**Décision** : utiliser **RFC 7807** (Problem Details for HTTP APIs). Format : `{type, title, status, detail, instance, errors?}`.

**Conséquences** :
- ✅ Format standard, bien documenté, compatible avec la plupart des clients HTTP.
- ✅ Le champ `type` (URI) est stable et documenté (section 4.4).
- ✅ Le champ `errors` (optionnel) permet des erreurs de validation détaillées (422).
- ✅ L'UI peut parser `title` + `detail` pour les toasts.
- ❌ Plus verbeux qu'un simple `{"error": "..."}`. Acceptable.
- ❌ Nécessite une gestion centralisée côté FastAPI (`HTTPException` + handler custom). Acceptable.

**Alternatives écartées** :
- **Format maison (`{"error": "...", "code": 42}`)** : pas standard, pas documenté, moins interopérable. Rejeté.
- **RFC 9457** (successeur de 7807) : identique en pratique, pas encore répandu. Rejeté (on reste sur 7807, compatible).
- **Pas de format structuré (juste `detail`)** : pas de distinction entre types d'erreur, l'UI ne peut pas adapter son comportement. Rejeté.

---

### ADR-013 — `metadata.<entité>.<clé>` pour les attributs explicites

**Contexte** : l'utilisateur veut parfois créer des **attributs métier stables** (ex. `profondeur_forage_m`) à partir d'une colonne Excel, sans attendre une migration pour ajouter une colonne dédiée. La convention `brut_<entête>` (ADR-002) préserve l'entête, mais ne normalise pas la clé.

**Décision** : permettre à `mapping_feuille.champ_cible` de contenir `metadata.ouvrage.<clé>`, `metadata.localite.<clé>` ou `metadata.cgpe.<clé>`. La valeur est stockée dans le `metadata` de l'entité consolidée, sous la clé explicite (`snake_case`, documentée dans `metadata_conventions.md`). La valeur brute reste **toujours** dans `donnees_brutes` et `metadata.brut_<entête>` (traçabilité).

**Conséquences** :
- ✅ L'utilisateur crée des attributs métier stables sans migration.
- ✅ La clé est normalisée (`snake_case`), donc exploitable dans des requêtes ciblées (`metadata->>'profondeur_forage_m'`).
- ✅ Traçabilité conservée (`brut_<entête>` toujours présent).
- ✅ V2 : promotion possible en attribut de première classe (`attribut_definition` + `ouvrage_attribut`).
- ❌ La clé doit être documentée (`metadata_conventions.md`), sinon risque d'incohérence.
- ❌ Pas de validation de type (une clé peut changer de type d'une ligne à l'autre). Acceptable au MVP.
- ❌ Pas de contrainte d'unicité (deux fichiers peuvent créer la même clé avec des valeurs différentes). Acceptable (la consolidation fusionne).

**Alternatives écartées** :
- **Tout en `brut_<entête>`** (ADR-002 seul) : pas de clé normalisée, requêtes ciblées difficiles. Rejeté.
- **Table EAV (`attribut_definition` + `ouvrage_attribut`)** : trop complexe au MVP. Reporté en V2.
- **Colonne dédiée par attribut** : schéma figé, migration à chaque nouveau fichier. Rejeté.

---

### ADR-014 — Suppression de `type_ouvrage` (refactoring sémantique)

**Contexte** : l'ancien modèle avait une table `type_ouvrage` (PMH, HVA, PEA, `"Forage ADM"`, `"Sondage"`...) qui **mélangeait** trois concepts distincts : la nature physique (`puits` / `forage`), le mode d'alimentation (`PMH` / `HVA` / `PEA` / `HV`), et la réalisation (`public` / `prive`). Une discussion avec le sous-directeur de la DHR a révélé cette confusion.

**Décision** : **supprimer** la table `type_ouvrage`. Le concept est éclaté en **3 colonnes** sur `ouvrage` :
- `nature_ouvrage` : `puits` | `forage` | `inconnu`.
- `type_alimentation` : `PMH` | `HVA` | `PEA` | `HV` | `AUTRE`.
- `realisation_par` : `public` | `prive` | `inconnu`.

L'interprétation du contenu (`"Forage ADM"` → `nature=forage` + `realisation=public`) est faite à la consolidation par `_map_nature`, `_map_alimentation`, `_map_realisation`.

**Conséquences** :
- ✅ Modèle sémantiquement correct (3 concepts distincts).
- ✅ Requêtes ciblées (`WHERE nature_ouvrage = 'forage' AND type_alimentation = 'PMH'`).
- ✅ Filtres UI plus précis (3 dropdowns au lieu d'un).
- ✅ Mapping plus clair (P11 : séparer le mapping de l'interprétation).
- ❌ Refactoring lourd (migration, models, services, UI).
- ❌ Certains fichiers n'ont qu'une colonne `Type_Ouvrage` (ex. `"Forage ADM"`), il faut la décortiquer (`_map_nature` + `_map_realisation`).

**Alternatives écartées** :
- **Garder `type_ouvrage`** (table unique) : mélange sémantique, filtres imprécis, confusion dans l'UI. Rejeté.
- **Ajouter des colonnes à `type_ouvrage`** (`nature`, `alimentation`, `realisation`) : complexité inutile (une table pour 3 colonnes). Rejeté.
- **Garder `type_ouvrage` + ajouter les 3 colonnes** : redondance, risque d'incohérence. Rejeté.

---

### ADR-015 — 6 statuts de qualité (règles conservatrices)

**Contexte** : chaque ligne ingérée doit être qualifiée (`ok`, invalide, non résolue, etc.) pour que la DHR sache ce qui est exploitable et ce qui ne l'est pas. Les règles doivent être **conservatrices** : ne pas rejeter ce qui est exploitable, ne pas consolider ce qui est manifestement faux.

**Décision** : **6 statuts** implémentés au MVP :
- `'ok'` : ligne valide (coordonnées OK, localité résolue, attributs exploitables). Consolidée.
- `'geom_invalide'` : coordonnées manquantes ou invalides. Non consolidée.
- `'localite_non_resolue'` : localité non trouvée au rapprochement. Non consolidée.
- `'type_ouvrage_inconnu'` : attributs métier indéterminés (`nature='inconnu'`, `alimentation='AUTRE'`, `realisation='inconnu'`). **Consolidée quand même** (l'ouvrage existe physiquement, marqué pour requalification V2).
- `'rejete'` : ligne manifestement inexploitable (total, sous-total). **Non stockée**.
- `'doublon_suspect'` : `code_ouvrage` déjà vu avec coordonnées > 1 km. Non consolidée.

**Conséquences** :
- ✅ Règles précises, testables (section 2.3.6).
- ✅ Conservatrices : on ne rejette que l'inexploitable, on ne signale que le probable.
- ✅ `'type_ouvrage_inconnu'` est consolidé (l'ouvrage apparaît sur la carte), mais marqué pour requalification.
- ❌ `'rejete'` n'est pas stocké (perte de la ligne). Acceptable au MVP, V2 : stocker pour correction manuelle.
- ❌ `'doublon_suspect'` est un seuil arbitraire (1 km). Acceptable, V2 : résolution manuelle.

**Alternatives écartées** :
- **Un seul statut booléen (`valide` / `invalide`)** : pas assez précis, l'UI ne peut pas distinguer les cas. Rejeté.
- **Statuts plus granulaires** (ex. `'coordonnee_manquante'`, `'coordonnee_hors_bornes'`) : complexité inutile, pas de besoin exprimé. Rejeté.
- **Rejeter tout ce qui n'est pas `'ok'`** : trop agressif, on perd des ouvrages exploitables (`type_ouvrage_inconnu`). Rejeté.

---

### ADR-016 — Dédoublonnage par `code_ouvrage` puis tuple

**Contexte** : un même ouvrage peut apparaître dans plusieurs fichiers (ONEP, SODECI, UNICEF...). Il faut le **dédoublonner** à la consolidation pour éviter les doublons dans la carte et l'export.

**Décision** : dédoublonner en **deux priorités** :
1. `code_ouvrage` identique (le plus fiable).
2. `(id_localite, nature_ouvrage, type_alimentation, annee_realisation)` identiques (avec au moins un champ non NULL).

Si trouvé → mise à jour (champs vides complétés, `metadata` et `qualite_eau` fusionnés). Sinon → création.

**Conséquences** :
- ✅ Dédoublonnage automatique, pas de doublons dans la carte.
- ✅ Deux fichiers qui mentionnent le même ouvrage → un seul `ouvrage`.
- ✅ Mise à jour incrémentale (complète les champs vides).
- ❌ `code_ouvrage` sans `id_localite` : deux localités différentes avec le même code peuvent être fusionnées à tort. Risque accepté au MVP.
- ❌ Le tuple `(id_localite, nature, alimentation, annee)` peut être trop vague si tous les champs sont NULL. On ne dédoublonne pas dans ce cas (condition : au moins un champ non NULL).
- ❌ Pas de résolution manuelle au MVP (V2).

**Alternatives écartées** :
- **Dédoublonner par `code_ouvrage` uniquement** : risque de fusion à tort (codes locaux). Rejeté.
- **Dédoublonner par tuple uniquement** : ne détecte pas les doublons avec des attributs incomplets. Rejeté.
- **Pas de dédoublonnage** : doublons dans la carte et l'export. Rejeté.
- **Résolution manuelle uniquement** : chronophage, pas viable pour des milliers d'ouvrages. Reporté en V2 (UI de résolution).

---

### ADR-017 — Pas de filtre `district`

**Contexte** : la DHR veut filtrer les ouvrages par région, département, sous-préfecture, localité. Historiquement, il y avait aussi un filtre par district. Mais la réforme territoriale ivoirienne a supprimé les districts, sauf Abidjan et Yamoussoukro (qui ne sont pas concernés par l'hydraulique rurale).

**Décision** : **pas de filtre `district`** dans l'UI ni dans l'API. Le filtre géographique se fait par **région → département → sous-préfecture → localité**. Exception : le **KPI `par_district`** est conservé dans la feuille Synthèse de l'export Excel (information utile pour la DHR).

**Conséquences** :
- ✅ Cohérent avec la réforme territoriale.
- ✅ Filtre géographique plus simple (4 niveaux au lieu de 5).
- ✅ Le KPI `par_district` reste disponible dans l'export Excel (pas dans l'UI).
- ❌ Si un jour les districts sont rétablis, il faudra réintroduire le filtre. Acceptable (la réforme est récente et stable).
- ❌ La vue `v_points_consolides` n'expose pas le district. Si l'UI veut l'afficher, elle devra faire une requête supplémentaire. Acceptable (le district n'est pas un niveau de filtre pertinent).

**Alternatives écartées** :
- **Garder le filtre `district`** : obsolète, complexité inutile. Rejeté.
- **Garder le district dans les vues mais pas dans les filtres** : complexité inutile, pas de besoin. Rejeté.

---

### ADR-018 — Migration initiale unique

**Contexte** : l'historique des migrations contient 5 migrations + un patch `qualite_eau`, avec de la dette technique accumulée (noms de colonnes incohérents, statuts mal implémentés, etc.). La Bible acte le **refactoring sémantique** (ADR-014) et la **réécriture du socle** (section 2.1.6).

**Décision** : **une migration initiale unique** (`0001_initial.py`) remplace l'historique. La base est **recréée from scratch** (`DROP SCHEMA public CASCADE; CREATE SCHEMA public;` puis `alembic upgrade head`). `schema.sql` est régénéré à partir de la Bible.

**Conséquences** :
- ✅ Schéma propre, aligné sur la Bible.
- ✅ Pas de dette technique conservée par compatibilité.
- ✅ Une seule migration à maintenir au MVP (les suivantes seront `0002`, `0003`, ...).
- ❌ Perte de l'historique des migrations (pas de rollback vers une version antérieure). Acceptable au MVP (pas de production).
- ❌ Les données existantes sont perdues (la base est recréée). Acceptable au MVP (pas de données de production).
- ❌ Point de non-retour : une fois la migration initiale générée et la base recréée, on ne revient pas aux anciennes migrations.

**Alternatives écartées** :
- **Patch incrémental des migrations existantes** : conserve la dette technique, complexité accrue, risque d'incohérence. Rejeté.
- **Conserver les anciennes migrations + ajouter une migration de refactoring** : mélange de schémas, difficile à maintenir. Rejeté.
- **Pas de migration (schema.sql seul)** : pas de versioning, pas de rollback. Rejeté.

---

## 7. Dette technique et points ouverts

Cette section recense les **écarts connus**, les **contraintes acceptées** et les **travaux reportés en V2**. Elle est mise à jour à chaque fin de phase.

### 7.1 Écarts Bible ↔ Code (à corriger en Phase D)

| #  | Écart                                                                                                                | Impact                                                                                 | Résolution                       |
|----|----------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|----------------------------------|
| B1 | `export.py` importe `TypeOuvrage` (supprimé)                                                                         | Bloque le démarrage du backend                                                         | Réécriture `export.py` (Phase D) |
| B2 | `models.py` : `nature_ouvrage_brut` / `type_alimentation_brut` au lieu de `type_ouvrage_brut` / `usage_ouvrage_brut` | Schéma non conforme                                                                    | Alignement `models.py` (Phase C) |
| B3 | `models.py` : CHECK `statut_qualite` contient `'type_alimentation_inconnu'`                                          | Faute de frappe                                                                        | Alignement (Phase C)             |
| B4 | `models.py` : `UNIQUE (id_run, num_ligne_source)` au lieu de `(id_feuille, id_run, num_ligne_source)`                | Bug potentiel (collision entre feuilles)                                               | Alignement (Phase C)             |
| B5 | `ingestion.py` : aucune détection de rejets                                                                          | `nb_rejetes` toujours 0, cohérence fausse                                              | Implémentation (Phase D)         |
| B6 | `consolidation.py` : `doublon_suspect`, `type_ouvrage_inconnu`, `qualite_eau` non implémentés                        | 3 statuts/règles manquants                                                             | Implémentation (Phase D)         |
| I1 | `ingestion.py` : `ligne.get("departement_brute")` au lieu de `departement_brut`                                      | `departement_brut` toujours NULL                                                       | Correction (Phase D)             |
| I2 | `ingestion.py` : met à jour `fichier.statut` à la fin de l'ingestion                                                 | `fichier.statut` faux pendant rapprochement/consolidation                              | Correction (Phase D, cf. 3.2.4)  |
| I3 | `rapprochement.py` : `message_qualite` avec suffixe `(méthode: ...)`                                                 | Format non strict                                                                      | Correction (Phase D, cf. 3.2.2)  |
| I4 | `models.py` : noms d'index `idx_ligne_nature_ouvrage` / `idx_ligne_type_alimentation` sur `ligne_ingeree`            | Non conformes à 2.2.B (qui liste `idx_ligne_type_ouvrage` / `idx_ligne_usage_ouvrage`) | Renommage (Phase C)              |

### 7.2 Écarts `openapi.yaml` (à corriger en Phase D)

| #   | Écart                                                   | Résolution                                                               |
|-----|---------------------------------------------------------|--------------------------------------------------------------------------|
| O1  | `/types-ouvrage` encore présent                         | Retirer (handoff : déjà supprimé)                                        |
| O2  | `Ouvrage.type_ouvrage` (objet)                          | Remplacer par `nature_ouvrage`, `type_alimentation`, `realisation_par`   |
| O3  | Filtre `district` sur `/ouvrages`, `/carto/tous/points` | Retirer (cf. C7)                                                         |
| O4  | `LigneIngeree` sans `usage_ouvrage_brut`                | Ajouter                                                                  |
| O5  | Filtre `type_ouvrage` sur `/ouvrages`                   | Remplacer par `nature_ouvrage` + `type_alimentation` + `realisation_par` |
| OI1 | `FeatureCollectionPoints` a un `type: object` en double | Corriger la syntaxe YAML                                                 |
| OI2 | `/types-ouvrage` référencé dans tags et description     | Retirer                                                                  |

### 7.3 Écarts `metadata_conventions.md` (à réécrire)

| #  | Écart                                                         | Résolution                                                                                                       |
|----|---------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| M1 | Convention `snake_case` normalisée vs `brut_<entête>` (Bible) | Réécrire le doc : `brut_<entête>` au MVP, normalisation V2                                                       |
| M2 | `champ_cible = NULL` → `donnees_brutes` seulement             | Corriger : → `metadata.brut_<entête>` **et** `donnees_brutes`                                                    |
| M3 | Liste de clés normalisées (4.1–4.3)                           | Marquer comme « clés à promouvoir en V2 », pas « clés à créer au MVP »                                           |
| M4 | `attribut_definition` + `ouvrage_attribut` (V2)               | Intégrer dans la section 7 (V2)                                                                                  |
| M5 | `metadata_sources` (V2)                                       | Intégrer dans la section 7 (V2)                                                                                  |
| M6 | `metadata.<entité>.<clé>`                                     | `metadata_conventions.md` ne documente pas `metadata.<entité>.<clé>` comme destination possible de `champ_cible` |


### 7.4 Contraintes acceptées au MVP

| #   | Contrainte                                         | Raison                          | V2                                       |
|-----|----------------------------------------------------|---------------------------------|------------------------------------------|
| A1  | Pas de filtre `district` dans l'UI                 | Réforme territoriale            | —                                        |
| A2  | Dédoublonnage `code_ouvrage` sans `id_localite`    | Risque de fusion à tort accepté | Ajouter `id_localite`                    |
| A3  | Trigram sans filtre sous-préfecture                | Faux positifs possibles         | Utiliser `sous_prefecture_brute`         |
| A4  | Lignes rejetées non stockées                       | Pollue la base                  | Stocker avec `statut_qualite = 'rejete'` |
| A5  | Alias localités non alimentés                      | Pas critique au MVP             | UI de correction                         |
| A6  | CGPE non créés                                     | V2                              | Détection + création                     |
| A7  | Projets de financement non créés                   | V2                              | UI de gestion                            |
| A8  | Import auto localités                              | Manuel suffit                   | Import auto sur détection feuille        |
| A9  | Création manuelle localités/ouvrages               | V2                              | UI dédiée                                |
| A10 | Pas de gestion utilisateurs (rôles)                | JWT manuel suffit               | Table `utilisateur` + rôles              |
| A11 | Pas de déploiement prod                            | MVP local Docker                | CI/CD + déploiement                      |
| A12 | `Localite.geom_centre` non exposé                  | V2                              | Sérialisation GeoJSON                    |
| A13 | Filtre bailleur exposé sans données                | Attente financements réels      | —                                        |
| A14 | `metadata` non normalisé (`brut_<entête>`)         | Zéro effort MVP                 | Normalisation V2 (promotion)             |
| A15 | `attribut_definition` + `ouvrage_attribut` absents | V2                              | Promotion des clés critiques             |

### 7.5 Points ouverts du handoff (statut)

| #  | Point                                        | Statut                                                                                                                                       |
|----|----------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| D1 | Filtre bailleur (backend OK, pas de données) | Accepté (A13)                                                                                                                                |
| D2 | Import auto localités                        | V2 (A8)                                                                                                                                      |
| D3 | Attributs `metadata` dynamiques (mapping UI) | Phase 6.3                                                                                                                                    |
| D4 | Création manuelle localités                  | V2 (A9)                                                                                                                                      |
| D5 | `Localite.geom_centre` non sérialisé         | V2 (A12) — **partiellement résolu** : exposé dans `Localite(détail) via geom_centre`, pas dans `LocaliteResume` (liste). Comportement voulu. |
| D6 | DMS corrompu (1 ligne)                       | Accepté (cas normal)                                                                                                                         |
| D7 | Déploiement prod                             | V2 (A11)                                                                                                                                     |
| D8 | Gestion utilisateurs                         | V2 (A10)                                                                                                                                     |
| D9 | Refactoring exports (KPI)                    | Résolu par Phase D (B1)                                                                                                                      |

### 7.6 Décisions de correction (traçabilité)

| Décision       | Section     | Résumé                                                             |
|----------------|-------------|--------------------------------------------------------------------|
| A1 (arbitrage) | 1.4         | `par_district` gardé en KPI export, pas en filtre UI               |
| A2 (arbitrage) | 3.2.2       | `message_qualite` format strict, sans suffixe debug                |
| A3 (arbitrage) | 3.2.4       | `fichier.statut` mis à jour par `run.py`, pas `ingestion.py`       |
| A4 (arbitrage) | 2.1.2 (P2)  | « Ignorer » = metadata au MVP, vraie suppression V2                |
| A5 (arbitrage) | 2.2.B       | Index renommés `idx_ligne_type_ouvrage`, `idx_ligne_usage_ouvrage` |
| A6 (arbitrage) | 2.2.B       | `UNIQUE (id_feuille, id_run, num_ligne_source)`                    |
| A7 (arbitrage) | 2.1.1       | `type_ouvrage` supprimé partout                                    |
| B1 (arbitrage) | 2.3.4 / 7.3 | `metadata` = `brut_<entête>` au MVP                                |
| B2 (arbitrage) | 2.3.4       | `champ_cible = NULL` → `metadata.brut_<entête>`                    |
| B3 (arbitrage) | 7.2         | `/types-ouvrage` retiré de l'openapi                               |
| B4 (arbitrage) | 1.4 / C7    | Filtre `district` retiré, KPI `par_district` gardé                 |
| B5 (arbitrage) | Section 4   | `PaginationCursor`, RFC 7807, `include=metadata` documentés        |

### 7.7 Récapitulatif des livrables de la réécriture

| Livrable                           | Phase | Statut   |
|------------------------------------|-------|----------|
| Bible v1.0 complète (sections 1–8) | A     | En cours |
| `CONSTITUTION.md`                  | B     | À faire  |
| `sql/schema.sql` régénéré          | C     | À faire  |
| `alembic/versions/0001_initial.py` | C     | À faire  |
| `app/models.py` aligné             | C     | À faire  |
| Services alignés (Phase D)         | D     | À faire  |
| Tests + CI GitHub Actions          | D     | À faire  |


---

# Vérification — Section 6 appliquée

J'ai relu la section 6. **Tout est conforme.** Les 18 ADR (ADR-001 à ADR-018) sont en place, avec le format standard (Contexte / Décision / Conséquences / Alternatives écartées), et l'index en début de section.

**La section 6 est validée.** On peut avancer sur la section 8 (la dernière).

---

## Petites remarques éditoriales (à traiter en passe finale)

| # | Détail                                                                                                                                                                                                                                                                                      | Impact                                                                                                                                                                            |
|---|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | La table des matières indique toujours `6. [Décisions d'architecture (ADR)](#6-decisions-darchitecture)` avec les sous-sections **6.1 → 6.18** (les ADR numérotés). Or dans le corps de la section, les ADR sont numérotés **ADR-001 → ADR-018**. Deux systèmes de numérotation coexistent. | À harmoniser : soit la ToC utilise ADR-001 → ADR-018, soit le corps utilise 6.1 → 6.18. Je recommande **ADR-001 → ADR-018** (plus parlant, immuable), et la ToC doit refléter ça. |
| 2 | La ToC met `8. Méthodologie de travail *(à venir)*` — à mettre à jour après la section 8.                                                                                                                                                                                                   | À faire en passe finale                                                                                                                                                           |
| 3 | La ligne `M6` de 7.3 est maintenant remplie ✅.                                                                                                                                                                                                                                              | OK                                                                                                                                                                                |
| 4 | La section 7 est toujours **après la section 6** (bien), mais la ToC la liste en 7. Elle est cohérente.                                                                                                                                                                                     | OK                                                                                                                                                                                |

---

## 8. Méthodologie de travail

Cette section définit les **conventions**, l'**architecture cible**, les **outils de qualité**, le **workflow** et les **phases du projet**. Elle fait autorité sur le code et les processus. Elle est **contraignante** : toute contribution doit la respecter.

### 8.1 Conventions de code

#### 8.1.1 Python (backend)

- **Version** : Python 3.12.
- **Style** : PEP 8, avec `ruff` (lint + format). Ligne max : 100 caractères.
- **Imports** : triés par `ruff` (`isort` intégré). Ordre : stdlib, third-party, app.
- **Type hints** : **obligatoires** sur toutes les fonctions publiques (signatures, retours). `from __future__ import annotations` en tête de chaque fichier.
- **Docstrings** : style Google. Obligatoires sur les fonctions publiques (mais pas sur les helpers internes triviaux).
- **Nommage** :
    - `snake_case` : variables, fonctions, modules, packages.
    - `PascalCase` : classes.
    - `UPPER_SNAKE_CASE` : constantes module-level.
    - Préfixe `_` : fonctions/variables privées.
- **Pas de `Any`** non justifié. Si `Any` est utilisé, un commentaire explique pourquoi.
- **Pas de `print()`** dans le code de production (utiliser `logging`).
- **Pas de `except:`** nu (toujours préciser l'exception).
- **Pas de mutable default argument** (`def f(x=[])` → `def f(x=None)`).

**Configuration `ruff`** (dans `pyproject.toml`) :

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM", "RUF"]
ignore = ["E501"]  # géré par le formatteur

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

**Configuration `mypy`** (dans `pyproject.toml`) :

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
plugins = ["pydantic.mypy"]
```

`mypy --strict` est **obligatoire** sur `services/` et `models/`. Les routers et les scripts CLI peuvent être en mode non-strict (mais typés quand même).

#### 8.1.2 SQL

- **Style** : `snake_case`, mots-clés SQL en **MAJUSCULES** (`SELECT`, `FROM`, `WHERE`).
- **Nommage** : voir section 2.3.4 (tables au singulier, `idx_<table>_<colonne>`, `<table>_<colonne>_check`, etc.).
- **Pas de `SELECT *`** en production (toujours lister les colonnes).
- **Pas de requêtes dans les routers** (toujours via les services).
- **Requêtes paramétrées** (jamais de f-string SQL, risque d'injection).
- **Commentaires** : `--` pour les commentaires en ligne, `/* */` pour les blocs.
- **Migrations Alembic** : SQL brut dans `op.execute()` pour les triggers, fonctions et index GIN/GIST (SQLAlchemy ne les gère pas nativement).

#### 8.1.3 TypeScript (frontend)

- **Style** : `eslint` + `prettier`. Ligne max : 100 caractères.
- **Type hints** : **obligatoires** (pas de `any` implicite, `strict: true` dans `tsconfig.json`).
- **Nommage** :
    - `camelCase` : variables, fonctions, props.
    - `PascalCase` : composants React, types, interfaces.
    - `UPPER_SNAKE_CASE` : constantes globales.
- **Composants React** : fonctionnels uniquement (pas de classes). Hooks (`useState`, `useEffect`, `useQuery`) en haut du composant.
- **Props** : toujours typées via `interface Props { ... }`.
- **Imports** : triés par `eslint-plugin-import` (stdlib, third-party, alias `@/`).
- **Pas de `console.log`** en production (utiliser un logger ou retirer).
- **Pas de `any`** sauf justifié (commentaire).

**Configuration `eslint`** (dans `frontend/.eslintrc.cjs`) :

```js
module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  rules: {
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
  },
}
```

**Configuration `prettier`** (dans `frontend/.prettierrc`) :

```json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100
}
```

#### 8.1.4 JSON / JSONB

- **Clés** : `snake_case` (`brut_<entête>`, `profondeur_forage_m`).
- **Valeurs** : typées (nombre, booléen, string ISO 8601 pour les dates).
- **Pas de `null`** : si la valeur est absente, la clé n'est pas écrite.
- **Pas de clé générique** (`valeur1`, `champ2`).

#### 8.1.5 Git

- **Branches** :
    - `main` : branche principale, protégée (pas de push direct).
    - `feat/<sujet>` : nouvelle fonctionnalité.
    - `fix/<sujet>` : correction de bug.
    - `docs/<sujet>` : documentation (Bible, README, ADR).
    - `refactor/<sujet>` : refactoring sans changement fonctionnel.
    - `chore/<sujet>` : tâches techniques (CI, dépendances, config).
- **Commits** : conventionnels (`Conventional Commits`).
    - `feat: ajouter l'export CSV des ouvrages`
    - `fix: corriger le message_qualite du rapprochement`
    - `docs: mettre à jour la section 3.2 de la Bible`
    - `refactor: aligner models.py sur la Bible`
    - `chore: ajouter ruff dans le CI`
    - `test: ajouter les tests d'ingestion`
- **Messages** : impératif, en français, max 72 caractères sur la première ligne. Corps optionnel (détails, références aux issues).
- **Merge** : `--no-ff` (préserver l'historique des branches). Pas de squash au MVP (garder la traçabilité).
- **Pull requests** : 1 PR = 1 sujet. Pas de PR fourre-tout. Description obligatoire (quoi, pourquoi, comment tester). Revue obligatoire (même en solo : relire sa propre PR à froid).

### 8.2 Architecture cible

#### 8.2.1 Backend (FastAPI)

```text
backend/
├── app/
│   ├── main.py              # Point d'entrée FastAPI (app, CORS, routers)
│   ├── config.py            # Settings (Pydantic)
│   ├── db.py                # Engine, Session, Base, get_db
│   ├── models/              # Modèles SQLAlchemy (miroir de la Bible)
│   │   ├── referentiels.py  # source, ref_geo_admin, localite, localite_alias
│   │   ├── ingestion.py     # fichier, feuille, mapping_feuille, ingestion_run, ligne_ingeree
│   │   └── metier.py        # ouvrage, cgpe, projet_financement, ouvrage_projet
│   ├── schemas/             # Schémas Pydantic (request/response)
│   │   ├── common.py        # Problem, Pagination, etc.
│   │   ├── referentiels.py  # Source, RefGeoAdmin, Localite, etc.
│   │   ├── fichiers.py      # Fichier, Feuille, Mapping, etc.
│   │   ├── ouvrages.py      # Ouvrage, CGPE, etc.
│   │   └── qualite.py       # QualiteFichier, etc.
│   ├── routers/             # Endpoints HTTP (fins, délèguent aux services)
│   │   ├── referentiels.py  # /sources, /ref-geo, /localites
│   │   ├── fichiers.py      # /fichiers, /fichiers/{id}/mapping
│   │   ├── ingestion.py     # /fichiers/{id}/runs, /runs, /lignes
│   │   ├── ouvrages.py      # /ouvrages, /cgpe, /ouvrages/export
│   │   ├── carto.py         # /carto/*
│   │   └── qualite.py       # /qualite/*
│   ├── services/            # Logique métier (indépendante de FastAPI)
│   │   ├── coordonnees.py   # parser_coordonnees
│   │   ├── patterns.py      # COLUMN_PATTERNS, INDICATEURS_SANITAIRES
│   │   ├── upload.py        # Sauvegarde + détection feuilles
│   │   ├── mapping.py       # Proposition + sauvegarde + chargement
│   │   ├── ingestion.py     # ingerer_fichier, ingerer_feuille
│   │   ├── rapprochement.py # rapprocher_lignes_run
│   │   ├── consolidation.py # consolider_lignes_run
│   │   ├── export.py        # export_ouvrages_xlsx, export_ouvrages_csv
│   │   └── run.py           # Orchestrateur (pipeline complet)
│   ├── auth.py              # API key + JWT
│   └── deps.py              # Dépendances FastAPI (pagination, filtres)
├── alembic/
│   ├── versions/
│   │   └── 0001_initial.py  # Migration unique
│   └── env.py
├── scripts/                 # Scripts CLI (import, test, consolidation)
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
│   └── test_api/
├── sql/
│   └── schema.sql           # Régénéré depuis la Bible
├── pyproject.toml
├── requirements.txt
└── Dockerfile
```

**Règles de couches** :
- **Routers** : fins. Valident les entrées (Pydantic), appellent les services, retournent les réponses. **Pas de logique métier**, **pas d'accès DB direct**.
- **Services** : logique métier. Reçoivent une `Session` SQLAlchemy, lisent/écrivent les modèles. **Pas de dépendance à FastAPI** (testables sans HTTP).
- **Models** : miroir exact de la Bible. Pas de logique métier dans les modèles (sauf propriétés calculées triviales).
- **Schemas** : Pydantic. Distincts des modèles (ne pas exposer directement les modèles ORM).

#### 8.2.2 Frontend (React)

```text
frontend/
├── src/
│   ├── pages/               # 1 fichier par page
│   │   ├── Fichiers.tsx
│   │   ├── Mapping.tsx
│   │   ├── Carte.tsx
│   │   ├── Liste.tsx
│   │   ├── Qualite.tsx
│   │   └── Parametres.tsx
│   ├── components/          # Composants transverses
│   │   ├── FiltersPanel.tsx
│   │   ├── MapView.tsx
│   │   ├── RunStatus.tsx
│   │   ├── UploadDialog.tsx
│   │   └── ui/              # Primitives shadcn (Button, Input, Dialog, Badge, ...)
│   ├── lib/
│   │   ├── api.ts           # Client HTTP + types + setJwt/getJwt
│   │   └── utils.ts         # Helpers (formatage dates, escape HTML, etc.)
│   ├── App.tsx              # Routes + layout
│   ├── main.tsx             # Point d'entrée React
│   └── index.css            # Tailwind
├── public/
├── .env                     # VITE_API_KEY (non commité)
├── .env.example             # Template (commité)
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── Dockerfile
```

**Règles de couches** :
- **Pages** : composent les composants, gèrent le state local, appellent l'API via `lib/api.ts`.
- **Components** : réutilisables, sans dépendance à une page spécifique.
- **Lib** : utilitaire, sans dépendance à React (sauf hooks éventuels).

### 8.3 Tests

#### 8.3.1 Backend (pytest)

- **Framework** : `pytest` + `pytest-postgresql` (base éphémère par test) + `httpx` + `pytest-asyncio`.
- **Couverture cible** : **≥ 70 %** sur `services/` et `models/`. Pas d'objectif sur `routers/` (fins, testés indirectement via l'API).
- **Structure** :
    - `tests/conftest.py` : fixtures (base éphémère, session, client HTTP).
    - `tests/fixtures/` : fichiers Excel de test (petits, anonymisés).
    - `tests/test_*.py` : un fichier par service.
    - `tests/test_api/` : un fichier par router (tests HTTP).
- **Conventions** :
    - Nom de test : `test_<fonction>_<cas>` (`test_parser_coordonnees_dms_compact`).
    - Un test = une assertion principale (plusieurs si elles portent sur le même cas).
    - Fixtures pour les données de test (pas de duplication).
    - Tests d'intégration (ingestion → rapprochement → consolidation) sur un fichier de test complet.
- **Exécution** :

```bash
cd backend
pytest                          # tous les tests
pytest tests/test_ingestion.py  # un fichier
pytest -k "coordonnees"         # par mot-clé
pytest --cov=app --cov-report=html  # avec couverture
```

#### 8.3.2 Frontend (vitest)

- **Framework** : `vitest` + `@testing-library/react` + `@testing-library/jest-dom`.
- **Couverture cible** : **≥ 50 %** sur `components/` et `lib/`. Pas d'objectif sur `pages/` (testées manuellement au MVP).
- **Structure** :
    - `src/components/__tests__/` : un fichier par composant.
    - `src/lib/__tests__/` : un fichier par module.
- **Conventions** :
    - Nom de test : `describe('Component', () => { it('should ...', ...) })`.
    - Tester le rendu, les interactions, les états (loading, error, empty).
    - Mocker l'API via `vi.mock('@/lib/api')`.
- **Exécution** :

```bash
cd frontend
npm run test           # tous les tests
npm run test:watch     # mode watch
npm run test:coverage  # avec couverture
```

#### 8.3.3 Tests d'intégration (pipeline complet)

Un test d'intégration **obligatoire** qui :
1. Upload un fichier Excel de test.
2. Lance un run (`mode=complet`).
3. Vérifie `fichier.statut = 'ingere'`, `nb_lignes_total > 0`.
4. Vérifie `ouvrage` créés (`COUNT > 0`).
5. Vérifie `v_qualite_par_fichier` (cohérence des compteurs).
6. Vérifie `v_points_consolides` (au moins un point).

Ce test garantit que le pipeline complet fonctionne (pas seulement les services isolés).

### 8.4 CI/CD (GitHub Actions)

#### 8.4.1 Workflow `ci.yml` (sur chaque PR et push sur `main`)

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:16-3.4
        env:
          POSTGRES_USER: dhr
          POSTGRES_PASSWORD: dhr
          POSTGRES_DB: dhr_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install ruff mypy pytest pytest-cov pytest-postgresql
      - name: Lint (ruff)
        run: cd backend && ruff check .
      - name: Format check (ruff)
        run: cd backend && ruff format --check .
      - name: Type check (mypy)
        run: cd backend && mypy app/services app/models
      - name: Tests (pytest)
        env:
          DATABASE_URL: postgresql+psycopg://dhr:dhr@localhost:5432/dhr_test
          API_KEY_READ: test-api-key
          JWT_SECRET: test-jwt-secret
        run: cd backend && pytest --cov=app --cov-fail-under=70
      - name: Migrations (alembic)
        env:
          DATABASE_URL: postgresql+psycopg://dhr:dhr@localhost:5432/dhr_test
        run: |
          cd backend
          alembic upgrade head
          alembic downgrade base
          alembic upgrade head

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Lint (eslint)
        run: cd frontend && npm run lint
      - name: Type check (tsc)
        run: cd frontend && npm run typecheck
      - name: Tests (vitest)
        run: cd frontend && npm run test
      - name: Build
        run: cd frontend && npm run build
```

**Règles** :
- **Aucune PR ne peut être mergée si la CI est rouge.**
- **Pas de `--no-verify`** sur les commits (les hooks doivent passer).
- **Pas de secrets en clair** dans le repo (utiliser les GitHub Secrets pour la prod, `.env` pour le dev local).

#### 8.4.2 Déploiement (V2)

Pas de déploiement automatique au MVP. En V2 :
- **Staging** : déploiement auto sur `main` (après merge).
- **Production** : déploiement manuel (tag `v*`).
- **Rollback** : `git revert` + redéploiement.

### 8.5 Workflow de contribution

#### 8.5.1 Cycle d'une contribution

1. **Créer une branche** depuis `main` : `git checkout -b feat/mon-sujet`.
2. **Développer** (code + tests).
3. **Vérifier localement** :
    - Backend : `ruff check .`, `ruff format --check .`, `mypy app/services app/models`, `pytest`.
    - Frontend : `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build`.
4. **Committer** avec un message conventionnel.
5. **Pousser** : `git push origin feat/mon-sujet`.
6. **Ouvrir une PR** avec description (quoi, pourquoi, comment tester).
7. **Attendre la CI verte**.
8. **Revue** (même en solo : relire sa propre PR à froid, 24h après).
9. **Merge** : `--no-ff` dans `main`.
10. **Supprimer la branche** (locale et distante).

#### 8.5.2 Règles de PR

- **1 PR = 1 sujet**. Pas de mélange (ex. une PR ne fait pas à la fois une feature et un refactoring).
- **Titre** : même convention que les commits (`feat: ...`, `fix: ...`).
- **Description** : obligatoire, avec :
    - **Quoi** : résumé du changement.
    - **Pourquoi** : référence à la Bible ou à l'issue.
    - **Comment tester** : commandes, étapes manuelles.
    - **Checklist** : cases à cocher (tests, lint, docs, Bible mise à jour si besoin).
- **Taille** : raisonnable (< 500 lignes de diff idéalement). Si plus gros, découper.
- **Revue** : approuver après lecture. Commenter les points bloquants (préfixe `blocking:`) ou non bloquants (préfixe `nit:`).

#### 8.5.3 Mise à jour de la Bible

Toute PR qui :
- **Change un schéma** (table, colonne, contrainte, index) → met à jour la section 2.
- **Change un endpoint** → met à jour la section 4 et l'`openapi.yaml`.
- **Change un composant ou une page** → met à jour la section 5.
- **Prend une décision d'architecture** → ajoute une ADR (section 6).
- **Corrige un écart** → met à jour la section 7 (retirer la ligne de dette).

**La Bible est mise à jour dans la même PR que le code**, pas dans une PR séparée.

### 8.6 Phases du projet

Le projet est découpé en **4 phases** séquentielles. Chaque phase a un **livrable** et une **definition of done** (DoD).

#### 8.6.1 Phase A — Finaliser la Bible

**Objectif** : Bible v1.0 complète (sections 1 → 8), validée.

**Livrable** : `DHR.md` complet, relu, cohérent.

**DoD** :
- Les 8 sections sont écrites et validées.
- Les écarts détectés (C1–C21, R1–R7) sont corrigés.
- La ToC est à jour.
- La section 7 est déplacée après la section 6.
- Les incohérences résiduelles (M6, numérotation ADR vs ToC) sont corrigées.

**Statut** : **en cours** (sections 1–6 et 8 écrites, section 7 écrite, reste la passe finale).

#### 8.6.2 Phase B — Constitution du projet

**Objectif** : `CONSTITUTION.md` validé.

**Livrable** : document court (2–3 pages) qui complète la Bible :
- Conventions de code (rappel synthétique de 8.1).
- Architecture cible (rappel synthétique de 8.2).
- Qualité (rappel synthétique de 8.3).
- CI/CD (rappel synthétique de 8.4).
- Workflow (rappel synthétique de 8.5).

**DoD** :
- `CONSTITUTION.md` est écrit.
- Il ne duplique pas la Bible (il y renvoie).
- Il est validé.

**Statut** : à faire.

#### 8.6.3 Phase C — Socle DB

**Objectif** : base de données recréée, alignée sur la Bible.

**Livrable** :
- `sql/schema.sql` régénéré (12 tables + 3 vues + fonctions + triggers + seed).
- `alembic/versions/0001_initial.py` (migration unique).
- `app/models.py` aligné.
- Base recréée from scratch (`DROP SCHEMA public CASCADE; CREATE SCHEMA public;` puis `alembic upgrade head`).

**DoD** :
- `alembic upgrade head` passe sans erreur.
- `alembic downgrade base` puis `alembic upgrade head` passe (idempotent).
- `\d+` sur chaque table correspond à la Bible (checklist).
- Les 6 sources sont seedées.
- Les fonctions `geom_from_latlon`, `trg_set_updated_at`, `trg_check_localite_geo` existent.
- Les 3 vues existent et se créent sans erreur.
- `models.py` correspond à `schema.sql` (pas de dérive).

**Statut** : à faire.

#### 8.6.4 Phase D — Services, frontend, tests, CI

**Objectif** : code aligné sur la Bible, testé, avec CI verte.

**Livrable** :
- Services alignés (B1–B6, I1–I4 corrigés).
- Frontend aligné (F1–F9 corrigés, `Liste.tsx` et `Qualite.tsx` implémentés).
- `openapi.yaml` aligné (O1–O5, OI1–OI2 corrigés).
- `metadata_conventions.md` réécrit (M1–M6 corrigés).
- Tests backend (pytest) + frontend (vitest).
- CI GitHub Actions verte.

**DoD** :
- Tous les écarts de la section 7 sont corrigés (sauf ceux marqués V2).
- `pytest` passe avec couverture ≥ 70 %.
- `npm run test` passe.
- `ruff check .`, `mypy`, `eslint`, `tsc` passent.
- `npm run build` passe.
- La CI est verte sur `main`.
- Un test d'intégration (pipeline complet) passe.

**Statut** : à faire.

### 8.7 Commandes utiles

#### 8.7.1 Docker Compose

```bash
# Démarrer tous les services (db + backend + frontend)
docker compose up -d --build

# Voir les logs
docker compose logs -f backend

# Redémarrer un service
docker compose restart backend

# Arrêter
docker compose down

# Reset complet (perte de données)
docker compose down -v
docker compose up -d --build
```

#### 8.7.2 Base de données

```bash
# Se connecter à psql
docker compose exec db psql -U dhr -d dhr

# Appliquer les migrations
docker compose exec backend alembic upgrade head

# Reset DB (perte de données)
docker compose exec db psql -U dhr -d dhr -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose exec backend alembic upgrade head

# Vérifier les tables
docker compose exec db psql -U dhr -d dhr -c "\dt"
docker compose exec db psql -U dhr -d dhr -c "\dv"
docker compose exec db psql -U dhr -d dhr -c "\df"
```

#### 8.7.3 Scripts CLI

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

#### 8.7.4 Tests

```bash
# Backend
cd backend
pytest
pytest --cov=app --cov-report=html
pytest tests/test_ingestion.py -v

# Frontend
cd frontend
npm run test
npm run test:coverage
npm run test:watch
```

#### 8.7.5 Qualité

```bash
# Backend
cd backend
ruff check .
ruff format .
mypy app/services app/models

# Frontend
cd frontend
npm run lint
npm run typecheck
npm run build
```

### 8.8 Points de coordination

**Au MVP, l'équipe est réduite (1–2 personnes).** Les points de coordination sont :
- **Daily** (15 min) : ce qui a été fait, ce qui est prévu, blocages.
- **Revue de PR** : obligatoire avant merge.
- **Mise à jour de la Bible** : dans la même PR que le code.
- **Blocages** : signaler immédiatement (pas attendre le daily).

**Règles** :
- **Pas de code non testé** mergé.
- **Pas de `TODO` non référencé** dans la section 7.
- **Pas de dette technique silencieuse** (tout écart à la Bible est documenté en section 7).
- **Pas de PR sans description**.

### 8.9 Hors scope (V2)

| Sujet                                             | Raison           |
|---------------------------------------------------|------------------|
| Déploiement production                            | MVP local Docker |
| Monitoring (Prometheus, Grafana)                  | V2               |
| Logging centralisé (ELK, Loki)                    | V2               |
| Authentification complète (login, OAuth)          | V2               |
| Gestion utilisateurs (table `utilisateur`, rôles) | V2               |
| CI/CD avancé (staging, prod, rollback)            | V2               |
| Tests de charge (Locust, k6)                      | V2               |
| Documentation utilisateur (guide DHR)             | V2               |
| Internationalisation (i18n)                       | V2               |

---

## Passe finale (après application de la section 8)

**Après ces corrections, la Bible est v1.0 finale.** On pourra alors enchaîner sur :
- **Phase B** : `CONSTITUTION.md` (2–3 pages, synthèse de la section 8).
- **Phase C** : `schema.sql` + `0001_initial.py` + `models.py` alignés.
- **Phase D** : services + frontend + tests + CI.

