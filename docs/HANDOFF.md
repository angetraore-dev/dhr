
---

## Handoff Complet — Projet DHR (v5.0)

# Handoff — Projet DHR (v5.0)

**Date** : 2026-11-04
**Version** : 5.0 (Phase 1 à 5 terminées, Phase 6 en cours)
**Objet** : Centralisation des ouvrages hydrauliques ruraux pour la Direction de l'Hydraulique Rurale (DHR)
**Repo** : `C:\Users\hp\PhpstormProjects\dhr`

---

## 1. Contexte métier

La DHR reçoit des fichiers Excel hétérogènes (ONEP, SODECI, UNICEF, BAD, LONACI, État) contenant des données sur les ouvrages hydrauliques ruraux, les CGPE et les financements. Elle veut centraliser ces données dans une base PostgreSQL/PostGIS et disposer d'une UI cartographique (vue satellite) et d'un export Excel/CSV.

**MVP** : lecture + ingestion + carto + export. L'écriture manuelle et l'analytique avancée sont hors scope.

**Décisions clés** :
- Un ouvrage sans coordonnées GPS n'existe pas (marqué `geom_invalide`, non consolidé).
- L'import des localités se fait manuellement (`import_localites.py`) pour enrichir le référentiel.
- Pas de filtre "district" (obsolète suite à la réforme territoriale, sauf Abidjan/Yamoussoukro).
- Le mapping des colonnes est proposé automatiquement, mais l'utilisateur peut le corriger via l'UI.

---

## 2. État d'avancement (Phases)

### ✅ Terminé
| Phase                             | Contenu                                                               | Statut |
|-----------------------------------|-----------------------------------------------------------------------|--------|
| **Conception**                    | MCDR, MLDR, UML, `schema.sql`, `openapi.yaml`, conventions metadata   | ✅      |
| **Phase 1 — Infrastructure**      | Docker Compose, config, db, entrypoint                                | ✅      |
| **Phase 2 — Modèles + migration** | 14 tables SQLAlchemy (dont `mapping_feuille`), migrations Alembic     | ✅      |
| **Phase 3 — API lecture**         | Endpoints référentiels, fichiers, ouvrages, CGPE, carto, qualité      | ✅      |
| **Phase 4 — Ingestion**           | Pipeline complet : upload → ingestion → rapprochement → consolidation | ✅      |
| **Phase 5 — Export**              | Excel XlsxWriter + Synthèse KPI + CSV, colonne N°, limite 413         | ✅      |
| **Phase 6.1 — Squelette Front**   | React + Vite + TS + Tailwind + shadcn/ui, layout sidebar/header       | ✅      |
| **Phase 6.2 — Page Fichiers**     | Liste, dialog upload, lancement run, polling statut                   | ✅      |
| **Phase 6.4 — Page Carte**        | Leaflet + Esri, filtres cascade, popups métadonnées `<details>`       | ✅      |

### 🔄 En cours / À faire (Phase 6)
| Phase                        | Contenu                                                 | Statut |
|------------------------------|---------------------------------------------------------|--------|
| **Phase 6.3 — Page Mapping** | UI de mapping (proposal + validation) par feuille       | ⏳      |
| **Phase 6.5 — Page Liste**   | Tableau paginé + filtres + boutons export Excel/CSV     | ⏳      |
| **Phase 6.6 — Page Qualité** | Tableau de bord par fichier                             | ⏳      |
| **Phase 7 — Tests**          | Tests d'API (pytest), tests d'ingestion, tests d'export | ⏳      |

---

## 3. Architecture

### 3.1 Stack Technique
| Couche          | Technologie                  | Version      |
|-----------------|------------------------------|--------------|
| Base de données | PostgreSQL + PostGIS         | 16 + 3.4     |
| Back-end        | Python + FastAPI             | 3.12 + 0.115 |
| ORM             | SQLAlchemy + GeoAlchemy2     | 2.0 + 0.16   |
| Validation      | Pydantic                     | 2.9          |
| Migrations      | Alembic                      | 1.13         |
| Parsing Excel   | openpyxl                     | 3.1          |
| Export Excel    | XlsxWriter                   | 3.2          |
| Auth            | python-jose (JWT) + API key  | —            |
| Front-end       | React + Vite + TypeScript    | 18 + 5.4     |
| UI              | Tailwind + shadcn/ui         | 3.4          |
| Carto           | Leaflet + Esri World Imagery | 1.9          |
| État API        | TanStack Query               | 5.59         |
| Conteneurs      | Docker Compose               | —            |

### 3.2 Modèle de Données (14 tables)
**Référentiels** : `source`, `type_ouvrage`, `ref_geo_admin` (hiérarchique), `localite`, `localite_alias`
**Ingestion** : `fichier`, `feuille`, `mapping_feuille`, `ingestion_run`, `ligne_ingeree`
**Métier** : `ouvrage`, `cgpe`, `projet_financement`, `ouvrage_projet`

*Note : `localite`, `ouvrage` et `cgpe` possèdent chacun un champ `metadata` (JSONB) pour les attributs non mappés.*

### 3.3 Le Pipeline d'Ingestion
1. **Import localités** (manuel, une fois) : `import_localites.py` → `ref_geo_admin` + `localite`.
2. **Upload** (`POST /v1/fichiers`) : Crée `fichier` + `feuille`.
3. **Run** (`POST /v1/fichiers/{id}/runs`) : Pipeline asynchrone en 3 étapes :
   - `ingerer_fichier()` → `ligne_ingeree` (statut `ok` ou `geom_invalide`).
   - `rapprocher_lignes_run()` → résout `localite_brute` → `id_localite`.
   - `consolider_lignes_run()` → crée les `ouvrage` (ignore les localités et les `geom_invalide`).

---

## 4. Contrat d'API (28 endpoints)

Base : `http://localhost:8000/v1`

| Méthode | Endpoint                                                                                          | Auth    | Statut |
|---------|---------------------------------------------------------------------------------------------------|---------|--------|
| GET     | `/sources`, `/types-ouvrage`, `/ref-geo`, `/ref-geo/{id}/chemin`, `/localites`, `/localites/{id}` | API key | ✅      |
| GET     | `/fichiers`, `/fichiers/{id}`, `/fichiers/{id}/feuilles`                                          | API key | ✅      |
| POST    | `/fichiers` (upload)                                                                              | JWT     | ✅      |
| GET     | `/fichiers/{id}/mapping-proposal`                                                                 | API key | ✅      |
| PUT     | `/fichiers/{id}/mapping`                                                                          | JWT     | ✅      |
| POST    | `/fichiers/{id}/runs`                                                                             | JWT     | ✅      |
| GET     | `/fichiers/{id}/runs`, `/runs/{id}`                                                               | API key | ✅      |
| GET     | `/runs/{id}/lignes`, `/feuilles/{id}/lignes`, `/lignes/{id}`                                      | API key | ✅      |
| GET     | `/ouvrages`, `/ouvrages/{id}`, `/cgpe/{id}`                                                       | API key | ✅      |
| GET     | `/ouvrages/export`, `/ouvrages/export.csv`                                                        | API key | ✅      |
| GET     | `/carto/fichiers/{id}/points`, `/carto/tous/points`, `/carto/fichiers/{id}/points.geojson`        | API key | ✅      |
| GET     | `/qualite/fichiers/{id}`                                                                          | API key | ✅      |

---

## 5. Frontend (React)

### 5.1 Composants UI
- `Button`, `Input`, `Dialog`, `Badge` (basés sur Tailwind).
- `FiltersPanel` : gère la cascade Région > Département > Sous-préfecture + Type + État + Localité + Année.
- `MapView` : Leaflet, Esri World Imagery (`maxNativeZoom: 16`), `circleMarker` colorés par type, popup avec `<details>` pour les métadonnées.
- `UploadDialog` : sélection de fichier, source, commentaire.
- `RunStatus` : polling toutes les 2s pour afficher l'avancement.

### 5.2 Pages
- `Fichiers` : tableau avec statut, bouton Upload, bouton Run, bouton Mapping.
- `Carte` : filtre par mode (Tous / Par fichier), panneau de filtres, carte interactive.
- `Mapping` (⏳ à faire) : correction des colonnes proposées.
- `Liste` (⏳ à faire) : tableau paginé + export.
- `Qualité` (⏳ à faire) : tableau de bord.
- `Parametres` : champ pour coller le JWT (généré via script).

---

## 6. Démarrage & Commandes Utiles

```powershell
# Démarrer
docker compose up -d --build
docker compose exec backend alembic upgrade head

# Reset DB (⚠️ perte de données)
docker compose exec db psql -U dhr -d dhr -c "TRUNCATE ligne_ingeree, ingestion_run, feuille, fichier, mapping_feuille, localite, localite_alias, ref_geo_admin, ouvrage, cgpe, projet_financement, ouvrage_projet RESTART IDENTITY CASCADE;"

# Importer les localités (1ère fois)
docker compose exec backend python -u /app/scripts/import_localites.py /app/tests/fixtures/fichier1.xlsx

# Générer un JWT pour l'UI
docker compose exec backend python -c "from app.auth import create_access_token; print(create_access_token('test', 'admin'))"
```

---

## 7. TODO Détaillé (Prochaines étapes)

### Phase 6.3 — Page Mapping (⏳ URGENT)
- [ ] Créer `frontend/src/pages/Mapping.tsx`.
- [ ] Afficher le mapping proposé (`GET /fichiers/{id}/mapping-proposal`).
- [ ] Permettre de modifier le `champ_cible` via un dropdown.
- [ ] Sauvegarder le mapping (`PUT /fichiers/{id}/mapping`).
- [ ] **Évolution Backend** : Ajouter la gestion des `metadata` dans le mapping (distinguer `metadata.ouvrage.*`, `metadata.localite.*`, `metadata.cgpe.*`).

### Phase 6.5 — Page Liste
- [ ] Créer `frontend/src/pages/Liste.tsx`.
- [ ] Intégrer `FiltersPanel` (déjà existant).
- [ ] Tableau paginé (TanStack Table).
- [ ] Boutons "Exporter Excel" et "Exporter CSV".

### Phase 6.6 — Page Qualité
- [ ] Créer `frontend/src/pages/Qualite.tsx`.
- [ ] Afficher les stats `GET /qualite/fichiers/{id}`.
- [ ] Graphiques (recharts ou simple barre CSS).

### Phase 7 — Tests & Finitions
- [ ] Tests unitaires API (pytest).
- [ ] Tests d'intégration (upload → run → export).
- [ ] Build de production (`npm run build`).
- [ ] Dockerfile frontend pour la prod (Nginx).
- [ ] Documentation finale.

---

## 8. Dette Technique / Points Ouverts

| # | Point                           | Impact                     | À traiter                       |
|---|---------------------------------|----------------------------|---------------------------------|
| 1 | Filtre bailleur                 | Backend OK, pas de données | Attendre des financements réels |
| 2 | Import auto des localités       | Manuel                     | V2 (UI de mapping localité)     |
| 3 | Attributs `metadata` dynamiques | Mapping UI non géré        | Phase 6.3                       |
| 4 | Création manuelle de localités  | Non géré                   | V2                              |
| 5 | `Localite.geom_centre`          | Non sérialisé              | V2                              |
| 6 | DMS corrompu                    | 1 ligne `geom_invalide`    | Normal                          |
| 7 | Déploiement prod                | Non fait                   | V2                              |
| 8 | Gestion utilisateurs (table)    | Config MVP (JWT manuel)    | V2                              |

---

*Handoff mis à jour le 2026-11-04. Toute modification de l'API ou du schéma doit être répercutée dans les livrables de conception.*
