/**
 * Client API DHR.
 * Utilise fetch natif. Gère API key + JWT.
 *
 * Notes :
 * - `API_BASE = '/api'` : proxy Vite → http://localhost:8000/v1
 *   (à configurer dans vite.config.ts : `/api` → `http://localhost:8000/v1`)
 * - `request()` gère RFC 7807 et redirige vers /parametres sur 401 (F5)
 */

const API_BASE = '/api'

const API_KEY = import.meta.env.VITE_API_KEY || 'dhr_dev_read_key_change_me'

let jwtToken: string | null = localStorage.getItem('jwt')

export function setJwt(token: string | null) {
    jwtToken = token
    if (token) localStorage.setItem('jwt', token)
    else localStorage.removeItem('jwt')
}

export function getJwt(): string | null {
    return jwtToken
}

// ---------- Types ----------
export interface PaginationOffset {
    offset: number
    limit: number
    total: number | null
}

export interface PaginationCursor {
    limit: number
    next_cursor: string | null
    has_more: boolean
}

export interface Problem {
    type: string
    title: string
    status: number
    detail?: string
    instance?: string
    errors?: { field: string; message: string }[]
}

export interface Source {
    id_source: number
    nom: string
    type_source: 'public' | 'prive' | 'bailleur' | 'etat' | 'autre'
    actif: boolean
}

export interface RefGeoParent {
    id_geo: number
    niveau: string
    nom: string
}

export interface RefGeoAdmin {
    id_geo: number
    niveau: 'district' | 'region' | 'departement' | 'sous_prefecture' | 'localite'
    nom: string
    code_officiel: string | null
    type_localite: 'village' | 'campement' | 'autre' | null
    parent: RefGeoParent | null
}

export interface LocaliteResume {
    id_localite: number
    nom_usage: string
}

export interface Localite extends LocaliteResume {
    latitude_centre: number | null
    longitude_centre: number | null
    geom_centre: { type: 'Point'; coordinates: [number, number] } | null
    alias: string[]
    metadata?: Record<string, unknown> | null
}

export interface Fichier {
    id_fichier: number
    nom_fichier_original: string
    source: Source
    hash_sha256: string | null
    taille_octets: number | null
    date_reception: string
    date_ingestion: string | null
    statut: 'en_attente' | 'en_cours' | 'ingere' | 'partiel' | 'erreur'
    nb_feuilles: number
    nb_lignes_total: number
    est_reingestion: boolean
    commentaire: string | null
}

export interface Feuille {
    id_feuille: number
    id_fichier: number
    nom_feuille: string
    index_feuille: number
    type_contenu: 'ouvrages' | 'cgpe' | 'mixte' | 'autre' | 'inconnu'
    nb_lignes: number
    nb_lignes_valides: number
    statut_ingestion: 'en_attente' | 'en_cours' | 'ingere' | 'partiel' | 'erreur'
    message_erreur: string | null
}

export interface IngestionRun {
    id_run: number
    id_fichier: number
    id_feuille: number | null
    mode: 'complet' | 'echantillon' | 'plage'
    limite_lignes: number | null
    ligne_debut: number | null
    ligne_fin: number | null
    nb_lignes_ingerees: number
    statut: 'en_cours' | 'termine' | 'erreur' | 'annule'
    message: string | null
    started_at: string
    finished_at: string | null
}

export type StatutQualite =
    | 'ok'
    | 'localite_non_resolue'
    | 'geom_invalide'
    | 'type_ouvrage_inconnu'
    | 'rejete'
    | 'doublon_suspect'

export interface LigneIngeree {
    id_ligne: number
    id_feuille: number
    num_ligne_source: number
    localite_brute: string | null
    type_ouvrage_brut: string | null
    usage_ouvrage_brut: string | null
    latitude_decimal: number | null
    longitude_decimal: number | null
    statut_qualite: StatutQualite
    message_qualite?: string | null
    annee_projet: number | null
    bailleur_brut: string | null
    donnees_brutes?: Record<string, unknown>
}

export interface MappingColonne {
    id_mapping: number | null
    entete_brut: string
    champ_cible: string | null
    confiance: number | null
    valide_par_utilisateur: boolean
}

export interface MappingProposalFeuille {
    id_feuille: number
    nom_feuille: string
    header_row: number
    colonnes: MappingColonne[]
}

export interface Ouvrage {
    id_ouvrage: number
    code_ouvrage: string | null
    nature_ouvrage: 'puits' | 'forage' | 'inconnu' | null
    type_alimentation: 'PMH' | 'HVA' | 'PEA' | 'HV' | 'AUTRE' | null
    realisation_par: 'public' | 'prive' | 'inconnu' | null
    etat: 'fonctionnel' | 'en_panne' | 'abandonne' | 'inconnu'
    annee_realisation: number | null
    localite: LocaliteResume
    geom: { type: 'Point'; coordinates: [number, number] } | null
    cgpe: { existe: boolean; statut: string | null } | null
    financements: Array<{
        id_projet: number
        nom_projet: string
        bailleur: string | null
        role: 'principal' | 'co_financement'
    }>
    qualite_eau?: Record<string, unknown> | null
    metadata?: Record<string, unknown> | null
}

export interface QualiteFichier {
    id_fichier: number
    nom_fichier: string
    source: string
    statut: string
    nb_lignes_total: number
    qualite: {
        ok: number
        localite_non_resolue: number
        geom_invalide: number
        type_ouvrage_inconnu: number
        rejete: number
        doublon_suspect: number
    }
    taux_reussite: number
}

export interface FeatureCollection {
    type: 'FeatureCollection'
    features: {
        type: 'Feature'
        id?: string
        geometry: { type: 'Point'; coordinates: [number, number] }
        properties: Record<string, unknown>
    }[]
    meta: Record<string, unknown>
}

export interface OuvrageFilters {
    nature_ouvrage?: string
    type_alimentation?: string
    realisation_par?: string
    etat?: string
    region?: string
    departement?: string
    sous_prefecture?: string
    localite?: string
    bailleur?: string
    annee_min?: number
    annee_max?: number
}

// ---------- Helpers ----------
function triggerBlobDownload(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
}

function toQuery(params?: Record<string, string | number | undefined>): string {
    const q = new URLSearchParams()
    if (params) {
        for (const [k, v] of Object.entries(params)) {
            if (v !== undefined && v !== null && v !== '') q.set(k, String(v))
        }
    }
    const s = q.toString()
    return s ? `?${s}` : ''
}

async function parseProblem(res: Response): Promise<Problem> {
    try {
        return (await res.json()) as Problem
    } catch {
        return { type: 'unknown', title: 'Erreur', status: res.status }
    }
}

// ---------- Requêtes ----------
type AuthMode = 'api_key' | 'jwt' | 'none'

async function request<T>(
    path: string,
    options: RequestInit & { auth?: AuthMode } = {},
): Promise<T> {
    const { auth = 'api_key', ...fetchOptions } = options

    const headers = new Headers(fetchOptions.headers)
    if (!headers.has('Content-Type') && fetchOptions.body) {
        headers.set('Content-Type', 'application/json')
    }

    if (auth === 'api_key') {
        headers.set('X-API-Key', API_KEY)
    } else if (auth === 'jwt') {
        if (!jwtToken) throw new Error('JWT manquant. Connectez-vous dans Paramètres.')
        headers.set('Authorization', `Bearer ${jwtToken}`)
    }

    const res = await fetch(`${API_BASE}${path}`, { ...fetchOptions, headers })

    if (res.status === 401) {
        // F5 : redirection vers /parametres sur 401
        if (typeof window !== 'undefined' && window.location.pathname !== '/parametres') {
            window.location.href = '/parametres'
        }
    }

    if (!res.ok) {
        const problem = await parseProblem(res)
        const err = new Error(problem.title || 'Erreur API') as Error & { problem?: Problem }
        err.problem = problem
        throw err
    }

    if (res.status === 204) return undefined as T
    return res.json() as Promise<T>
}

// ---------- Endpoints ----------
export const api = {
    // ----- Référentiels -----
    sources: (params?: { offset?: number; limit?: number }) =>
        request<{ data: Source[]; pagination: PaginationOffset }>(
            `/sources${toQuery(params)}`,
        ),

    refGeo: (params?: { niveau?: string; parent_id?: number; offset?: number; limit?: number }) =>
        request<{ data: RefGeoAdmin[]; pagination: PaginationOffset }>(
            `/ref-geo${toQuery(params)}`,
        ),

    refGeoChemin: (idGeo: number) =>
        request<RefGeoAdmin[]>(`/ref-geo/${idGeo}/chemin`),

    localites: (params?: { q?: string; id_geo?: number; offset?: number; limit?: number }) =>
        request<{ data: LocaliteResume[]; pagination: PaginationOffset }>(
            `/localites${toQuery(params)}`,
        ),

    localite: (id: number, includeMetadata = false) =>
        request<Localite>(
            `/localites/${id}${includeMetadata ? '?include=metadata' : ''}`,
        ),

    // ----- Fichiers -----
    fichiers: (params?: { id_source?: number; statut?: string; offset?: number; limit?: number }) =>
        request<{ data: Fichier[]; pagination: PaginationOffset }>(
            `/fichiers${toQuery(params)}`,
        ),

    fichier: (id: number) => request<Fichier>(`/fichiers/${id}`),

    feuilles: (idFichier: number, params?: { offset?: number; limit?: number }) =>
        request<{ data: Feuille[]; pagination: PaginationOffset }>(
            `/fichiers/${idFichier}/feuilles${toQuery(params)}`,
        ),

    // ----- Upload -----
    upload: async (file: File, idSource: number, commentaire?: string, force = false) => {
        const form = new FormData()
        form.append('file', file)
        form.append('id_source', String(idSource))
        if (commentaire) form.append('commentaire', commentaire)

        if (!jwtToken) throw new Error('JWT manquant. Connectez-vous dans Paramètres.')
        const headers = new Headers()
        headers.set('Authorization', `Bearer ${jwtToken}`)

        const res = await fetch(
            `${API_BASE}/fichiers${force ? '?force=true' : ''}`,
            { method: 'POST', headers, body: form },
        )

        if (!res.ok) {
            const problem = await parseProblem(res)
            const err = new Error(problem.title || 'Erreur upload') as Error & { problem?: Problem }
            err.problem = problem
            throw err
        }
        return res.json() as Promise<{
            id_fichier: number
            nom_fichier_original: string
            statut: string
            hash_sha256: string
            est_reingestion: boolean
            feuilles_detectees: { nom: string; index: number; nb_lignes_estime: number }[]
        }>
    },

    // ----- Mapping -----
    mappingProposal: (idFichier: number) =>
        request<MappingProposalFeuille[]>(`/fichiers/${idFichier}/mapping-proposal`),

    saveMapping: (
        idFichier: number,
        idFeuille: number,
        colonnes: { entete_brut: string; champ_cible: string | null }[],
    ) =>
        request<MappingProposalFeuille>(
            `/fichiers/${idFichier}/mapping?id_feuille=${idFeuille}`,
            { method: 'PUT', auth: 'jwt', body: JSON.stringify({ colonnes }) },
        ),

    // ----- Runs & Lignes -----
    lancerRun: (
        idFichier: number,
        params?: {
            mode?: 'complet' | 'echantillon' | 'plage'
            id_feuille?: number
            limite_lignes?: number
            ligne_debut?: number
            ligne_fin?: number
        },
    ) =>
        request<{
            id_run: number
            id_fichier: number
            statut: string
            started_at: string
            poll_url: string
        }>(`/fichiers/${idFichier}/runs${toQuery(params ?? { mode: 'complet' })}`, {
            method: 'POST',
            auth: 'jwt',
        }),

    run: (id: number) => request<IngestionRun>(`/runs/${id}`),

    runsFichier: (idFichier: number, params?: { offset?: number; limit?: number }) =>
        request<{ data: IngestionRun[]; pagination: PaginationOffset }>(
            `/fichiers/${idFichier}/runs${toQuery(params)}`,
        ),

    lignesRun: (
        idRun: number,
        params?: { statut_qualite?: string; cursor?: string; limit?: number },
    ) =>
        request<{ data: LigneIngeree[]; pagination: PaginationCursor }>(
            `/runs/${idRun}/lignes${toQuery(params)}`,
        ),

    lignesFeuille: (
        idFeuille: number,
        params?: { id_run?: number; statut_qualite?: string; cursor?: string; limit?: number },
    ) =>
        request<{ data: LigneIngeree[]; pagination: PaginationCursor }>(
            `/feuilles/${idFeuille}/lignes${toQuery(params)}`,
        ),

    ligne: (id: number, includeBrut = false) =>
        request<LigneIngeree>(
            `/lignes/${id}${includeBrut ? '?include=brut' : ''}`,
        ),

    // ----- Ouvrages -----
    ouvrages: (params?: OuvrageFilters & { cursor?: string; limit?: number; include?: string }) =>
        request<{ data: Ouvrage[]; pagination: PaginationCursor }>(
            `/ouvrages${toQuery(params)}`,
        ),

    ouvrage: (id: number, includeMetadata = false) =>
        request<Ouvrage>(
            `/ouvrages/${id}${includeMetadata ? '?include=metadata' : ''}`,
        ),

    // ----- Carto -----
    cartoFichier: (
        idFichier: number,
        params?: {
            id_feuille?: number
            id_run?: number
            statut_qualite?: string
            type_alimentation?: string
            localite?: string
            region?: string
            departement?: string
            sous_prefecture?: string
        },
    ) =>
        request<FeatureCollection>(
            `/carto/fichiers/${idFichier}/points${toQuery(params)}`,
        ),

    cartoTous: (params?: OuvrageFilters & { include?: string }) =>
        request<FeatureCollection>(`/carto/tous/points${toQuery(params)}`),

    // ----- Qualité -----
    qualite: (idFichier: number) =>
        request<QualiteFichier>(`/qualite/fichiers/${idFichier}`),

    // ----- Export (fetch + blob, F3) -----
    exportOuvrages: async (
        format: 'xlsx' | 'csv',
        params?: OuvrageFilters & { include?: string; with_summary?: boolean },
    ) => {
        const path = format === 'csv' ? '/ouvrages/export.csv' : '/ouvrages/export'
        const headers = new Headers()
        headers.set('X-API-Key', API_KEY)

        const res = await fetch(`${API_BASE}${path}${toQuery(params)}`, { headers })

        if (!res.ok) {
            const problem = await parseProblem(res)
            throw new Error(
                problem.title || `Erreur export ${format.toUpperCase()}`,
            )
        }

        const blob = await res.blob()
        const date = new Date().toISOString().slice(0, 10)
        triggerBlobDownload(blob, `ouvrages_${date}.${format}`)
    },
}