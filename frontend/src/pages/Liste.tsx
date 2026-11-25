import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Download, Eye, ChevronRight, RotateCcw, X } from 'lucide-react'
import { api, type Ouvrage } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { FiltersPanel } from '@/components/FiltersPanel'
import { EMPTY_FILTERS, type Filters } from '@/lib/filters'

export default function Liste() {
    const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS)
    const [cursor, setCursor] = useState<string | null>(null)
    const [selectedOuvrageId, setSelectedOuvrageId] = useState<number | null>(null)
    const [exporting, setExporting] = useState<'xlsx' | 'csv' | null>(null)

    const buildParams = (includeCursor = true): Record<string, string | number> => {
        const params: Record<string, string | number> = { limit: 50 }
        for (const [k, v] of Object.entries(filters)) {
            if (v) params[k] = v
        }
        if (includeCursor && cursor) {
            params.cursor = cursor
        }
        return params
    }

    const { data, isLoading, isFetching } = useQuery({
        queryKey: ['ouvrages', filters, cursor],
        queryFn: () => api.ouvrages(buildParams(true)),
    })

    const { data: detailOuvrage, isLoading: loadingDetail } = useQuery({
        queryKey: ['ouvrage-detail', selectedOuvrageId],
        queryFn: () => api.ouvrage(selectedOuvrageId!, true),
        enabled: selectedOuvrageId !== null,
    })

    const handleFiltersChange = (next: Filters) => {
        setFilters(next)
        setCursor(null)
    }

    const handleExport = async (format: 'xlsx' | 'csv') => {
        try {
            setExporting(format)
            const params: Record<string, string | number> = {}
            for (const [k, v] of Object.entries(filters)) {
                if (v) params[k] = v
            }
            await api.exportOuvrages(format, params)
            toast.success(`Export ${format.toUpperCase()} téléchargé`)
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : "Erreur lors de l'export"
            toast.error(msg)
        } finally {
            setExporting(null)
        }
    }

    return (
        <div className="space-y-4">
            {/* En-tête + boutons export */}
            <div className="flex items-center justify-between flex-wrap gap-3">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Ouvrages consolidés</h2>
                    <p className="text-sm text-gray-500">
                        {isLoading
                            ? 'Chargement...'
                            : `${data?.data.length ?? 0} ouvrage(s) affiché(s) sur cette page`}
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        disabled={exporting !== null}
                        onClick={() => handleExport('csv')}
                    >
                        <Download className="w-4 h-4 mr-1.5" />
                        {exporting === 'csv' ? 'Export CSV...' : 'Exporter CSV'}
                    </Button>
                    <Button
                        size="sm"
                        disabled={exporting !== null}
                        onClick={() => handleExport('xlsx')}
                    >
                        <Download className="w-4 h-4 mr-1.5" />
                        {exporting === 'xlsx' ? 'Export Excel...' : 'Exporter Excel'}
                    </Button>
                </div>
            </div>

            {/* Filtres */}
            <FiltersPanel
                filters={filters}
                onChange={handleFiltersChange}
                showGeographic={true}
            />

            {/* Tableau */}
            <div className="bg-white border rounded-lg overflow-x-auto">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b">
                    <tr>
                        <th className="text-left px-4 py-3 font-medium text-gray-700">ID / Code</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-700">Région</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-700">Département</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-700">Sous-préfecture</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-700">Localité</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-700">Nature</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-700">Alimentation</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-700">Réalisation</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-700">État</th>
                        <th className="text-right px-4 py-3 font-medium text-gray-700">Année</th>
                        <th className="text-right px-4 py-3 font-medium text-gray-700">Détail</th>
                    </tr>
                    </thead>
                    <tbody>
                    {isLoading && (
                        <tr>
                            <td colSpan={11} className="px-4 py-8 text-center text-gray-500">
                                Chargement des ouvrages...
                            </td>
                        </tr>
                    )}

                    {!isLoading && data?.data.length === 0 && (
                        <tr>
                            <td colSpan={11} className="px-4 py-8 text-center text-gray-500">
                                Aucun ouvrage trouvé pour ces critères.
                            </td>
                        </tr>
                    )}

                    {data?.data.map((o: Ouvrage) => (
                        <tr key={o.id_ouvrage} className="border-b hover:bg-gray-50">
                            <td className="px-4 py-3">
                                <div className="font-medium text-gray-900">#{o.id_ouvrage}</div>
                                {o.code_ouvrage && (
                                    <div className="text-xs font-mono text-gray-500">
                                        {o.code_ouvrage}
                                    </div>
                                )}
                            </td>
                            <td className="px-4 py-3 text-gray-700">{o.region || '—'}</td>
                            <td className="px-4 py-3 text-gray-700">{o.departement || '—'}</td>
                            <td className="px-4 py-3 text-gray-700">{o.sous_prefecture || '—'}</td>
                            <td className="px-4 py-3 font-medium text-gray-800">
                                {o.localite.nom_usage}
                            </td>
                            <td className="px-4 py-3 capitalize text-gray-700">
                                {o.nature_ouvrage || '—'}
                            </td>
                            <td className="px-4 py-3">
                                    <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-xs font-medium">
                                        {o.type_alimentation || 'AUTRE'}
                                    </span>
                            </td>
                            <td className="px-4 py-3 capitalize text-gray-700">
                                {o.realisation_par || '—'}
                            </td>
                            <td className="px-4 py-3">
                                <Badge status={o.etat}>{o.etat}</Badge>
                            </td>
                            <td className="px-4 py-3 text-right text-gray-700">
                                {o.annee_realisation || '—'}
                            </td>
                            <td className="px-4 py-3 text-right">
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setSelectedOuvrageId(o.id_ouvrage)}
                                >
                                    <Eye className="w-4 h-4" />
                                </Button>
                            </td>
                        </tr>
                    ))}
                    </tbody>
                </table>
            </div>

            {/* Pagination par curseur */}
            <div className="flex items-center justify-between">
                <Button
                    variant="outline"
                    size="sm"
                    disabled={!cursor || isFetching}
                    onClick={() => setCursor(null)}
                >
                    <RotateCcw className="w-4 h-4 mr-1.5" />
                    Début de liste
                </Button>

                <Button
                    variant="outline"
                    size="sm"
                    disabled={
                        !data?.pagination.has_more ||
                        !data?.pagination.next_cursor ||
                        isFetching
                    }
                    onClick={() => setCursor(data?.pagination.next_cursor ?? null)}
                >
                    Page suivante
                    <ChevronRight className="w-4 h-4 ml-1.5" />
                </Button>
            </div>

            {/* Modale détail ouvrage */}
            {selectedOuvrageId !== null && (
                <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
                    <div className="bg-white rounded-lg max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6 space-y-4 shadow-xl">
                        <div className="flex items-center justify-between border-b pb-3">
                            <h3 className="text-lg font-bold text-gray-900">
                                Ouvrage #{selectedOuvrageId}
                                {detailOuvrage?.code_ouvrage
                                    ? ` — ${detailOuvrage.code_ouvrage}`
                                    : ''}
                            </h3>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setSelectedOuvrageId(null)}
                            >
                                <X className="w-4 h-4" />
                            </Button>
                        </div>

                        {loadingDetail && (
                            <p className="text-sm text-gray-500">
                                Chargement des détails...
                            </p>
                        )}

                        {detailOuvrage && (
                            <div className="space-y-3 text-sm">
                                <dl className="grid grid-cols-[140px_1fr] gap-y-2">
                                    <dt className="text-gray-500">Région</dt>
                                    <dd className="font-medium text-gray-900">
                                        {detailOuvrage.region || '—'}
                                    </dd>

                                    <dt className="text-gray-500">Département</dt>
                                    <dd className="font-medium text-gray-900">
                                        {detailOuvrage.departement || '—'}
                                    </dd>

                                    <dt className="text-gray-500">Sous-préfecture</dt>
                                    <dd className="font-medium text-gray-900">
                                        {detailOuvrage.sous_prefecture || '—'}
                                    </dd>

                                    <dt className="text-gray-500">Localité</dt>
                                    <dd className="font-medium text-gray-900">
                                        {detailOuvrage.localite.nom_usage}
                                    </dd>

                                    <dt className="text-gray-500">État</dt>
                                    <dd>
                                        <Badge status={detailOuvrage.etat}>
                                            {detailOuvrage.etat}
                                        </Badge>
                                    </dd>

                                    <dt className="text-gray-500">Nature</dt>
                                    <dd className="capitalize">
                                        {detailOuvrage.nature_ouvrage || '—'}
                                    </dd>

                                    <dt className="text-gray-500">Alimentation</dt>
                                    <dd>{detailOuvrage.type_alimentation || '—'}</dd>

                                    <dt className="text-gray-500">Réalisation</dt>
                                    <dd className="capitalize">
                                        {detailOuvrage.realisation_par || '—'}
                                    </dd>

                                    <dt className="text-gray-500">Année</dt>
                                    <dd>{detailOuvrage.annee_realisation || '—'}</dd>
                                </dl>

                                {detailOuvrage.geom && (
                                    <section className="pt-3 border-t">
                                        <h4 className="font-semibold text-gray-900 mb-1">
                                            Coordonnées GPS
                                        </h4>
                                        <p className="font-mono text-xs text-gray-700">
                                            {detailOuvrage.geom.coordinates[1].toFixed(6)},{' '}
                                            {detailOuvrage.geom.coordinates[0].toFixed(6)}
                                        </p>
                                    </section>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}