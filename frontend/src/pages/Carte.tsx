import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Map as MapIcon, Layers, FileSpreadsheet, Boxes } from 'lucide-react'
import { api, type FeatureCollection } from '@/lib/api'
import { MapView, type MapMode } from '@/components/MapView'
import { Button } from '@/components/ui/button'
import { FiltersPanel } from '@/components/FiltersPanel'
import { EMPTY_FILTERS, type Filters } from '@/lib/filters'

type SousMode = 'brut' | 'ouvrages'

export default function Carte() {
    const [mode, setMode] = useState<MapMode>('tous')
    const [sousMode, setSousMode] = useState<SousMode>('brut')
    const [idFichier, setIdFichier] = useState<number | null>(null)
    const [idFeuille, setIdFeuille] = useState<number | null>(null)
    const [idRun, setIdRun] = useState<number | null>(null)
    const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS)

    const { data: fichiers } = useQuery({
        queryKey: ['fichiers'],
        queryFn: () => api.fichiers({ limit: 100 }),
    })

    const { data: feuilles } = useQuery({
        queryKey: ['feuilles', idFichier],
        queryFn: () => api.feuilles(idFichier!),
        enabled: idFichier !== null,
    })

    const { data: runsData } = useQuery({
        queryKey: ['runs', idFichier],
        queryFn: () => api.runsFichier(idFichier!),
        enabled: idFichier !== null,
    })

    // Reset feuille + run quand le fichier change
    useEffect(() => {
        setIdFeuille(null)
        setIdRun(null)
    }, [idFichier])

    const { data: cartoData, isLoading } = useQuery<FeatureCollection>({
        queryKey: [
            'carto',
            mode,
            sousMode,
            idFichier,
            idFeuille,
            idRun,
            filters,
        ],
        queryFn: () => {
            // ----- Mode Tous -----
            if (mode === 'tous') {
                const params: Record<string, string | number> = {}
                for (const [k, v] of Object.entries(filters)) {
                    if (v) params[k] = v
                }
                return api.cartoTous(params)
            }

            // ----- Mode Fichier -----
            if (idFichier === null) {
                return Promise.resolve({
                    type: 'FeatureCollection' as const,
                    features: [],
                    meta: { count: 0 },
                })
            }

            // Sous-mode « Ouvrages consolidés » : pas de filtres, pas de run/feuille
            if (sousMode === 'ouvrages') {
                return api.cartoFichiersOuvrages(idFichier)
            }

            // Sous-mode « Lignes brutes » : filtres supportés par /points
            const fichierParams: Record<string, string | number> = {}
            if (filters.type_alimentation)
                fichierParams.type_alimentation = filters.type_alimentation
            if (filters.region) fichierParams.region = filters.region
            if (filters.departement)
                fichierParams.departement = filters.departement
            if (filters.sous_prefecture)
                fichierParams.sous_prefecture = filters.sous_prefecture
            if (filters.localite) fichierParams.localite = filters.localite
            if (idFeuille !== null) fichierParams.id_feuille = idFeuille
            if (idRun !== null) fichierParams.id_run = idRun
            return api.cartoFichier(idFichier, fichierParams)
        },
        enabled: mode === 'tous' || idFichier !== null,
    })

    const pointCount = cartoData?.features.length ?? 0
    const hasRuns = (runsData?.data.length ?? 0) > 0

    // En sous-mode « Ouvrages », les filtres géo/métier ne s'appliquent pas
    const showFilters = mode === 'tous' || sousMode === 'brut'

    return (
        <div className="space-y-4">
            {/* En-tête + toggles mode */}
            <div className="flex items-center justify-between flex-wrap gap-2">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Carte</h2>
                    <p className="text-sm text-gray-500">
                        {isLoading
                            ? 'Chargement...'
                            : `${pointCount} point(s) affiché(s)`}
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        variant={mode === 'tous' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => {
                            setMode('tous')
                            setIdFichier(null)
                            setIdFeuille(null)
                            setIdRun(null)
                        }}
                    >
                        <Layers className="w-4 h-4 mr-1" /> Tous
                    </Button>
                    <Button
                        variant={mode === 'fichier' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => {
                            setMode('fichier')
                            setIdFichier(null)
                            setIdFeuille(null)
                            setIdRun(null)
                        }}
                    >
                        <MapIcon className="w-4 h-4 mr-1" /> Par fichier
                    </Button>
                </div>
            </div>

            {/* Sélecteurs (mode Fichier uniquement) */}
            {mode === 'fichier' && (
                <div className="flex gap-3 items-center flex-wrap bg-gray-50 p-3 rounded-lg border">
                    {/* Toggle sous-mode */}
                    <div className="flex items-center gap-1 border-r pr-3">
                        <Button
                            variant={sousMode === 'brut' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setSousMode('brut')}
                        >
                            <FileSpreadsheet className="w-4 h-4 mr-1" />
                            Lignes brutes
                        </Button>
                        <Button
                            variant={sousMode === 'ouvrages' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setSousMode('ouvrages')}
                        >
                            <Boxes className="w-4 h-4 mr-1" />
                            Ouvrages consolidés
                        </Button>
                    </div>

                    {/* Sélecteur fichier (toujours visible) */}
                    <select
                        value={idFichier ?? ''}
                        onChange={(e) =>
                            setIdFichier(
                                e.target.value ? Number(e.target.value) : null,
                            )
                        }
                        className="h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-sm"
                    >
                        <option value="">— Sélectionner un fichier —</option>
                        {fichiers?.data.map((f) => (
                            <option key={f.id_fichier} value={f.id_fichier}>
                                {f.nom_fichier_original} ({f.statut})
                            </option>
                        ))}
                    </select>

                    {/* Sélecteurs feuille + run : uniquement en sous-mode « brut » */}
                    {sousMode === 'brut' && idFichier !== null && feuilles && feuilles.data.length > 0 && (
                        <select
                            value={idFeuille ?? ''}
                            onChange={(e) =>
                                setIdFeuille(
                                    e.target.value
                                        ? Number(e.target.value)
                                        : null,
                                )
                            }
                            className="h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-sm"
                        >
                            <option value="">Toutes les feuilles</option>
                            {feuilles.data.map((fe) => (
                                <option key={fe.id_feuille} value={fe.id_feuille}>
                                    {fe.nom_feuille}
                                </option>
                            ))}
                        </select>
                    )}

                    {sousMode === 'brut' && idFichier !== null && hasRuns && (
                        <select
                            value={idRun ?? ''}
                            onChange={(e) =>
                                setIdRun(
                                    e.target.value
                                        ? Number(e.target.value)
                                        : null,
                                )
                            }
                            className="h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-sm"
                        >
                            <option value="">
                                Tous les runs ({runsData!.data.length})
                            </option>
                            {runsData!.data.map((r) => (
                                <option key={r.id_run} value={r.id_run}>
                                    Run #{r.id_run} — {r.statut} (
                                    {r.nb_lignes_ingerees} lignes)
                                </option>
                            ))}
                        </select>
                    )}
                </div>
            )}

            {/* Message si fichier sans run (seulement en sous-mode « brut ») */}
            {mode === 'fichier' &&
                sousMode === 'brut' &&
                idFichier !== null &&
                !hasRuns && (
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
                        Ce fichier n'a pas encore été ingéré. Lancez un run depuis
                        la page « Fichiers » pour voir ses points sur la carte.
                    </div>
                )}

            {/* Message si fichier sans ouvrages (sous-mode « ouvrages ») */}
            {mode === 'fichier' &&
                sousMode === 'ouvrages' &&
                idFichier !== null &&
                !isLoading &&
                pointCount === 0 && (
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
                        Aucun ouvrage consolidé pour ce fichier. Vérifiez que le
                        pipeline (ingestion → rapprochement → consolidation) a bien
                        été exécuté.
                    </div>
                )}

            {/* Filtres : visibles en mode Tous, ou en mode Fichier + brut */}
            {showFilters && (
                <FiltersPanel
                    filters={filters}
                    onChange={setFilters}
                    showGeographic={true}
                />
            )}

            <MapView
                data={cartoData ?? null}
                height="calc(100vh - 380px)"
                mode={mode}
                sousMode={sousMode}
            />

            {/* Légende conditionnelle */}
            <div className="flex items-center gap-4 text-sm text-gray-600 flex-wrap">
                <span className="font-medium">Légende :</span>
                {mode === 'tous' || sousMode === 'ouvrages' ? (
                    <>
                        <span className="text-xs text-gray-500 mr-2">
                            Couleur = Alimentation, forme = Nature
                        </span>
                        {Object.entries({
                            PMH: '#2563eb',
                            HVA: '#16a34a',
                            PEA: '#ea580c',
                            HV: '#9333ea',
                            AUTRE: '#6b7280',
                        }).map(([type, color]) => (
                            <span key={type} className="flex items-center gap-1.5">
                                <span
                                    className="inline-block w-3 h-3 rounded-full border border-white"
                                    style={{ backgroundColor: color }}
                                />
                                {type}
                            </span>
                        ))}
                    </>
                ) : (
                    <>
                        <span className="text-xs text-gray-500 mr-2">
                            Couleur = Qualité (statut de la ligne)
                        </span>
                        {Object.entries({
                            ok: '#16a34a',
                            localite_non_resolue: '#f59e0b',
                            geom_invalide: '#dc2626',
                            type_ouvrage_inconnu: '#9333ea',
                            doublon_suspect: '#eab308',
                        }).map(([statut, color]) => (
                            <span
                                key={statut}
                                className="flex items-center gap-1.5"
                            >
                                <span
                                    className="inline-block w-3 h-3 rounded-full border border-white"
                                    style={{ backgroundColor: color }}
                                />
                                {statut}
                            </span>
                        ))}
                    </>
                )}
            </div>
        </div>
    )
}