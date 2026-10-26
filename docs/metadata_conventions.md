# Conventions des métadonnées (`*.metadata`)

## 1. Objectif

Les fichiers reçus des sources (ONEP, SODECI, UNICEF, BAD, LONACI, État…)
contiennent souvent des colonnes **non mappées** vers les champs normalisés
de la base. Pour ne pas perdre cette information, on la conserve dans :

- `ligne_ingeree.donnees_brutes` (jsonb) — **ligne Excel brute intégrale**, immuable
- `localite.metadata` (jsonb) — attributs consolidés non mappés de la localité
- `ouvrage.metadata` (jsonb) — attributs consolidés non mappés de l'ouvrage
- `cgpe.metadata` (jsonb) — attributs consolidés non mappés du CGPE

Ce document définit la **convention de nommage** et la **liste des clés connues**
pour les trois tables métier.

## 2. Règles de nommage

Toute clé ajoutée dans un `metadata` doit respecter :

1. **`snake_case`** : `profondeur_forage`, pas `ProfondeurForage` ni `profondeur-forage`.
2. **Unité dans le nom si pertinent** : `profondeur_forage_m`, `debit_l_s`.
3. **Préfixe source si ambiguïté** : `onep_profondeur_forage_m` (quand deux sources
   donnent des valeurs différentes pour le même concept).
4. **Valeur typée** : nombre pour les numériques, booléen pour les oui/non,
   chaîne ISO 8601 pour les dates (`"2023-05-12"`).
5. **Pas de valeur `null`** : si la valeur est absente, **ne pas mettre la clé**.
6. **Pas de clé générique** : `valeur1`, `champ2`, `colonne_x` sont interdits.
7. **Documenter ici** toute nouvelle clé (section 4).

## 3. Cycle de vie d'une clé `metadata`

1. **Détection** : à l'ingestion, la clé non mappée est détectée dans
   `donnees_brutes` (à la consolidation `ligne_ingeree` → entité métier).
2. **Proposition** : la clé est nommée selon la convention et ajoutée au
   `metadata` de l'entité concernée (`localite`, `ouvrage` ou `cgpe`).
3. **Documentation** : ajoutée à la section 4 de ce document.
4. **Promotion (V2)** : si la clé devient critique (utilisée dans des filtres,
   rapports, exports), elle est promue en attribut de première classe via
   `attribut_definition` + `ouvrage_attribut`. Elle peut alors être retirée
   de `metadata` (ou conservée en doublon temporaire le temps de la migration).

## 4. Clés documentées

> Cette liste est **vivante**. Elle est mise à jour à chaque nouvelle clé rencontrée.

### 4.1 `localite.metadata`

| Clé | Type | Unité | Description | Sources connues |
|---|---|---|---|---|
| `population_estimee` | number | habitants | Population estimée de la localité | ONEP, UNICEF |
| `existence_ecole` | boolean | — | Présence d'une école | ONEP |
| `existence_dispensaire` | boolean | — | Présence d'un dispensaire | ONEP |
| `type_habitat` | string | — | Type d'habitat dominant (ex. "habitat dispersé") | ONEP |
| `accessibilite_routiere` | string | — | Accessibilité (ex. "piste dégradée") | UNICEF |

### 4.2 `ouvrage.metadata`

| Clé | Type | Unité | Description | Sources connues |
|---|---|---|---|---|
| `profondeur_forage_m` | number | m | Profondeur totale du forage | ONEP, UNICEF |
| `debit_l_s` | number | L/s | Débit nominal de l'ouvrage | ONEP |
| `nom_prestataire` | string | — | Nom de l'entreprise réalisatrice | UNICEF, BAD |
| `date_mise_en_service` | string (ISO 8601) | — | Date de mise en service | ONEP |
| `observations_terrain` | string | — | Observations libres de l'agent | ONEP, UNICEF |

### 4.3 `cgpe.metadata`

| Clé | Type | Unité | Description | Sources connues |
|---|---|---|---|---|
| `nom_president` | string | — | Nom du président du CGPE | ONEP |
| `contact_president` | string | — | Téléphone du président | ONEP |
| `date_derniere_reunion` | string (ISO 8601) | — | Date de la dernière réunion | UNICEF |

> **Ajouter une clé** : ouvrir une PR qui modifie ce fichier + le code d'ingestion
> qui la reconnaît. Une clé non documentée ici ne doit pas être ajoutée en base.

## 5. Ce qu'il ne faut **pas** mettre dans `metadata`

- Les champs déjà normalisés (`etat`, `annee_realisation`, `type_ouvrage`,
  `latitude_decimal`, `longitude_decimal`, `id_localite`, `nom_usage`…) → ils
  ont leurs colonnes dédiées.
- Les identifiants internes (`id_ligne`, `id_fichier`, `id_run`) → ils sont
  dans `ligne_ingeree`.
- Les données personnelles sensibles sans base légale (RGPD) → à traiter
  séparément si besoin.
- Les fichiers binaires ou les URLs temporaires.

## 6. Requêtes utiles

### 6.1 Lister les ouvrages ayant une clé `metadata` donnée

```sql
SELECT id_ouvrage, metadata->>'profondeur_forage_m' AS profondeur
FROM ouvrage
WHERE metadata ? 'profondeur_forage_m';
```

### 6.2 Compter les occurrences d'une clé par source

```sql
SELECT s.nom AS source, COUNT(*) AS nb
FROM ouvrage o
JOIN ligne_ingeree li ON li.id_ouvrage_consolide = o.id_ouvrage
JOIN feuille fe ON fe.id_feuille = li.id_feuille
JOIN fichier f ON f.id_fichier = fe.id_fichier
JOIN source s ON s.id_source = f.id_source
WHERE o.metadata ? 'profondeur_forage_m'
GROUP BY s.nom
ORDER BY nb DESC;
```

### 6.3 Détecter les clés `metadata` non documentées

```sql
SELECT 'localite' AS table_cible, cle FROM (
    SELECT DISTINCT jsonb_object_keys(metadata) AS cle
    FROM localite WHERE metadata <> '{}'::jsonb
) t
UNION ALL
SELECT 'ouvrage' AS table_cible, cle FROM (
    SELECT DISTINCT jsonb_object_keys(metadata) AS cle
    FROM ouvrage WHERE metadata <> '{}'::jsonb
) t
UNION ALL
SELECT 'cgpe' AS table_cible, cle FROM (
    SELECT DISTINCT jsonb_object_keys(metadata) AS cle
    FROM cgpe WHERE metadata <> '{}'::jsonb
) t
ORDER BY table_cible, cle;
```

→ Comparer le résultat à la section 4 de ce document. Toute clé absente
doit être soit documentée, soit supprimée (si jugée non pertinente).

## 7. Évolution

- **MVP** : `metadata` simple, sans traçabilité fine de l'origine.
- **V2** : ajout de `metadata_sources` (jsonb) sur chaque table métier pour
  tracer l'origine de chaque clé (fichier, ligne, source, date).
- **V2+** : `attribut_definition` + `ouvrage_attribut` pour promouvoir
  les clés critiques en attributs de première classe.
