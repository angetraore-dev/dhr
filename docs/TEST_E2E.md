
---

# Test de bout en bout — Projet DHR

**Date** : 2026-11-02
**Version** : 3.0
**Objectif** : Valider l'ensemble du pipeline (upload → mapping → ingestion → rapprochement → export → carto) sur les 3 fichiers DHR.

---

## 1. Pré-requis

```powershell
# Services démarrés
docker compose ps
# Attendu : db, backend, frontend healthy/running

# Base vierge (optionnel, pour repartir de zéro)
docker compose exec db psql -U dhr -d dhr -c "TRUNCATE ligne_ingeree, ingestion_run, feuille, fichier, mapping_feuille, localite, localite_alias, ref_geo_admin, ouvrage, cgpe, projet_financement, ouvrage_projet RESTART IDENTITY CASCADE;"

# Vérifier les 22 endpoints
docker compose exec backend python -c "from app.main import app; import json; print(len(app.openapi()['paths']))"
# Attendu : 22
```

---

## 2. Étape 1 — Upload d'un fichier

> **Note** : l'endpoint `POST /fichiers` n'est pas encore implémenté (Phase 4.3). On utilise le script `test_ingestion_reelle.py` qui crée le fichier + les feuilles + le run **directement en base**.

```powershell
docker compose exec backend python -u /app/scripts/test_ingestion_reelle.py /app/tests/fixtures/fichier1.xlsx 2>&1 | Select-Object -Last 10
```

**Attendu** :
```
[7] Ingestion terminée : total_lignes=3511, ...
[9] Total lignes en base : 3511
[10] Avec coordonnées : 3511 (100.0%)
```

Récupérer l'`id_fichier` :

```powershell
docker compose exec db psql -U dhr -d dhr -c "SELECT id_fichier, nom_fichier_original, statut FROM fichier ORDER BY id_fichier DESC LIMIT 3;"
```

---

## 3. Étape 2 — Proposition de mapping

```powershell
$apiKey = "dhr_dev_read_key_change_me"
$idFichier = 1   # ← remplacer par l'id réel
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/fichiers/$idFichier/mapping-proposal
```

**Attendu** : JSON avec les 5 feuilles (`Localités`, `PMH`, `HVA`, `PEA`, `Autres_ouvrages`), chacune avec `colonnes`.

**Vérifier** :
- Feuille `Localités` : `Localite_ou_Campement` → `type_localite_brut`
- Feuille `PMH` : `Q3.1.1g. Type d'ouvrage` → `type_ouvrage_brut`
- Feuille `PMH` : `Latitude` → `latitude_decimal`, `Longitude` → `longitude_decimal`

---

## 4. Étape 3 — Validation du mapping

Générer un JWT :

```powershell
$jwt = docker compose exec backend python -c "from app.auth import create_access_token; print(create_access_token('test', 'admin'))"
```

Récupérer l'`id_feuille` de `Localités` :

```powershell
docker compose exec db psql -U dhr -d dhr -c "SELECT id_feuille, nom_feuille FROM feuille WHERE id_fichier = $idFichier ORDER BY index_feuille;"
```

Valider le mapping pour `Localités` :

```powershell
$body = @"
{
    "colonnes": [
        { "entete_brut": "Localite_ou_Campement", "champ_cible": "type_localite_brut" },
        { "entete_brut": "Q1.2. Région", "champ_cible": "region_brute" },
        { "entete_brut": "Q1.3. Département", "champ_cible": "departement_brute" },
        { "entete_brut": "Q1.4. Commune/Sous-préfecture", "champ_cible": "sous_prefecture_brute" },
        { "entete_brut": "Q1.5. Localité/Campement", "champ_cible": "localite_brute" },
        { "entete_brut": "Q1.7. Taille de la population", "champ_cible": null },
        { "entete_brut": "Latitude", "champ_cible": "latitude_decimal" },
        { "entete_brut": "Longitude", "champ_cible": "longitude_decimal" }
    ]
}
"@

curl.exe -X PUT -H "Authorization: Bearer $jwt" -H "Content-Type: application/json" -d $body "http://localhost:8000/v1/fichiers/$idFichier/mapping?id_feuille=<id_feuille_localites>"
```

**Attendu** : mapping sauvegardé (200).

Vérifier en base :

```powershell
docker compose exec db psql -U dhr -d dhr -c "SELECT entete_brut, champ_cible FROM mapping_feuille WHERE id_feuille = <id_feuille_localites>;"
```

**Attendu** : les 8 entêtes avec les `champ_cible` correspondants.

---

## 5. Étape 4 — Import des localités

```powershell
docker compose exec backend python -u /app/scripts/import_localites.py /app/tests/fixtures/fichier1.xlsx 2>&1
```

**Attendu** :
```
Lignes traitées : 1132
Localités créées : ~1132
Erreurs : 0
```

Vérifier :

```powershell
docker compose exec db psql -U dhr -d dhr -c "SELECT COUNT(*) FROM localite;"
# Attendu : ~1132

docker compose exec db psql -U dhr -d dhr -c "SELECT type_localite, COUNT(*) FROM ref_geo_admin WHERE niveau = 'localite' GROUP BY type_localite;"
# Attendu : village ~700, campement ~400
```

---

## 6. Étape 5 — Rapprochement

> **Note** : `services/rapprochement.py` n'est pas encore implémenté. À faire dans le prochain message.

```powershell
# Récupérer id_run
docker compose exec db psql -U dhr -d dhr -c "SELECT id_run, id_fichier, statut FROM ingestion_run ORDER BY id_run DESC LIMIT 3;"

# Lancer le rapprochement (à venir)
# docker compose exec backend python /app/scripts/test_rapprochement.py <id_run>
```

**Attendu** (quand implémenté) :
```
Total lignes : 7045
Exact match : ~5000-6000
Alias : 0-100
Trigram : 500-1500
Non résolu : 200-800
```

---

## 7. Étape 6 — Export Excel

```powershell
$apiKey = "dhr_dev_read_key_change_me"
curl.exe -H "X-API-Key: $apiKey" -o export.xlsx http://localhost:8000/v1/ouvrages/export
Get-Item export.xlsx | Select-Object Name, Length
```

**Attendu** : `export.xlsx` ~7 Ko (avec feuille Synthèse).

Ouvrir dans Excel : 2 onglets (Synthèse + Ouvrages).

---

## 8. Étape 7 — Export CSV

```powershell
curl.exe -H "X-API-Key: $apiKey" -o export.csv http://localhost:8000/v1/ouvrages/export.csv
Get-Content export.csv -Encoding UTF8
```

**Attendu** : en-tête avec `N°;District;Région;...`.

---

## 9. Étape 8 — Carto

```powershell
# Points d'un fichier
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/carto/fichiers/$idFichier/points | Select-Object -First 500

# Tous les points
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/carto/tous/points

# Téléchargement GeoJSON
curl.exe -H "X-API-Key: $apiKey" -o fichier.geojson http://localhost:8000/v1/carto/fichiers/$idFichier/points.geojson
Get-Item fichier.geojson | Select-Object Name, Length
```

**Attendu** : `FeatureCollection` avec les points (lat/lon).

---

## 10. Étape 9 — Qualité

```powershell
curl.exe -H "X-API-Key: $apiKey" http://localhost:8000/v1/qualite/fichiers/$idFichier
```

**Attendu** :
```json
{
  "id_fichier": 1,
  "nom_fichier": "fichier1.xlsx",
  "source": "ONEP",
  "statut": "ingere",
  "nb_lignes_total": 3511,
  "qualite": { "ok": 3511, "geom_invalide": 0, ... },
  "taux_reussite": 1.0
}
```

---

## 11. Récapitulatif

| Étape | Endpoint / Script | Statut |
|---|---|---|
| Upload | `test_ingestion_reelle.py` | ✅ |
| Mapping proposal | `GET /mapping-proposal` | ✅ |
| Mapping validation | `PUT /mapping` | ✅ |
| Import localités | `import_localites.py` | ✅ |
| Rapprochement | `test_rapprochement.py` | ⏳ à implémenter |
| Export Excel | `GET /ouvrages/export` | ✅ |
| Export CSV | `GET /ouvrages/export.csv` | ✅ |
| Carto | `GET /carto/...` | ✅ |
| Qualité | `GET /qualite/fichiers/{id}` | ✅ |

---

## 12. Prochaines étapes

1. **Implémenter `services/rapprochement.py`** (Phase 4.2c) — débloquer le rapprochement.
2. **Implémenter `POST /fichiers`** (Phase 4.3) — upload réel.
3. **Implémenter `POST /fichiers/{id}/runs`** (Phase 4.3) — lancer l'ingestion via l'API.
4. **Phase 6 — Frontend** — UI de mapping, carte, liste, export.

---

## 3. Question

1. **Applique la correction de l'import circulaire** (section 1, étapes 1-3).
2. **Vérifie** (section 1, étape 4) et colle-moi la sortie.
3. **Crée `docs/TEST_E2E.md`** (section 2) — c'est le document de test.
4. **Lance les étapes 2 à 4** (upload, mapping-proposal, mapping) et colle-moi les sorties.

Dès que le mapping validé fonctionne, on implémente `services/rapprochement.py` (Phase 4.2c) pour débloquer le rapprochement, puis on complète le test E2E.