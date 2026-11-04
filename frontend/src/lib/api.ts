/**
 * Client API DHR.
 * Utilise fetch natif. Gère API key + JWT.
 */

const API_BASE = '/api'  // proxy Vite → http://localhost:8000/v1

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
    type_source: string
    actif: boolean
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
    type_contenu: string
    nb_lignes: number
    nb_lignes_valides: number
    statut_ingestion: string
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
    type_ouvrage: { code: string; libelle: string }
    etat: string
    annee_realisation: number | null
    localite: { id_localite: number; nom_usage: string }
    geom: { type: string; coordinates: [number, number] } | null
    cgpe: { existe: boolean; statut: string | null } | null
    financements: { id_projet: number; nom_projet: string; bailleur: string; role: string }[]
    metadata: Record<string, unknown> | null
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

// ---------- Requêtes ----------
async function request<T>(
    path: string,
    options: RequestInit & { auth?: 'api_key' | 'jwt' | 'none' } = {},
): Promise<T> {
    const { auth = 'api_key', ...fetchOptions } = options

    const headers = new Headers(fetchOptions.headers)
    headers.set('Content-Type', 'application/json')

    if (auth === 'api_key') {
        headers.set('X-API-Key', API_KEY)
    } else if (auth === 'jwt') {
        if (!jwtToken) throw new Error('JWT manquant. Connectez-vous.')
        headers.set('Authorization', `Bearer ${jwtToken}`)
    }

    const res = await fetch(`${API_BASE}${path}`, { ...fetchOptions, headers })

    if (!res.ok) {
        let problem: Problem
        try {
            problem = await res.json()
        } catch {
            problem = { type: 'unknown', title: 'Erreur', status: res.status }
        }
        throw Object.assign(new Error(problem.title || 'Erreur API'), { problem })
    }

    if (res.status === 204) return undefined as T
    return res.json()
}

// ---------- Endpoints ----------
export const api = {
    // Référentiels
    sources: () => request<{ data: Source[] }>('/sources'),
    typesOuvrage: () => request<{ data: unknown[] }>('/types-ouvrage'),

    // Fichiers
    fichiers: (params?: { offset?: number; limit?: number }) => {
        const q = new URLSearchParams()
        if (params?.offset !== undefined) q.set('offset', String(params.offset))
        if (params?.limit !== undefined) q.set('limit', String(params.limit))
        return request<{ data: Fichier[]; pagination: PaginationOffset }>(`/fichiers?${q}`)
    },
    fichier: (id: number) => request<Fichier>(`/fichiers/${id}`),
    feuilles: (idFichier: number) =>
        request<{ data: Feuille[]; pagination: PaginationOffset }>(`/fichiers/${idFichier}/feuilles`),

    // Upload
    upload: async (file: File, idSource: number, commentaire?: string) => {
        const form = new FormData()
        form.append('file', file)
        form.append('id_source', String(idSource))
        if (commentaire) form.append('commentaire', commentaire)

        const headers = new Headers()
        if (!jwtToken) throw new Error('JWT manquant')
        headers.set('Authorization', `Bearer ${jwtToken}`)

        const res = await fetch(`${API_BASE}/fichiers`, {
            method: 'POST',
            headers,
            body: form,
        })
        if (!res.ok) {
            const problem = await res.json().catch(() => ({}))
            throw Object.assign(new Error(problem.detail || 'Erreur upload'), { problem })
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

    // Mapping
    mappingProposal: (idFichier: number) =>
        request<MappingProposalFeuille[]>(`/fichiers/${idFichier}/mapping-proposal`),
    saveMapping: (idFichier: number, idFeuille: number, colonnes: { entete_brut: string; champ_cible: string | null }[]) =>
        request<MappingProposalFeuille>(`/fichiers/${idFichier}/mapping?id_feuille=${idFeuille}`, {
            method: 'PUT',
            auth: 'jwt',
            body: JSON.stringify({ colonnes }),
        }),

    // Runs
    lancerRun: (idFichier: number, mode: 'complet' | 'echantillon' | 'plage' = 'complet') =>
        request<{ id_run: number; id_fichier: number; statut: string; started_at: string; poll_url: string }>(
            `/fichiers/${idFichier}/runs?mode=${mode}`,
            { method: 'POST', auth: 'jwt' },
        ),
    run: (id: number) => request<IngestionRun>(`/runs/${id}`),
    runsFichier: (idFichier: number) =>
        request<{ data: IngestionRun[]; pagination: PaginationOffset }>(`/fichiers/${idFichier}/runs`),

    // Ouvrages
    ouvrages: (params?: Record<string, string | number>) => {
        const q = new URLSearchParams()
        if (params) for (const [k, v] of Object.entries(params)) q.set(k, String(v))
        return request<{ data: Ouvrage[]; pagination: PaginationCursor }>(`/ouvrages?${q}`)
    },
    ouvrage: (id: number) => request<Ouvrage>(`/ouvrages/${id}`),

    // Carto
    cartoFichier: (idFichier: number, params?: Record<string, string | number>) => {
        const q = new URLSearchParams()
        if (params) for (const [k, v] of Object.entries(params)) q.set(k, String(v))
        return request<FeatureCollection>(`/carto/fichiers/${idFichier}/points?${q}`)
    },
    cartoTous: (params?: Record<string, string | number>) => {
        const q = new URLSearchParams()
        if (params) for (const [k, v] of Object.entries(params)) q.set(k, String(v))
        return request<FeatureCollection>(`/carto/tous/points?${q}`)
    },

    // Qualité
    qualite: (idFichier: number) => request<QualiteFichier>(`/qualite/fichiers/${idFichier}`),

    // Export (retourne un blob)
    exportExcel: async (params?: Record<string, string | number>) => {
        const q = new URLSearchParams()
        if (params) for (const [k, v] of Object.entries(params)) q.set(k, String(v))
        const headers = new Headers()
        headers.set('X-API-Key', API_KEY)
        const res = await fetch(`${API_BASE}/ouvrages/export?${q}`, { headers })
        if (!res.ok) throw new Error('Erreur export Excel')
        return res.blob()
    },
    exportCsv: async (params?: Record<string, string | number>) => {
        const q = new URLSearchParams()
        if (params) for (const [k, v] of Object.entries(params)) q.set(k, String(v))
        const headers = new Headers()
        headers.set('X-API-Key', API_KEY)
        const res = await fetch(`${API_BASE}/ouvrages/export.csv?${q}`, { headers })
        if (!res.ok) throw new Error('Erreur export CSV')
        return res.blob()
    },
    refGeo: (params?: { niveau?: string; parent_id?: number }) => {
        const q = new URLSearchParams()
        if (params?.niveau) q.set('niveau', params.niveau)
        if (params?.parent_id !== undefined) q.set('parent_id', String(params.parent_id))
        return request<{ data: any[]; pagination: PaginationOffset }>(`/ref-geo?${q}`)
    },
    localites: (params?: { q?: string; limit?: number }) => {
        const q = new URLSearchParams()
        if (params?.q) q.set('q', params.q)
        if (params?.limit !== undefined) q.set('limit', String(params.limit))
        return request<{ data: any[]; pagination: PaginationOffset }>(`/localites?${q}`)
    },
}