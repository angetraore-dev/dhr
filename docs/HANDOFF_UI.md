
---

# Handoff — Spécifications UI Carte (Phase 6.4)

## 1. Modes d'affichage (4 modes)

L'utilisateur peut basculer entre 4 modes via des boutons (comme actuellement « Tous » / « Par fichier ») :

1. **Tous les ouvrages** (`/carto/tous/points`)
    - Source : `ouvrage` (consolidé).
    - Affiche tous les ouvrages dédoublonnés.
    - Inclut les métadonnées de `ouvrage`, `localite` et `cgpe` (si disponible).

2. **Par fichier** (`/carto/fichiers/{id}/points`)
    - Source : `ligne_ingeree`.
    - Sélecteur : Fichier (obligatoire).
    - Affiche toutes les lignes du fichier.
    - Inclut `donnees_brutes` dans le popup.

3. **Par run** (`/carto/fichiers/{id}/points?id_run=...`)
    - Source : `ligne_ingeree`.
    - Sélecteurs : Fichier (obligatoire) + Run (obligatoire).
    - Affiche uniquement les lignes du run sélectionné.

4. **Par feuille** (`/carto/fichiers/{id}/points?id_feuille=...`)
    - Source : `ligne_ingeree`.
    - Sélecteurs : Fichier (obligatoire) + Feuille (obligatoire).
    - Affiche uniquement les lignes de la feuille sélectionnée.

## 2. Filtres (tous, combinables)

Une barre de filtres (accordéon ou panneau latéral) avec :

- **Type d'ouvrage** : PMH, HVA, PEA, HV, AUTRE (multi-sélection).
- **État** : fonctionnel, en_panne, abandonne, inconnu (multi-sélection).
- **Géographie** : District, Région, Département, Sous-préfecture (dropdowns dépendants).
- **Année** : min / max (inputs).
- **Bailleur** : UNICEF, BAD, etc. (dropdown).

*Note : Ces filtres s'appliquent au mode « Tous » et « Par fichier ». Les modes « run » et « feuille » ont déjà leur propre filtre natif.*

## 3. Gestion des Métadonnées (Popup)

Le backend doit renvoyer les métadonnées structurées par entité. L'UI les affichera dans le popup sous forme de **3 sections dépliables** :

```json
"properties": {
  "type_ouvrage": "PMH",
  "etat": "fonctionnel",
  ...
  "details": {
    "ouvrage": { "profondeur_forage_m": 45, "nom_prestataire": "Foraco" },
    "localite": { "population": 1200, "existence_ecole": true },
    "cgpe": { "nom_president": "M. Kouassi", "statut": "fonctionnel" }
  }
}
```

**UI du Popup** :
- Affichage des infos principales.
- `<details>` « Détails Ouvrage (N) » → affiche `details.ouvrage`.
- `<details>` « Détails Localité (N) » → affiche `details.localite`.
- `<details>` « Détails CGPE (N) » → affiche `details.cgpe`.
- (Pour le mode Fichier/Run/Feuille) : `<details>` « Données brutes (N) » → affiche `donnees_brutes`.

---

# Plan de production (Ordre des messages)

Pour éviter de tout casser d'un coup, on va procéder en 4 étapes :

### Étape 1 (Backend) — Carto v2
- Modification de `_ouvrage_to_feature` et `_ligne_to_feature` pour retourner `details.{ouvrage, localite, cgpe}`.
- Modification de `points_tous` pour joindre `cgpe` et `localite` (afin de récupérer leurs métadonnées).
- Ajout du filtre `bailleur` dans `points_tous`.
- Ajout du filtre `id_run` et `id_feuille` dans `points_fichier` (déjà là mais à valider).
- Modification de `_ligne_to_feature` pour inclure `donnees_brutes`.

### Étape 2 (Frontend) — Composants de Filtres
- Création de `FiltersPanel.tsx` (multi-sélection type, état, bailleur, année).
- Création de `GeoFilters.tsx` (dropdowns District → Région → Département → Sous-préfecture).
- Intégration dans la page `Carte.tsx`.

### Étape 3 (Frontend) — Modes et Sélecteurs
- Ajout des boutons Run et Feuille dans `Carte.tsx`.
- Ajout des sélecteurs conditionnels (si mode = run, afficher dropdown Run, etc.).

### Étape 4 (Frontend) — Popup v2
- Modification de `MapView.tsx` pour parser `details.*` et générer les sections `<details>`.

---
