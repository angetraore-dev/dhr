
---

# Tests API DHR — Scénario bout-en-bout

**Version** : 1.0
**Date** : 2026-11-11
**Objet** : Tester le pipeline complet via l'API REST, de l'import des localités à l'export Excel/CSV.
**Prérequis** : API démarrée (`docker compose up -d`), base migrée (`alembic upgrade head`).

---

```text

# 1. L'ordre exact des étapes

- 1. Ingestion (ingerer_fichier) : Lit le fichier Excel, insère les 1306 lignes dans ligne_ingeree et met à jour run.nb_lignes_ingerees = 1306. À ce stade, elle ne touche pas au statut du fichier (qui reste en_attente).
- 2. Rapprochement (rapprocher_lignes_run) : Associe chaque ligne ingérée à une id_localite en base.
- 3. Consolidation (consolider_lignes_run) : Crée ou met à jour les ouvrage consolidés.
- 4. Clôture (executer_pipeline) : Passe run.statut à 'termine' et fichier.statut à 'ingere'.

```
## 0. Préparation

### 0.1 Variables d'environnement

**PowerShell (Windows)** :
```powershell
$BASE = "http://localhost:8000"
$API_KEY = (Get-Content .env | Select-String '^API_KEY_READ=').ToString().Split('=')[1]
$JWT = (docker compose exec -T backend python -c "from app.auth import create_access_token; print(create_access_token('test', 'admin'))").Trim()
$H_READ = @{ "X-API-Key" = $API_KEY }
$H_WRITE = @{ "X-API-Key" = $API_KEY; "Authorization" = "Bearer $JWT" }
Write-Host "API_KEY=$API_KEY"
Write-Host "JWT=$JWT"
```

**Bash (Linux/Mac)** :
```bash
export BASE="http://localhost:8000"
export API_KEY=$(grep '^API_KEY_READ=' .env | cut -d= -f2)
export JWT=$(docker compose exec -T backend python -c "from app.auth import create_access_token; print(create_access_token('test', 'admin'))" | tr -d '\r\n')
export H_READ=(-H "X-API-Key: $API_KEY")
export H_WRITE=(-H "X-API-Key: $API_KEY" -H "Authorization: Bearer $JWT")
echo "API_KEY=$API_KEY"
echo "JWT=$JWT"
```

### 0.2 Vérifier que l'API répond

**PowerShell** :
```powershell
curl.exe -s "$BASE/health" | ConvertFrom-Json | Format-List
```
**Bash** :
```bash
curl -s "$BASE/health" | jq .
```

**Attendu** : `{status: "ok", db: true, ...}`.

### 0.3 Vérifier les sources seedées

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/sources" | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/sources" | jq .
```

**Attendu** : 6 sources (`ONEP`, `SODECI`, `UNICEF`, `BAD`, `LONACI`, `ETAT_CI`).
**Noter** : `id_source` de `ONEP` (ex. 1).

---

## 1. Import des localités (script CLI, pas API)

> **Note** : l'import des localités est **hors API** au MVP (script CLI manuel, Bible § 1.4 décision 2). On le lance une fois.

### 1.1 Vérifier si le référentiel est déjà peuplé

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ref-geo?niveau=region&limit=5" | ConvertFrom-Json | Select-Object -ExpandProperty pagination
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ref-geo?niveau=region&limit=5" | jq '.pagination'
```

- **Si `total > 0`** : le référentiel est déjà peuplé → passer à l'étape 2.
- **Si `total = 0`** : lancer l'import (étape 1.2).

### 1.2 Lancer l'import (si nécessaire)

```bash
docker compose exec -T backend python -u /app/scripts/import_localites.py /app/tests/fixtures/fichier1.xlsx
```

**Attendu** : log avec `N localités importées`, `M nœuds ref_geo_admin créés`.

### 1.3 Vérifier les localités importées

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/localites?limit=5" | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/localites?limit=5" | jq .
```

**Attendu** : au moins 1 localité avec `id_localite` et `nom_usage`.
**Noter** : un `id_localite` existant (ex. 1) → servira pour vérifier le rapprochement.

### 1.4 Vérifier la hiérarchie d'une localité

**PowerShell** :
```powershell
$LOC_ID = 1   # remplacer par un id_localite réel
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/localites/$LOC_ID" | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
export LOC_ID=1   # remplacer
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/localites/$LOC_ID" | jq .
```

**Attendu** : `geom_centre` non NULL (si lat/lon fournis), `alias: []`.

### 1.5 Vérifier le chemin hiérarchique

**PowerShell** :
```powershell
# Récupérer id_geo de la localité
$LOC = curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/localites/$LOC_ID" | ConvertFrom-Json
# On n'a pas id_geo dans LocaliteSchema, il faut passer par ref-geo
# (optionnel : tester /ref-geo/{id}/chemin avec un id_geo connu)
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ref-geo/1/chemin" | jq '.[].nom'
```

**Attendu** : liste ordonnée `district → région → département → sous-préfecture → localité`.

---

## 2. Upload d'un fichier Excel

### 2.1 Uploader le fichier

**PowerShell** :
```powershell
$FICHIER = ".\backend\tests\fixtures\fichier1.xlsx"   # adapter le chemin
$ID_SOURCE = 1   # ONEP (adapter)
$resp = curl.exe -s -X POST "$BASE/v1/fichiers?force=true" `
  -H "Authorization: Bearer $JWT" `
  -F "file=@$FICHIER" `
  -F "id_source=$ID_SOURCE" `
  -F "commentaire=Test API bout-en-bout"
$resp | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
export FICHIER="./backend/tests/fixtures/fichier1.xlsx"
export ID_SOURCE=1
curl -s -X POST "$BASE/v1/fichiers?force=true" \
  -H "Authorization: Bearer $JWT" \
  -F "file=@$FICHIER" \
  -F "id_source=$ID_SOURCE" \
  -F "commentaire=Test API bout-en-bout" | jq .
```

**Attendu** :
```json
{
  "id_fichier": 1,
  "nom_fichier_original": "fichier1.xlsx",
  "nb_feuilles": N,
  "feuilles": [{"id_feuille": 1, "nom_feuille": "...", "index_feuille": 0}, ...]
}
```
**Noter** : `id_fichier` (ex. 1).

### 2.2 Vérifier le détail du fichier

**PowerShell** :
```powershell
$FICHIER_ID = 1   # remplacer
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/fichiers/$FICHIER_ID" | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
export FICHIER_ID=1
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/fichiers/$FICHIER_ID" | jq .
```

**Attendu** : `statut: "en_attente"`, `nb_feuilles: N`, `nb_lignes_total: 0`.

### 2.3 Lister les feuilles

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/fichiers/$FICHIER_ID/feuilles" | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/fichiers/$FICHIER_ID/feuilles" | jq '.data[] | {id_feuille, nom_feuille, statut_ingestion}'
```

**Attendu** : toutes les feuilles en `statut_ingestion: "en_attente"`.

### 2.4 Tester le 409 sans `force`

**PowerShell** :
```powershell
curl.exe -s -X POST "$BASE/v1/fichiers" `
  -H "Authorization: Bearer $JWT" `
  -F "file=@$FICHIER" `
  -F "id_source=$ID_SOURCE" | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
curl -s -X POST "$BASE/v1/fichiers" \
  -H "Authorization: Bearer $JWT" \
  -F "file=@$FICHIER" \
  -F "id_source=$ID_SOURCE" | jq .
```

**Attendu** (RFC 7807) :
```json
{
  "type": "https://api.dhr.local/errors/conflict",
  "title": "Conflict",
  "status": 409,
  "detail": "Un fichier avec le même hash existe déjà (id_fichier=1). Utilisez ?force=true pour réingérer.",
  "instance": "/v1/fichiers"
}
```

---

## 3. Mapping (proposition + validation)

### 3.1 Obtenir la proposition de mapping

**PowerShell** :
```powershell
$MAPPING = curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/fichiers/$FICHIER_ID/mapping-proposal" | ConvertFrom-Json
$MAPPING | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/fichiers/$FICHIER_ID/mapping-proposal" | jq .
```

**Attendu** : liste de feuilles avec `colonnes: [{entete_brut, champ_cible, confiance}, ...]`.
**Vérifier** : au moins un `champ_cible` non NULL (ex. `localite_brute`, `latitude_decimal`).

### 3.2 Valider le mapping (optionnel — le mapping auto suffit au MVP)

Si on veut forcer un champ cible (ex. mapper `Prof_Totale` vers `metadata.ouvrage.profondeur_forage_m`) :

**PowerShell** :
```powershell
$body = @{
  colonnes = @(
    @{ entete_brut = "Localité"; champ_cible = "localite_brute" },
    @{ entete_brut = "Latitude"; champ_cible = "latitude_decimal" },
    @{ entete_brut = "Longitude"; champ_cible = "longitude_decimal" },
    @{ entete_brut = "Prof_Totale"; champ_cible = "metadata.ouvrage.profondeur_forage_m" }
  )
} | ConvertTo-Json -Depth 5

curl.exe -s -X PUT "$BASE/v1/fichiers/$FICHIER_ID/mapping?id_feuille=1" `
  -H "Authorization: Bearer $JWT" `
  -H "Content-Type: application/json" `
  -d $body | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
curl -s -X PUT "$BASE/v1/fichiers/$FICHIER_ID/mapping?id_feuille=1" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"colonnes":[
    {"entete_brut":"Localité","champ_cible":"localite_brute"},
    {"entete_brut":"Latitude","champ_cible":"latitude_decimal"},
    {"entete_brut":"Longitude","champ_cible":"longitude_decimal"},
    {"entete_brut":"Prof_Totale","champ_cible":"metadata.ouvrage.profondeur_forage_m"}
  ]}' | jq .
```

**Attendu** : `200 OK` avec `{id_feuille, nom_feuille, header_row, colonnes: [...]}`.
**Si 400** : le `champ_cible` n'est pas reconnu (vérifier `COLUMN_PATTERNS`).

---

## 4. Ingestion (run complet)

### 4.1 Lancer le run

**PowerShell** :
```powershell
$resp = curl.exe -s -X POST "$BASE/v1/fichiers/$FICHIER_ID/runs?mode=complet" `
  -H "Authorization: Bearer $JWT"
$RUN = $resp | ConvertFrom-Json
$RUN | ConvertTo-Json -Depth 5
$RUN_ID = $RUN.id_run
```
**Bash** :
```bash
export RUN=$(curl -s -X POST "$BASE/v1/fichiers/$FICHIER_ID/runs?mode=complet" \
  -H "Authorization: Bearer $JWT")
export RUN_ID=$(echo "$RUN" | jq -r '.id_run')
echo "$RUN" | jq .
```

**Attendu** (202 Accepted) :
```json
{
  "id_run": 1,
  "id_fichier": 1,
  "statut": "en_cours",
  "started_at": "2026-11-11T...",
  "poll_url": "/v1/runs/1"
}
```
**Noter** : `id_run`.

### 4.2 Poller le run jusqu'à `termine`

**PowerShell** :
```powershell
do {
  Start-Sleep -Seconds 2
  $r = curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/runs/$RUN_ID" | ConvertFrom-Json
  Write-Host "statut=$($r.statut) lignes=$($r.nb_lignes_ingerees)"
} while ($r.statut -eq "en_cours")
$r | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
while true; do
  sleep 2
  R=$(curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/runs/$RUN_ID")
  STATUT=$(echo "$R" | jq -r '.statut')
  echo "statut=$STATUT lignes=$(echo "$R" | jq -r '.nb_lignes_ingerees')"
  [ "$STATUT" != "en_cours" ] && break
done
echo "$R" | jq .
```

**Attendu** : `statut: "termine"`, `nb_lignes_ingerees > 0`, `finished_at` non NULL.

### 4.3 Vérifier le statut du fichier

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/fichiers/$FICHIER_ID" | ConvertFrom-Json | Select-Object statut, nb_lignes_total
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/fichiers/$FICHIER_ID" | jq '{statut, nb_lignes_total}'
```

**Attendu** : `statut: "ingere"`, `nb_lignes_total > 0`.

### 4.4 Lister les lignes du run (cursor)

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/runs/$RUN_ID/lignes?limit=5" | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/runs/$RUN_ID/lignes?limit=5" | jq '.data[] | {id_ligne, localite_brute, statut_qualite, latitude_decimal, longitude_decimal}'
```

**Attendu** : lignes avec `statut_qualite` parmi `ok`, `geom_invalide`, `localite_non_resolue` (à ce stade, le rapprochement n'est pas encore lancé → `localite_non_resolue` ne devrait pas apparaître ; `id_localite` NULL).

### 4.5 Filtrer par statut qualité

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/runs/$RUN_ID/lignes?statut_qualite=geom_invalide&limit=5" | ConvertFrom-Json | Select-Object -ExpandProperty pagination
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/runs/$RUN_ID/lignes?statut_qualite=geom_invalide&limit=5" | jq '.pagination'
```

**Attendu** : `has_more`, `next_cursor` si > 5 lignes invalides.

### 4.6 Détail d'une ligne (avec `?include=brut`)

**PowerShell** :
```powershell
$LIGNE_ID = (curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/runs/$RUN_ID/lignes?limit=1" | ConvertFrom-Json).data[0].id_ligne
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/lignes/$LIGNE_ID?include=brut" | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
export LIGNE_ID=$(curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/runs/$RUN_ID/lignes?limit=1" | jq -r '.data[0].id_ligne')
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/lignes/$LIGNE_ID?include=brut" | jq .
```

**Attendu** : `donnees_brutes` non vide (JSONB complet de la ligne Excel), `usage_ouvrage_brut` présent.

---

## 5. Rapprochement

> **Note** : le rapprochement est **inclus dans le pipeline** `POST /fichiers/{id}/runs`. Il n'y a pas d'endpoint API dédié. Pour le rejouer manuellement, utiliser le script CLI (`scripts/test_rapprochement.py`).

### 5.1 Vérifier le rapprochement via les lignes

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/runs/$RUN_ID/lignes?limit=10" | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/runs/$RUN_ID/lignes?limit=10" | jq '.data[] | {id_ligne, localite_brute, statut_qualite}'
```

**Attendu** : certaines lignes `statut_qualite: "ok"` (localité résolue), d'autres `"localite_non_resolue"` (si le référentiel ne couvre pas toutes les localités).

### 5.2 Compter les statuts

**PowerShell** :
```powershell
$stats = @{}
foreach ($s in @("ok","localite_non_resolue","geom_invalide","type_ouvrage_inconnu","doublon_suspect")) {
  $stats[$s] = (curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/runs/$RUN_ID/lignes?statut_qualite=$s&limit=1" | ConvertFrom-Json).pagination.has_more
}
$stats | ConvertTo-Json
```
**Bash** :
```bash
for s in ok localite_non_resolue geom_invalide type_ouvrage_inconnu doublon_suspect; do
  echo -n "$s: "
  curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/runs/$RUN_ID/lignes?statut_qualite=$s&limit=1" | jq '.pagination.has_more'
done
```

**Attendu** : au moins `ok` à `true` (des lignes valides existent).

### 5.3 Tester le format strict de `message_qualite`

**PowerShell** :
```powershell
$lignes = curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/runs/$RUN_ID/lignes?statut_qualite=localite_non_resolue&limit=1" | ConvertFrom-Json
if ($lignes.pagination.total -gt 0) {
  $lignes.data[0].message_qualite   # attendu : "Localité non résolue : <localite_brute>"
}
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/runs/$RUN_ID/lignes?statut_qualite=localite_non_resolue&limit=1" | jq -r '.data[0].message_qualite // "aucune ligne non résolue"'
```

**Attendu** : `"Localité non résolue : <nom>"` (sans suffixe debug, conforme I3).

---

## 6. Consolidation

> **Note** : la consolidation est **incluse dans le pipeline**. Elle crée les `ouvrage`. On la vérifie via les endpoints `/ouvrages` et `/carto/tous/points`.

### 6.1 Vérifier que des ouvrages ont été créés

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages?limit=5" | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages?limit=5" | jq '{pagination, data: [.data[] | {id_ouvrage, nature_ouvrage, type_alimentation, realisation_par, etat, localite}]}'
```

**Attendu** : `pagination.total > 0`, ouvrages avec les 3 champs sémantiques (`nature_ouvrage`, `type_alimentation`, `realisation_par`).

### 6.2 Détail d'un ouvrage

**PowerShell** :
```powershell
$OUV_ID = (curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages?limit=1" | ConvertFrom-Json).data[0].id_ouvrage
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/$OUV_ID?include=metadata" | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
export OUV_ID=$(curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages?limit=1" | jq -r '.data[0].id_ouvrage')
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/$OUV_ID?include=metadata" | jq .
```

**Attendu** :
- `metadata` non NULL (si des colonnes non mappées existent).
- `qualite_eau` non NULL (si des colonnes sanitaires existent).
- `geom` non NULL.
- **Pas de `type_ouvrage`** (supprimé).

### 6.3 Filtrer par attribut métier

**PowerShell** :
```powershell
foreach ($f in @("nature_ouvrage=forage","type_alimentation=PMH","realisation_par=public","etat=fonctionnel")) {
  $r = curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages?$f&limit=1" | ConvertFrom-Json
  Write-Host "$f -> total=$($r.pagination.total)"
}
```
**Bash** :
```bash
for f in "nature_ouvrage=forage" "type_alimentation=PMH" "realisation_par=public" "etat=fonctionnel"; do
  echo -n "$f -> "
  curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages?$f&limit=1" | jq '.pagination.total'
done
```

**Attendu** : chaque filtre retourne un total (éventuellement 0).

### 6.4 Tester le 422 sur filtre invalide

> **⚠️ Après B9** : `type_alimentation` sera typé `Literal`, donc `?type_alimentation=XXX` → 422. **Avant B9** : retourne 0 résultat (pas d'erreur).

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages?type_alimentation=XXX" | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages?type_alimentation=XXX" | jq .
```

**Attendu (après B9)** :
```json
{
  "type": "https://api.dhr.local/errors/validation",
  "title": "Validation Error",
  "status": 422,
  "detail": "...",
  "instance": "/v1/ouvrages",
  "errors": [{"field": "type_alimentation", "message": "..."}]
}
```
**Attendu (avant B9)** : `200` avec `pagination.total: 0`.

### 6.5 Vérifier le dédoublonnage

**PowerShell** :
```powershell
# Compter les ouvrages avec le même code
$all = curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages?limit=1000" | ConvertFrom-Json
$all.data | Where-Object { $_.code_ouvrage } | Group-Object code_ouvrage | Where-Object { $_.Count -gt 1 }
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages?limit=1000" | jq -r '.data[] | select(.code_ouvrage != null) | .code_ouvrage' | sort | uniq -d
```

**Attendu** : aucun doublon (ou doublons documentés `doublon_suspect`).

### 6.6 Tester la pagination cursor

**PowerShell** :
```powershell
$p1 = curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages?limit=2" | ConvertFrom-Json
Write-Host "page1: $($p1.data.Count) items, has_more=$($p1.pagination.has_more)"
if ($p1.pagination.has_more) {
  $p2 = curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages?limit=2&cursor=$($p1.pagination.next_cursor)" | ConvertFrom-Json
  Write-Host "page2: $($p2.data.Count) items"
  Write-Host "ids page1: $($p1.data.id_ouvrage -join ',')"
  Write-Host "ids page2: $($p2.data.id_ouvrage -join ',')"
}
```
**Bash** :
```bash
P1=$(curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages?limit=2")
echo "page1: $(echo "$P1" | jq '.data | length') items, has_more=$(echo "$P1" | jq -r '.pagination.has_more')"
NEXT=$(echo "$P1" | jq -r '.pagination.next_cursor // empty')
if [ -n "$NEXT" ]; then
  P2=$(curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages?limit=2&cursor=$NEXT")
  echo "page2: $(echo "$P2" | jq '.data | length') items"
  echo "ids page1: $(echo "$P1" | jq -r '[.data[].id_ouvrage] | join(",")')"
  echo "ids page2: $(echo "$P2" | jq -r '[.data[].id_ouvrage] | join(",")')"
fi
```

**Attendu** : pas de chevauchement entre page1 et page2.

---

## 7. Cartographie

### 7.1 Mode Tous (ouvrages consolidés)

**PowerShell** :
```powershell
$geojson = curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/carto/tous/points" | ConvertFrom-Json
Write-Host "count: $($geojson.meta.count)"
$geojson.features[0] | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/carto/tous/points" | jq '{count: .meta.count, first: .features[0]}'
```

**Attendu** :
- `meta.count > 0`.
- `features[0].geometry.coordinates` en `[lon, lat]`.
- `features[0].properties` contient `nature_ouvrage`, `type_alimentation`, `realisation_par`, `etat`, `qualite_eau`, `details.qualite_eau`.
- **Pas de `district`** dans les `properties` (Bible § 1.4 décision 6).

### 7.2 Mode Fichier (points bruts)

**PowerShell** :
```powershell
$geojson = curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/carto/fichiers/$FICHIER_ID/points" | ConvertFrom-Json
Write-Host "count: $($geojson.meta.count)"
$geojson.features[0] | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/carto/fichiers/$FICHIER_ID/points" | jq '{count: .meta.count, first: .features[0]}'
```

**Attendu** :
- `meta.count > 0`.
- `features[0].properties` contient `type_ouvrage_brut`, `etat_ouvrage_brut` (brut, pas métier).
- **Aucune feature** avec `nom_feuille` contenant `"localité"`, `"village"` ou `"campement"` (A1).

**Vérification explicite** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/carto/fichiers/$FICHIER_ID/points" | \
  jq '[.features[] | select(.properties.nom_feuille | test("ocalit|village|campement"; "i"))] | length'
```
**Attendu** : `0`.

### 7.3 Filtre `type_alimentation` en mode Fichier

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/carto/fichiers/$FICHIER_ID/points?type_alimentation=PMH" | ConvertFrom-Json | Select-Object -ExpandProperty meta
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/carto/fichiers/$FICHIER_ID/points?type_alimentation=PMH" | jq '.meta'
```

**Attendu** : count ≤ count global (filtre sur `nom_feuille`).

### 7.4 Téléchargement GeoJSON

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/carto/fichiers/$FICHIER_ID/points.geojson" -o "points_$FICHIER_ID.geojson"
Get-Content "points_$FICHIER_ID.geojson" | ConvertFrom-Json | Select-Object type, @{n='count';e={$_.features.Count}}
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/carto/fichiers/$FICHIER_ID/points.geojson" -o "points_$FICHIER_ID.geojson"
jq '{type, count: (.features | length)}' "points_$FICHIER_ID.geojson"
```

**Attendu** : `{type: "FeatureCollection", count: N}`, fichier valide.

---

## 8. Qualité

### 8.1 Tableau de bord qualité du fichier

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/qualite/fichiers/$FICHIER_ID" | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/qualite/fichiers/$FICHIER_ID" | jq .
```

**Attendu** :
```json
{
  "id_fichier": 1,
  "nom_fichier": "fichier1.xlsx",
  "source": "ONEP",
  "statut": "ingere",
  "nb_lignes_total": N,
  "qualite": {
    "ok": A,
    "localite_non_resolue": B,
    "geom_invalide": C,
    "type_ouvrage_inconnu": D,
    "rejete": E,
    "doublon_suspect": F
  },
  "taux_reussite": A/N
}
```

**Vérification de cohérence** (Bible § 2.2.D) :
```
A + B + C + D + E + F == N
```
**PowerShell** :
```powershell
$q = curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/qualite/fichiers/$FICHIER_ID" | ConvertFrom-Json
$sum = $q.qualite.ok + $q.qualite.localite_non_resolue + $q.qualite.geom_invalide + $q.qualite.type_ouvrage_inconnu + $q.qualite.rejete + $q.qualite.doublon_suspect
Write-Host "somme=$sum / total=$($q.nb_lignes_total) -> $(if ($sum -eq $q.nb_lignes_total) {'OK'} else {'ÉCHEC'})"
```
**Bash** :
```bash
Q=$(curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/qualite/fichiers/$FICHIER_ID")
SUM=$(echo "$Q" | jq '.qualite | .ok + .localite_non_resolue + .geom_invalide + .type_ouvrage_inconnu + .rejete + .doublon_suspect')
TOTAL=$(echo "$Q" | jq '.nb_lignes_total')
echo "somme=$SUM / total=$TOTAL -> $([ "$SUM" -eq "$TOTAL" ] && echo OK || echo ÉCHEC)"
```

**Attendu** : `OK`.

### 8.2 Vérifier `rejete` par différence

**Bash** :
```bash
# nb_rejetes = nb_lignes_total - COUNT(ligne_ingeree)
# On ne peut pas le vérifier via l'API (pas d'endpoint COUNT), mais le dashboard doit être cohérent.
echo "rejete=$($Q | jq '.qualite.rejete')"
```

**Attendu** : `rejete ≥ 0` (peut être 0 si aucune ligne de total).

---

## 9. Export Excel

### 9.1 Export avec filtres par défaut

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/export" -o "export_ouvrages.xlsx"
# Vérifier la taille
(Get-Item "export_ouvrages.xlsx").Length
# Ouvrir avec Excel (optionnel)
Start-Process "export_ouvrages.xlsx"
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/export" -o "export_ouvrages.xlsx"
ls -lh export_ouvrages.xlsx
file export_ouvrages.xlsx   # attendu : "Microsoft Excel 2007+"
```

**Attendu** :
- Fichier `.xlsx` valide (taille > 5 Ko).
- **Feuille Synthèse** incluse par défaut (KPI : total, par nature, par alimentation, par réalisation, par état, **par district** — Bible § 1.4 décision 6).
- **Feuille Ouvrages** avec toutes les colonnes (code, nature, alimentation, réalisation, état, localité, sous-préfecture, département, région, année, lat, lon).

### 9.2 Export avec `?include=metadata`

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/export?include=metadata" -o "export_metadata.xlsx"
(Get-Item "export_metadata.xlsx").Length
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/export?include=metadata" -o "export_metadata.xlsx"
ls -lh export_metadata.xlsx
```

**Attendu** : fichier plus gros que 9.1 (colonne `metadata` ajoutée).

### 9.3 Export avec `?with_summary=false`

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/export?with_summary=false" -o "export_no_summary.xlsx"
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/export?with_summary=false" -o "export_no_summary.xlsx"
```

**Attendu** : fichier avec **une seule feuille** (Ouvrages), pas de Synthèse.

### 9.4 Export avec filtres métier

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/export?nature_ouvrage=forage&etat=fonctionnel" -o "export_forage_fonctionnel.xlsx"
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/export?nature_ouvrage=forage&etat=fonctionnel" -o "export_forage_fonctionnel.xlsx"
```

**Attendu** : fichier avec uniquement les forages fonctionnels (vérifier le nombre de lignes dans Excel).

### 9.5 Vérifier le KPI `par_district` dans la Synthèse

**Ouvrir `export_ouvrages.xlsx`** avec Excel/LibreOffice, feuille **Synthèse**.
**Attendu** : section `Par district` (agrégation en lecture seule, **pas un filtre** — Bible § 1.4 décision 6).

### 9.6 Export avec 0 résultat

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/export?nature_ouvrage=inconnu&etat=abandonne&annee_min=1900&annee_max=1901" -o "export_vide.xlsx"
(Get-Item "export_vide.xlsx").Length
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/export?nature_ouvrage=inconnu&etat=abandonne&annee_min=1900&annee_max=1901" -o "export_vide.xlsx"
ls -lh export_vide.xlsx
```

**Attendu** : fichier valide avec en-têtes mais 0 ligne de données (pas d'erreur 500).

---

## 10. Export CSV

### 10.1 Export CSV par défaut

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/export.csv" -o "export_ouvrages.csv"
# Vérifier l'encodage UTF-8 et le séparateur ';'
Get-Content "export_ouvrages.csv" -TotalCount 3
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/export.csv" -o "export_ouvrages.csv"
head -3 export_ouvrages.csv
file export_ouvrages.csv   # attendu : "UTF-8 Unicode text"
```

**Attendu** :
- Séparateur `;` (Bible § 4.3.4).
- Encodage UTF-8.
- En-tête avec les colonnes (code, nature, alimentation, etc.).
- **Pas de BOM** (ou BOM UTF-8, à vérifier — la Bible ne tranche pas).

### 10.2 Export CSV avec `?include=metadata`

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/export.csv?include=metadata" -o "export_metadata.csv"
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/export.csv?include=metadata" -o "export_metadata.csv"
head -1 export_metadata.csv | tr ';' '\n' | grep metadata
```

**Attendu** : colonne `metadata` présente.

### 10.3 Export CSV avec filtres

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/export.csv?type_alimentation=PMH&region=Marahoué" -o "export_pmh_marahoue.csv"
(Get-Content "export_pmh_marahoue.csv").Count
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ouvrages/export.csv?type_alimentation=PMH&region=Marahoué" -o "export_pmh_marahoue.csv"
wc -l export_pmh_marahoue.csv
```

**Attendu** : nombre de lignes cohérent.

---

## 11. Tests d'erreur (RFC 7807)

### 11.1 401 sans API key

**PowerShell** :
```powershell
curl.exe -s "$BASE/v1/sources" | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
curl -s "$BASE/v1/sources" | jq .
```

**Attendu** : `{type: ".../unauthorized", title: "Unauthorized", status: 401, ...}`.

### 11.2 403 avec JWT `role=ingesteur` sur endpoint admin

> **Note** : au MVP, `PUT /fichiers/{id}/mapping` n'est pas protégé par `role=admin` (Bible § 4.2 dit V2). Ce test est **à ignorer** au MVP.

### 11.3 404 sur ressource inexistante

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/fichiers/99999" | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/fichiers/99999" | jq .
```

**Attendu** : `{type: ".../not-found", status: 404, detail: "Fichier 99999 introuvable"}`.

### 11.4 422 sur paramètre invalide

**PowerShell** :
```powershell
curl.exe -s -H "X-API-Key: $API_KEY" "$BASE/v1/ref-geo?niveau=invalide" | ConvertFrom-Json | ConvertTo-Json -Depth 5
```
**Bash** :
```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE/v1/ref-geo?niveau=invalide" | jq .
```

**Attendu** : `{type: ".../validation", status: 422, errors: [{field: "niveau", ...}]}`.

### 11.5 413 sur export trop volumineux

> **Note** : `MAX_EXPORT_ROWS` n'est pas implémenté au MVP (Bible § 4.4 le prévoit). **Test à ignorer** tant que l'export ne plafonne pas.

---

## 12. Récapitulatif

| # | Test | Statut |
|---|------|--------|
| 0 | Préparation | ⏳ |
| 1 | Import localités | ⏳ |
| 2 | Upload fichier | ⏳ |
| 3 | Mapping | ⏳ |
| 4 | Ingestion | ⏳ |
| 5 | Rapprochement | ⏳ |
| 6 | Consolidation | ⏳ |
| 7 | Cartographie | ⏳ |
| 8 | Qualité | ⏳ |
| 9 | Export Excel | ⏳ |
| 10 | Export CSV | ⏳ |
| 11 | Erreurs RFC 7807 | ⏳ |

**Cocher au fur et à mesure.**

---

## Annexe A — Reset complet

Pour repartir de zéro :

```bash
# 1. Reset DB
docker compose exec -T db psql -U dhr -d dhr -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose exec -T backend alembic upgrade head

# 2. Supprimer les fichiers uploadés
docker compose exec -T backend rm -rf /app/uploads/*

# 3. Réimporter les localités
docker compose exec -T backend python -u /app/scripts/import_localites.py /app/tests/fixtures/fichier1.xlsx
```

---

## Annexe B — Vérifications SQL (optionnelles)

### B.1 Vérifier la cohérence `nb_lignes_total`

```sql
SELECT f.id_fichier, f.nb_lignes_total, COUNT(li.id_ligne) AS stockees
FROM fichier f
LEFT JOIN feuille fe ON fe.id_fichier = f.id_fichier
LEFT JOIN ligne_ingeree li ON li.id_feuille = fe.id_feuille
GROUP BY f.id_fichier, f.nb_lignes_total
HAVING f.nb_lignes_total < COUNT(li.id_ligne);
-- Attendu : 0 ligne
```

### B.2 Vérifier R5 (ouvrage → geom NOT NULL)

```sql
SELECT id_ouvrage FROM ouvrage WHERE geom IS NULL;
-- Attendu : 0 ligne
```

### B.3 Vérifier R8 (`qualite_eau != '{}'`)

```sql
SELECT id_ouvrage FROM ouvrage WHERE qualite_eau = '{}'::jsonb;
-- Attendu : 0 ligne
```

### B.4 Vérifier R10 (pas de doublon tuple)

```sql
SELECT id_localite, nature_ouvrage, type_alimentation, annee_realisation, COUNT(*)
FROM ouvrage
GROUP BY 1,2,3,4
HAVING COUNT(*) > 1;
-- Attendu : 0 ligne
```