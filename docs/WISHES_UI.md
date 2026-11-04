
---

## 1. Les modes d'affichage cartographique

Pour bien se comprendre, voici les axes d'affichage possibles :

### Axe 1 — Source de données
| Mode | Source | Contenu | Métadonnées |
|---|---|---|---|
| **1. Tous les ouvrages** | `ouvrage` (consolidé) | Ouvrages dédoublonnés (PMH, HVA, PEA…) | ✅ `ouvrage.metadata` |
| **2. Par fichier** | `ligne_ingeree` (brut) | Toutes les lignes ingérées d'un fichier | ❌ (actuellement) → à ajouter `ligne_ingeree.donnees_brutes` |
| **3. Par run** | `ligne_ingeree` filtré par `id_run` | Lignes d'un run spécifique | ❌ → à ajouter |
| **4. Par feuille** | `ligne_ingeree` filtré par `id_feuille` | Lignes d'une feuille (PMH, HVA, PEA…) | ❌ → à ajouter |

### Axe 2 — Filtres géographiques (pour le mode « Tous »)
| Mode | Source | Filtre |
|---|---|---|
| **5. Par district** | `ouvrage` | `ref_geo_admin.niveau = 'district'` |
| **6. Par région** | `ouvrage` | `ref_geo_admin.niveau = 'region'` |
| **7. Par département** | `ouvrage` | `ref_geo_admin.niveau = 'departement'` |
| **8. Par sous-préfecture** | `ouvrage` | `ref_geo_admin.niveau = 'sous_prefecture'` |
| **9. Par localité** | `ouvrage` | `localite.nom_usage` |

### Axe 3 — Filtres métier (pour le mode « Tous »)
| Mode | Source | Filtre |
|---|---|---|
| **10. Par type d'ouvrage** | `ouvrage` | `type_ouvrage.code` (PMH, HVA, PEA…) |
| **11. Par état** | `ouvrage` | `ouvrage.etat` (fonctionnel, en_panne…) |
| **12. Par année** | `ouvrage` | `annee_realisation` (min/max) |
| **13. Par bailleur** | `ouvrage` + `ouvrage_projet` | `source.nom` (UNICEF, BAD…) |

### Axe 4 — Combinaisons
Tous ces filtres peuvent se **combiner** :
- **14. District + Type** : « Tous les PMH du district CAVALLY »
- **15. Fichier + Feuille** : « Feuille PMH du fichier1 »
- **16. Fichier + Statut qualité** : « Lignes `localite_non_resolue` du fichier22 »
- **17. Type + État** : « PMH en panne »

---

## 2. Ce qui manque aujourd'hui

| Fonctionnalité | Statut |
|---|---|
| Métadonnées dans le mode « Tous » | ✅ |
| **Métadonnées dans le mode « Par fichier »** | ❌ à ajouter |
| **Filtre par district/région/département/sous-préfecture** | ⚠️ backend OK, UI non |
| **Filtre par localité** | ❌ à ajouter |
| **Filtre par type d'ouvrage (UI)** | ⚠️ backend OK, UI non |
| **Filtre par état (UI)** | ⚠️ backend OK, UI non |
| **Filtre par année (UI)** | ⚠️ backend OK, UI non |
| **Filtre par bailleur** | ❌ à ajouter |
| **Mode par run** | ❌ à ajouter |
| **Combinaisons de filtres** | ❌ à ajouter |

---

## 3. Handoff — État actuel et décisions à prendre

```markdown
# Handoff — Phase 6.4 (Carte) — v4.1

## État actuel
- ✅ Carte satellite (Esri) fonctionnelle, échelle pays.
- ✅ Mode « Tous » → 2 379 ouvrages (métadonnées OK).
- ✅ Mode « Par fichier » → lignes ingérées (mais **métadonnées absentes**, points colorés grâce au fix `nom_feuille`).
- ✅ Popup avec `<details>` pour métadonnées (mode « Tous » uniquement).
- ⏳ Filtres UI : district, région, type, état, année → **backend OK, UI non**.

## Décisions à prendre
1. Quels modes d'affichage veut-on dans le MVP ?
2. Quels filtres veut-on dans l'UI ?
3. Veut-on les métadonnées dans le mode « Par fichier » (lignes brutes) ?

## Prochaines étapes
- Décider du périmètre UI Carte.
- Coder les filtres + le fix métadonnées « Par fichier ».
- Passer à 6.5 (Liste).
```

---

## 4. Question

1. **Dans le MVP**, quels modes veux-tu ?
    - **A** : Tous + Par fichier (actuel) + filtres géo/métier
    - **B** : Tous + Par fichier + Par feuille + filtres géo/métier
    - **C** : Tous + Par fichier + Par run + filtres géo/métier
    - **D** : Tout (tous les modes de la liste)

2. **Quels filtres** veux-tu dans l'UI ?
    - Type d'ouvrage (PMH, HVA, PEA…)
    - État (fonctionnel, en_panne…)
    - District / Région / Département / Sous-préfecture
    - Année (min/max)
    - Bailleur

3. **Métadonnées « Par fichier »** : on les ajoute (donnees_brutes) ?

**Ma reco** :
- **Mode** : **A** (Tous + Par fichier) + filtres.
- **Filtres** : Type, État, District/Région (les plus utiles).
- **Métadonnées** : oui, on les ajoute dans « Par fichier » (10 lignes de code).
