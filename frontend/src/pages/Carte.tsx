import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Map as MapIcon, Layers } from 'lucide-react'
import { api, type FeatureCollection } from '@/lib/api'
import { MapView } from '@/components/MapView'
import { Button } from '@/components/ui/button'

type Mode = 'tous' | 'fichier'

export default function Carte() {
    const [mode, setMode] = useState<Mode>('tous')
    const [idFichier, setIdFichier] = useState<number | null>(null)
    const [idFeuille, setIdFeuille] = useState<number | null>(null)

    // Liste des fichiers (pour le sélecteur)
    const { data: fichiers } = useQuery({
        queryKey: ['fichiers'],
        queryFn: () => api.fichiers({ limit: 100 }),
    })

    // Feuilles du fichier sélectionné
    const { data: feuilles } = useQuery({
        queryKey: ['feuilles', idFichier],
        queryFn: () => api.feuilles(idFichier!),
        enabled: idFichier !== null,
    })

    // Données carto
    const { data: cartoData, isLoading } = useQuery<FeatureCollection>({
        queryKey: ['carto', mode, idFichier, idFeuille],
        queryFn: () => {
            if (mode === 'tous') return api.cartoTous()
            if (idFichier === null) return Promise.resolve({ type: 'FeatureCollection', features: [], meta: { count: 0 } })
            const params: Record<string, string | number> = {}
            if (idFeuille !== null) params.id_feuille = idFeuille
            return api.cartoFichier(idFichier, params)
        },
        enabled: mode === 'tous' || idFichier !== null,
    })

    // Reset la feuille si on change de fichier
    useEffect(() => {
        setIdFeuille(null)
    }, [idFichier])

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Carte</h2>
                    <p className="text-sm text-gray-500">
                        {isLoading
                            ? 'Chargement...'
                            : `${cartoData?.features.length ?? 0} point(s) affiché(s)`}
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        variant={mode === 'tous' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => { setMode('tous'); setIdFichier(null); setIdFeuille(null) }}
                    >
                        <Layers className="w-4 h-4 mr-1" />
                        Tous les ouvrages
                    </Button>
                    <Button
                        variant={mode === 'fichier' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setMode('fichier')}
                    >
                        <MapIcon className="w-4 h-4 mr-1" />
                        Par fichier
                    </Button>
                </div>
            </div>

            {/* Sélecteurs (si mode fichier) */}
            {mode === 'fichier' && (
                <div className="flex gap-3 items-center flex-wrap">
                    <div className="flex items-center gap-2">
                        <label className="text-sm font-medium">Fichier :</label>
                        <select
                            value={idFichier ?? ''}
                            onChange={(e) => setIdFichier(e.target.value ? Number(e.target.value) : null)}
                            className="h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-sm"
                        >
                            <option value="">— Sélectionner —</option>
                            {fichiers?.data.map((f) => (
                                <option key={f.id_fichier} value={f.id_fichier}>
                                    {f.nom_fichier_original} ({f.source.nom})
                                </option>
                            ))}
                        </select>
                    </div>

                    {idFichier !== null && feuilles && feuilles.data.length > 0 && (
                        <div className="flex items-center gap-2">
                            <label className="text-sm font-medium">Feuille :</label>
                            <select
                                value={idFeuille ?? ''}
                                onChange={(e) => setIdFeuille(e.target.value ? Number(e.target.value) : null)}
                                className="h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-sm"
                            >
                                <option value="">Toutes les feuilles</option>
                                {feuilles.data.map((fe) => (
                                    <option key={fe.id_feuille} value={fe.id_feuille}>
                                        {fe.nom_feuille} ({fe.nb_lignes} lignes)
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}
                </div>
            )}

            {/* Carte */}
            <MapView data={cartoData ?? null} height="calc(100vh - 240px)" />

            {/* Légende */}
            <div className="flex items-center gap-4 text-sm text-gray-600 flex-wrap">
                <span className="font-medium">Légende :</span>
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
            </div>
        </div>
    )
}