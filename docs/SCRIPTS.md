
---

# Scripts et pipeline — Projet DHR

**Version** : 1.0
**Date** : 2026-11-03
**Objet** : Documenter les scripts CLI du projet et le pipeline d'ingestion complet.

---

## 1. Vue d'ensemble

Le projet DHR est découpé en **étapes indépendantes**, chacune implémentée par un **service** (`backend/app/services/`) et exposée soit par un **endpoint API** (Phase 3+), soit par un **script CLI** (Phase 4, en attendant les endpoints).

**Pourquoi des scripts CLI ?**

- Permettre de **tester chaque étape séparément** sans dépendre de l'UI.
- **Simuler** ce que fera l'API en Phase 4.4 (upload + run).
- **Débloquer** le développement du front-end et des endpoints en attendant.

**Les scripts CLI seront conservés** même après la Phase 4.4, comme **outils d'administration** (relancer un rapprochement, reconsolider un run, etc.).

---

## 2. Schéma du pipeline complet

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
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ÉTAPE 2 — INGESTION                                                │
│  (à chaque nouveau fichier)                                         │
│                                                                     │
│  Script   : scripts/test_ingestion_reelle.py <fichier.xlsx>         │
│  Service  : services/ingestion.py + services/coordonnees.py         │
│                                                                     │
│  Entrée   : fichier Excel (multi-feuilles)                          │
│  Sortie   : fichier, feuille, ingestion_run, ligne_ingeree          │
│             (donnees_brutes JSONB + coordonnées décimales)          │
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
│  Sortie   : ouvrage (dédoublonné, type/état/GPS)                    │
│             ligne_ingeree.id_ouvrage_consolide                      │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ÉTAPE 5 — LECTURE / EXPORT / CARTO                                 │
│                                                                     │
│  Endpoints : GET /ouvrages, /ouvrages/export,                       │
│              /carto/tous/points, /qualite/fichiers/{id}             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Détail des scripts

### 3.1 `scripts/inventaire_fichiers.py`

**Rôle** : inspecter un fichier Excel (feuilles, entêtes, exemples de lignes) **sans rien insérer en base**.

**Usage** :
```powershell
docker compose exec backend python /app/scripts/inventaire_fichiers.py /app/tests/fixtures/fichier1.xlsx
```

**Sortie** :
- Nombre de feuilles, lignes, colonnes par feuille
- Liste des entêtes
- 3 lignes d'exemple

**Quand l'utiliser** :
- Avant d'ingérer un nouveau fichier, pour comprendre sa structure.
- Pour vérifier que le fichier est bien formé (header_row, colonnes).
- Pour décider quels patterns ajouter à `COLUMN_PATTERNS`.

**Ne touche pas à la base.** C'est un outil de diagnostic.

---

### 3.2 `scripts/test_ingestion.py`

**Rôle** : tester le **mapping automatique** d'un fichier Excel, **sans rien insérer en base**.

**Usage** :
```powershell
docker compose exec backend python /app/scripts/test_ingestion.py /app/tests/fixtures/fichier1.xlsx
```

**Sortie** :
- Pour chaque feuille : `header_row`, colonnes mappées (avec champ cible), colonnes non mappées
- Permet de vérifier que `COLUMN_PATTERNS` reconnaît bien les entêtes.

**Quand l'utiliser** :
- Après avoir ajouté un nouveau fichier, pour vérifier le mapping auto.
- Avant d'ingérer, pour anticiper les colonnes non mappées.

**Ne touche pas à la base.** C'est un outil de diagnostic.

---

### 3.3 `scripts/test_ingestion_reelle.py`

**Rôle** : **ingérer un fichier Excel** en base. Simule ce que fera `POST /fichiers` + `POST /fichiers/{id}/runs` en Phase 4.4.

**Usage** :
```powershell
docker compose exec backend python -u /app/scripts/test_ingestion_reelle.py /app/tests/fixtures/fichier1.xlsx
```

**Ce qu'il fait** :
1. Crée une ligne `fichier` (source, nom, chemin, `statut='en_attente'`).
2. Détecte les feuilles (`detecter_feuilles`) et crée N lignes `feuille`.
3. Crée un `ingestion_run` (`statut='en_cours'`).
4. Appelle `ingerer_fichier` → remplit `ligne_ingeree` (une ligne par ligne Excel).
5. Met à jour `fichier.statut='ingere'`, `run.statut='termine'`.

**Tables remplies** :
- `fichier`
- `feuille`
- `ingestion_run`
- `ligne_ingeree` (avec `donnees_brutes` JSONB + `latitude_decimal`/`longitude_decimal`)

**Tables NON remplies** (volontairement) :
- `localite`, `ref_geo_admin` → c'est `import_localites.py`
- `ligne_ingeree.id_localite` → c'est `test_rapprochement.py`
- `ouvrage` → c'est `consolidation.py`

**Quand l'utiliser** :
- Pour tester l'ingestion d'un nouveau fichier.
- En attendant `POST /fichiers` (Phase 4.4).

**Idempotence** : **non**. Réexécuter crée un nouveau `fichier` + `run`. Pour repartir de zéro, faire un `TRUNCATE` (voir section 4).

---

### 3.4 `scripts/import_localites.py`

**Rôle** : **importer les localités** depuis la feuille `Localités` d'un fichier Excel. Crée la hiérarchie `ref_geo_admin` (district → région → département → sous-préfecture → localité) et les lignes `localite` (nom + GPS + metadata).

**Usage** :
```powershell
docker compose exec backend python -u /app/scripts/import_localites.py /app/tests/fixtures/fichier1.xlsx
```

**Ce qu'il fait** :
1. Lit la feuille `Localités`.
2. Pour chaque ligne :
    - Crée/récupère la hiérarchie `ref_geo_admin` (région, département, sous-préfecture, localité) — avec un **district par défaut** (`DISTRICT_NON_DEFINI`) si le district n'est pas connu.
    - Crée une `localite` rattachée au nœud `localite`.
    - Remplit `metadata` (population, etc.).
3. **Ne duplique pas** les localités existantes (check par `nom_usage` + `id_geo`).

**Tables remplies** :
- `ref_geo_admin` (district, région, département, sous-préfecture, localité)
- `localite`

**Quand l'utiliser** :
- **Une seule fois** au démarrage, pour peupler le référentiel.
- **À chaque nouveau fichier** qui contient une feuille `Localités` avec de nouvelles localités.
- **Après un `TRUNCATE`** de `localite` / `ref_geo_admin` (sinon le rapprochement ne trouve rien).

**Important** : c'est un **pré-requis** pour le rapprochement. Sans localités importées, `test_rapprochement.py` retourne `Non résolu = 100%`.

---

### 3.5 `scripts/test_rapprochement.py`

**Rôle** : **rapprocher** les `ligne_ingeree` d'un run avec les `localite` existantes. Remplit `id_localite` et met à jour `statut_qualite`.

**Usage** :
```powershell
docker compose exec backend python -u /app/scripts/test_rapprochement.py <id_run>
```

**Ce qu'il fait** :
1. Pour chaque `ligne_ingeree` du run avec `statut_qualite='ok'` et `id_localite IS NULL` :
    - Normalise `localite_brute` (minuscules, sans accents).
    - Cherche un **exact match** sur `localite.nom_usage`.
    - Sinon, cherche dans `localite_alias`.
    - Sinon, utilise **trigram similarity** (`pg_trgm`, seuil 0.6).
    - Si trouvé : remplit `id_localite`.
    - Si non trouvé : passe `statut_qualite = 'localite_non_resolue'`.
2. Affiche les stats : exact / alias / trigram / non résolu.

**Tables modifiées** :
- `ligne_ingeree.id_localite`
- `ligne_ingeree.statut_qualite`

**Quand l'utiliser** :
- **Après l'ingestion** (`test_ingestion_reelle.py`).
- **Après l'import des localités** (`import_localites.py`).

**Pré-requis** : `localite` doit contenir des lignes (sinon `Non résolu = 100%`).

---

### 3.6 `scripts/consolidation.py`

**Rôle** : **consolider** les `ligne_ingeree` d'un run en `ouvrage`. Dédoublonne et marque `id_ouvrage_consolide`.

**Usage** :
```powershell
docker compose exec backend python -u /app/scripts/consolidation.py <id_run>
```

**Ce qu'il fait** :
1. Pour chaque `ligne_ingeree` du run avec `statut_qualite='ok'` et `id_localite` rempli :
    - Détermine le **type d'ouvrage** (priorité : nom de la feuille → PMH/HVA/PEA/HV ; fallback : `type_ouvrage_brut`).
    - Détermine l'**état** (`fonctionnel`, `en_panne`, `abandonne`, `inconnu`).
    - Cherche un `ouvrage` existant (dédoublonnage : `code_ouvrage`, puis `(id_localite, id_type_ouvrage, annee_realisation)`).
    - Si trouvé : met à jour les champs vides.
    - Sinon : crée un `ouvrage`.
    - Marque `ligne_ingeree.id_ouvrage_consolide`.
2. Affiche les stats : créés / mis à jour / ignorés / erreurs.

**Tables remplies** :
- `ouvrage` (code, localite, type, etat, annee, lat/lon, metadata)
- `ligne_ingeree.id_ouvrage_consolide`

**Quand l'utiliser** :
- **Après le rapprochement** (`test_rapprochement.py`).

**Pré-requis** : `ligne_ingeree.id_localite` doit être rempli (sinon `Lignes traitées = 0`).

---

## 4. Ordre correct des commandes

```powershell
# ============================================================
# 0. RESET COMPLET (optionnel, pour repartir de zéro)
# ============================================================
docker compose exec db psql -U dhr -d dhr -c "TRUNCATE ligne_ingeree, ingestion_run, feuille, fichier, mapping_feuille, localite, localite_alias, ref_geo_admin, ouvrage, cgpe, projet_financement, ouvrage_projet RESTART IDENTITY CASCADE;"

# ============================================================
# 1. IMPORT DES LOCALITÉS (une seule fois)
# ============================================================
docker compose exec backend python -u /app/scripts/import_localites.py /app/tests/fixtures/fichier1.xlsx 2>&1 | Select-Object -Last 5

# Vérifier
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM localite;"
# Attendu : ~891

# ============================================================
# 2. INGESTION
# ============================================================
docker compose exec backend python -u /app/scripts/test_ingestion_reelle.py /app/tests/fixtures/fichier1.xlsx 2>&1 | Select-Object -Last 5

# Vérifier
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM ligne_ingeree;"
# Attendu : 3511

docker compose exec db psql -U dhr -d dhr -c "SELECT id_run, id_fichier, statut FROM ingestion_run ORDER BY id_run DESC LIMIT 1;"
# Attendu : 1 | 1 | termine (récupérer l'id_run)

# ============================================================
# 3. RAPPROCHEMENT (avec l'id_run récupéré)
# ============================================================
docker compose exec backend python -u /app/scripts/test_rapprochement.py 1 2>&1 | Select-Object -Last 10

# Attendu :
#   Total lignes : 3511
#   Exact match : ~3504
#   Alias : 0
#   Trigram : ~7
#   Non résolu : 0
#   Vide : 0

# Vérifier
docker compose exec db psql -U dhr -d dhr -c "SELECT statut_qualite, COUNT(*) FROM ligne_ingeree GROUP BY statut_qualite;"
# Attendu : ok = 3511

# ============================================================
# 4. CONSOLIDATION
# ============================================================
docker compose exec backend python -u /app/scripts/consolidation.py 1 2>&1 | Select-Object -Last 10

# Attendu :
#   Lignes traitées : 3511
#   Ouvrages créés : ~3511
#   Ouvrages mis à jour : 0
#   Lignes ignorées : 0
#   Erreurs : 0

# Vérifier
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM ouvrage;"
# Attendu : ~3511

docker compose exec db psql -U dhr -d dhr -c "SELECT t.code, COUNT(*) FROM ouvrage o JOIN type_ouvrage t ON t.id_type_ouvrage = o.id_type_ouvrage GROUP BY t.code ORDER BY COUNT(*) DESC;"
# Attendu :
#   PMH   : ~2103
#   HVA   : ~86
#   PEA   : ~172
#   AUTRE : ~1150

# ============================================================
# 5. LECTURE / EXPORT / CARTO
# ============================================================
$apiKey = "dhr_dev_read_key_change_me"

# Liste des ouvrages
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/ouvrages

# Détail d'un ouvrage
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/ouvrages/1

# Export Excel
curl.exe -H "X-API-Key: $apiKey" -o export.xlsx http://localhost:8000/v1/ouvrages/export
Get-Item export.xlsx | Select-Object Name, Length

# Export CSV
curl.exe -H "X-API-Key: $apiKey" -o export.csv http://localhost:8000/v1/ouvrages/export.csv

# Carte « Tous »
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/carto/tous/points

# Carte « Fichier 1 »
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/carto/fichiers/1/points

# Exporter les points GeoJson
curl.exe -H "X-API-Key: $apiKey" -o fichier.geojson http://localhost:8000/v1/carto/fichiers/1/points.geojson
Get-Item fichier.geojson | Select-Object Name, Length

# Qualité
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/qualite/fichiers/1
```

---

## 5. Tableau récapitulatif

| Script                     | Rôle                           | Tables modifiées                                       | Pré-requis                         |
|----------------------------|--------------------------------|--------------------------------------------------------|------------------------------------|
| `inventaire_fichiers.py`   | Diagnostic (feuilles, entêtes) | ❌ Aucune                                               | —                                  |
| `test_ingestion.py`        | Diagnostic (mapping auto)      | ❌ Aucune                                               | —                                  |
| `import_localites.py`      | Import des localités           | `ref_geo_admin`, `localite`                            | —                                  |
| `test_ingestion_reelle.py` | Ingestion d'un fichier         | `fichier`, `feuille`, `ingestion_run`, `ligne_ingeree` | —                                  |
| `test_rapprochement.py`    | Rapprochement localités        | `ligne_ingeree.id_localite`, `statut_qualite`          | `localite` peuplée                 |
| `consolidation.py`         | Consolidation en ouvrages      | `ouvrage`, `ligne_ingeree.id_ouvrage_consolide`        | `ligne_ingeree.id_localite` rempli |

---

## 6. Différences avec le pipeline de production (Phase 4.4)

En Phase 4.4, on ajoutera :

| Script (test)              | Endpoint (production)                                                              |
|----------------------------|------------------------------------------------------------------------------------|
| `import_localites.py`      | `POST /v1/localites/import` (ou intégré à `POST /fichiers` si feuille `Localités`) |
| `test_ingestion_reelle.py` | `POST /v1/fichiers` (upload) + `POST /v1/fichiers/{id}/runs`                       |
| `test_rapprochement.py`    | `POST /v1/runs/{id}/rapprochement` (ou automatique après ingestion)                |
| `consolidation.py`         | `POST /v1/runs/{id}/consolidation` (ou automatique après rapprochement)            |

**Le pipeline automatique** (dans `POST /v1/fichiers/{id}/runs`) fera :
```bash
1. ingerer_fichier()          → ligne_ingeree
2. rapprocher_lignes_run()    → id_localite
3. consolider_lignes_run()    → ouvrage
```

**Les scripts CLI resteront** comme outils d'administration (relancer un rapprochement, reconsolider un run, etc.).

---

## 7. Erreurs fréquentes

| Symptôme                                | Cause                                     | Solution                                         |
|-----------------------------------------|-------------------------------------------|--------------------------------------------------|
| Rapprochement : `Non résolu = 100%`     | `localite` vide (pas d'import)            | Lancer `import_localites.py`                     |
| Consolidation : `Lignes traitées = 0`   | `id_localite` NULL (pas de rapprochement) | Lancer `test_rapprochement.py`                   |
| `type_localite` NULL                    | Mapping non validé                        | Utiliser `PUT /fichiers/{id}/mapping`            |
| `type_ouvrage` = AUTRE pour PMH/HVA/PEA | `type_ouvrage_brut` = Forage/Puits        | La consolidation utilise `nom_feuille` (corrigé) |
| `/carto/tous/points` vide               | `ouvrage` vide                            | Lancer `consolidation.py`                        |
| `/ouvrages` → `Internal Server Error`   | `geom` non chargé                         | Utiliser `ST_AsGeoJSON` (corrigé)                |

---

*Document rédigé le 2026-11-03. À mettre à jour à chaque nouveau script ou modification du pipeline.*


---

## Question

1. **Colle ce document dans `docs/SCRIPTS.md`**.
2. **Applique l'ordre correct** (section 4) et colle-moi les sorties de chaque étape.
3. **On enchaîne sur la Phase 4.4** (routers upload + runs qui automatisent le pipeline) ?

Ma reco : **oui**. Une fois que l'ordre correct fonctionne (import localités → ingestion → rapprochement → consolidation), on peut implémenter les endpoints qui font la même chose en une seule requête.