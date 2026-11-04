import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Map as MapIcon, Layers } from 'lucide-react'
import { api, type FeatureCollection } from '@/lib/api'
import { MapView } from '@/components/MapView'
import { Button } from '@/components/ui/button'
import { FiltersPanel, type Filters } from '@/components/FiltersPanel'

const EMPTY_FILTERS: Filters = {
    region: '', departement: '', sous_prefecture: '', localite: '',
    type_ouvrage: '', etat: '', annee_min: '', annee_max: '',
}

type Mode = 'tous' | 'fichier'

export default function Carte() {
    const [mode, setMode] = useState<Mode>('tous')
    const [idFichier, setIdFichier] = useState<number | null>(null)
    const [idFeuille, setIdFeuille] = useState<number | null>(null)
    const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS)

    const { data: fichiers } = useQuery({ queryKey: ['fichiers'], queryFn: () => api.fichiers({ limit: 100 }) })
    const { data: feuilles } = useQuery({
        queryKey: ['feuilles', idFichier],
        queryFn: () => api.feuilles(idFichier!),
        enabled: idFichier !== null,
    })

    const { data: cartoData, isLoading } = useQuery<FeatureCollection>({
        queryKey: ['carto', mode, idFichier, idFeuille, filters],
        queryFn: () => {
            if (mode === 'tous') {
                const params: Record<string, string | number> = {}
                for (const [k, v] of Object.entries(filters)) {
                    if (v) params[k] = v
                }
                return api.cartoTous(params)
            }
            if (idFichier === null) return Promise.resolve({ type: 'FeatureCollection', features: [], meta: { count: 0 } })
            const params: Record<string, string | number> = {}
            if (idFeuille !== null) params.id_feuille = idFeuille
            return api.cartoFichier(idFichier, params)
        },
        enabled: mode === 'tous' || idFichier !== null,
    })

    useEffect(() => { setIdFeuille(null) }, [idFichier])

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Carte</h2>
                    <p className="text-sm text-gray-500">
                        {isLoading ? 'Chargement...' : `${cartoData?.features.length ?? 0} point(s) affiché(s)`}
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <Button variant={mode === 'tous' ? 'default' : 'outline'} size="sm" onClick={() => { setMode('tous'); setIdFichier(null) }}>
                        <Layers className="w-4 h-4 mr-1" /> Tous
                    </Button>
                    <Button variant={mode === 'fichier' ? 'default' : 'outline'} size="sm" onClick={() => setMode('fichier')}>
                        <MapIcon className="w-4 h-4 mr-1" /> Par fichier
                    </Button>
                </div>
            </div>

            {mode === 'tous' && (
                <FiltersPanel filters={filters} onChange={setFilters} showGeographic={true} />
            )}

            {mode === 'fichier' && (
                <div className="flex gap-3 items-center flex-wrap">
                    <select
                        value={idFichier ?? ''}
                        onChange={(e) => setIdFichier(e.target.value ? Number(e.target.value) : null)}
                        className="h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-sm"
                    >
                        <option value="">— Fichier —</option>
                        {fichiers?.data.map((f) => (
                            <option key={f.id_fichier} value={f.id_fichier}>{f.nom_fichier_original}</option>
                        ))}
                    </select>
                    {idFichier !== null && (
                        <select
                            value={idFeuille ?? ''}
                            onChange={(e) => setIdFeuille(e.target.value ? Number(e.target.value) : null)}
                            className="h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-sm"
                        >
                            <option value="">Toutes les feuilles</option>
                            {feuilles?.data.map((fe) => (
                                <option key={fe.id_feuille} value={fe.id_feuille}>{fe.nom_feuille}</option>
                            ))}
                        </select>
                    )}
                </div>
            )}

            <MapView data={cartoData ?? null} height="calc(100vh - 320px)" />

            {/* Légende */}
            <div className="flex items-center gap-4 text-sm text-gray-600 flex-wrap">
                <span className="font-medium">Légende :</span>
                {Object.entries({ PMH: '#2563eb', HVA: '#16a34a', PEA: '#ea580c', HV: '#9333ea', AUTRE: '#6b7280' }).map(([type, color]) => (
                    <span key={type} className="flex items-center gap-1.5">
            <span className="inline-block w-3 h-3 rounded-full border border-white" style={{ backgroundColor: color }} />
                        {type}
          </span>
                ))}
            </div>
        </div>
    )
}