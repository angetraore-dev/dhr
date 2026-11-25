/**
 * Types et constantes partagés pour les filtres (Liste, Carte).
 */
export interface Filters {
    region: string
    departement: string
    sous_prefecture: string
    localite: string
    type_alimentation: string
    nature_ouvrage: string
    realisation_par: string
    etat: string
    annee_min: string
    annee_max: string
}

export const EMPTY_FILTERS: Filters = {
    region: '',
    departement: '',
    sous_prefecture: '',
    localite: '',
    type_alimentation: '',
    nature_ouvrage: '',
    realisation_par: '',
    etat: '',
    annee_min: '',
    annee_max: '',
}