import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
    Activity,
    CheckCircle2,
    AlertTriangle,
    XCircle,
    Eye,
    X,
    ChevronRight,
    RotateCcw,
} from 'lucide-react'
import { api, type LigneIngeree } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const STATUT_LABELS: Record<
    string,
    { label: string; color: string; bg: string }
> = {
    ok: {
        label: 'Valides (OK)',
        color: 'text-green-700',
        bg: 'bg-green-50 border-green-200',
    },
    localite_non_resolue: {
        label: 'Localité non résolue',
        color: 'text-amber-700',
        bg: 'bg-amber-50 border-amber-200',
    },
    geom_invalide: {
        label: 'Géométrie invalide',
        color: 'text-red-700',
        bg: 'bg-red-50 border-red-200',
    },
    type_ouvrage_inconnu: {
        label: 'Type ouvrage inconnu',
        color: 'text-purple-700',
        bg: 'bg-purple-50 border-purple-200',
    },
    doublon_suspect: {
        label: 'Doublon suspect',
        color: 'text-orange-700',
        bg: 'bg-orange-50 border-orange-200',
    },
    rejete: {
        label: 'Lignes rejetées',
        color: 'text-gray-700',
        bg: 'bg-gray-100 border-gray-200',
    },
}

export default function Qualite() {
    const [idFichier, setIdFichier] = useState<number | null>(null)
    const [statutFilter, setStatutFilter] = useState<string>('localite_non_resolue')
    const [cursor, setCursor] = useState<string | null>(null)
    const [selectedLigneId, setSelectedLigneId] = useState<number | null>(null)

    const { data: fichiers } = useQuery({
        queryKey: ['fichiers'],
        queryFn: () => api.fichiers({ limit: 100 }),
    })

    // Sélectionne automatiquement le premier fichier disponible
    useEffect(() => {
        if (idFichier === null && fichiers?.data && fichiers.data.length > 0) {
            setIdFichier(fichiers.data[0].id_fichier)
        }
    }, [fichiers, idFichier])

    const { data: qualiteData, isLoading: loadingQualite } = useQuery({
        queryKey: ['qualite', idFichier],
        queryFn: () => api.qualite(idFichier!),
        enabled: idFichier !== null,
    })

    // Récupère le dernier run du fichier pour lister les lignes
    const { data: runsData } = useQuery({
        queryKey: ['runs', idFichier],
        queryFn: () => api.runsFichier(idFichier!),
        enabled: idFichier !== null,
    })

    const lastRunId = runsData?.data?.[0]?.id_run ?? null

    const {
        data: lignesData,
        isLoading: loadingLignes,
        isFetching: fetchingLignes,
    } = useQuery({
        queryKey: ['run-lignes', lastRunId, statutFilter, cursor],
        queryFn: () =>
            api.lignesRun(lastRunId!, {
                statut_qualite: statutFilter || undefined,
                cursor: cursor || undefined,
                limit: 30,
            }),
        enabled: lastRunId !== null && statutFilter !== 'rejete',
    })

    const { data: detailLigne } = useQuery({
        queryKey: ['ligne-detail', selectedLigneId],
        queryFn: () => api.ligne(selectedLigneId!, true),
        enabled: selectedLigneId !== null,
    })

    const tauxPct = qualiteData
        ? Math.round(qualiteData.taux_reussite * 1000) / 10
        : 0

    return (
        <div className="space-y-6">
            {/* En-tête + sélecteur de fichier */}
            <div className="flex items-center justify-between flex-wrap gap-3">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">
                        Tableau de bord Qualité
                    </h2>
                    <p className="text-sm text-gray-500">
                        Suivi de la résolution géographique, des géométries et des
                        anomalies d'ingestion
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    <label className="text-sm font-medium text-gray-700">Fichier :</label>
                    <select
                        value={idFichier ?? ''}
                        onChange={(e) => {
                            setIdFichier(e.target.value ? Number(e.target.value) : null)
                            setCursor(null)
                        }}
                        className="h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-sm min-w-[240px]"
                    >
                        <option value="">— Choisir un fichier —</option>
                        {fichiers?.data.map((f) => (
                            <option key={f.id_fichier} value={f.id_fichier}>
                                {f.nom_fichier_original} ({f.statut})
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {loadingQualite && (
                <p className="text-gray-500">Chargement des métriques qualité...</p>
            )}

            {qualiteData && (
                <>
                    {/* Bandeau synthèse + barre de progression */}
                    <div className="bg-white border rounded-lg p-5 space-y-4">
                        <div className="flex items-center justify-between flex-wrap gap-4">
                            <div className="flex items-center gap-3">
                                <Activity className="w-6 h-6 text-blue-600" />
                                <div>
                                    <h3 className="font-semibold text-gray-900">
                                        {qualiteData.nom_fichier}
                                    </h3>
                                    <p className="text-xs text-gray-500">
                                        Source : {qualiteData.source} •{' '}
                                        {qualiteData.nb_lignes_total} lignes totales dans le
                                        fichier
                                    </p>
                                </div>
                            </div>

                            <div className="text-right">
                                <div className="text-2xl font-bold text-gray-900">
                                    {tauxPct} %
                                </div>
                                <div className="text-xs text-gray-500">Taux de réussite</div>
                            </div>
                        </div>

                        <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
                            <div
                                className={`h-full transition-all ${
                                    tauxPct >= 80
                                        ? 'bg-green-500'
                                        : tauxPct >= 50
                                            ? 'bg-amber-500'
                                            : 'bg-red-500'
                                }`}
                                style={{ width: `${Math.min(100, tauxPct)}%` }}
                            />
                        </div>
                    </div>

                    {/* Grille des 6 compteurs (cliquables pour filtrer le tableau ci-dessous) */}
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                        {Object.entries(STATUT_LABELS).map(([key, meta]) => {
                            const count =
                                qualiteData.qualite[
                                    key as keyof typeof qualiteData.qualite
                                    ] ?? 0
                            const isSelected = statutFilter === key
                            return (
                                <button
                                    key={key}
                                    onClick={() => {
                                        setStatutFilter(key)
                                        setCursor(null)
                                    }}
                                    className={`text-left border rounded-lg p-3 transition ${meta.bg} ${
                                        isSelected ? 'ring-2 ring-blue-600' : 'hover:opacity-90'
                                    }`}
                                >
                                    <div className={`text-xl font-bold ${meta.color}`}>
                                        {count}
                                    </div>
                                    <div className="text-xs font-medium text-gray-700 mt-1">
                                        {meta.label}
                                    </div>
                                </button>
                            )
                        })}
                    </div>

                    {/* Tableau des lignes du dernier run filtrées par statut */}
                    {lastRunId !== null && (
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <h3 className="font-semibold text-gray-900">
                                    Détail des lignes —{' '}
                                    {STATUT_LABELS[statutFilter]?.label ?? statutFilter} (Run #
                                    {lastRunId})
                                </h3>
                            </div>

                            {statutFilter === 'rejete' ? (
                                <div className="bg-gray-50 border rounded-lg p-6 text-center text-sm text-gray-500">
                                    Les lignes rejetées (totaux, sous-totaux ou lignes vides)
                                    sont écartées avant stockage en base.
                                </div>
                            ) : (
                                <>
                                    <div className="bg-white border rounded-lg overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead className="bg-gray-50 border-b">
                                            <tr>
                                                <th className="text-left px-4 py-3 font-medium text-gray-700">
                                                    Ligne Excel
                                                </th>
                                                <th className="text-left px-4 py-3 font-medium text-gray-700">
                                                    Localité brute
                                                </th>
                                                <th className="text-left px-4 py-3 font-medium text-gray-700">
                                                    Type brut
                                                </th>
                                                <th className="text-left px-4 py-3 font-medium text-gray-700">
                                                    Coordonnées
                                                </th>
                                                <th className="text-left px-4 py-3 font-medium text-gray-700">
                                                    Diagnostic
                                                </th>
                                                <th className="text-right px-4 py-3 font-medium text-gray-700">
                                                    Brut
                                                </th>
                                            </tr>
                                            </thead>
                                            <tbody>
                                            {loadingLignes && (
                                                <tr>
                                                    <td
                                                        colSpan={6}
                                                        className="px-4 py-8 text-center text-gray-500"
                                                    >
                                                        Chargement des lignes...
                                                    </td>
                                                </tr>
                                            )}

                                            {!loadingLignes &&
                                                lignesData?.data.length === 0 && (
                                                    <tr>
                                                        <td
                                                            colSpan={6}
                                                            className="px-4 py-8 text-center text-gray-500"
                                                        >
                                                            Aucune ligne dans cette
                                                            catégorie.
                                                        </td>
                                                    </tr>
                                                )}

                                            {lignesData?.data.map(
                                                (lig: LigneIngeree) => (
                                                    <tr
                                                        key={lig.id_ligne}
                                                        className="border-b hover:bg-gray-50"
                                                    >
                                                        <td className="px-4 py-3 font-mono text-gray-900">
                                                            #{lig.num_ligne_source}
                                                        </td>
                                                        <td className="px-4 py-3 text-gray-800">
                                                            {lig.localite_brute || '—'}
                                                        </td>
                                                        <td className="px-4 py-3 text-gray-700">
                                                            {lig.type_ouvrage_brut || '—'}
                                                        </td>
                                                        <td className="px-4 py-3 font-mono text-xs text-gray-700">
                                                            {lig.latitude_decimal !== null &&
                                                            lig.longitude_decimal !== null
                                                                ? `${lig.latitude_decimal.toFixed(4)}, ${lig.longitude_decimal.toFixed(4)}`
                                                                : 'Manquantes'}
                                                        </td>
                                                        <td className="px-4 py-3 text-gray-600 max-w-xs truncate">
                                                            {lig.message_qualite || '—'}
                                                        </td>
                                                        <td className="px-4 py-3 text-right">
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                onClick={() =>
                                                                    setSelectedLigneId(lig.id_ligne)
                                                                }
                                                            >
                                                                <Eye className="w-4 h-4" />
                                                            </Button>
                                                        </td>
                                                    </tr>
                                                )
                                            )}
                                            </tbody>
                                        </table>
                                    </div>

                                    {/* Pagination */}
                                    <div className="flex items-center justify-between">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            disabled={!cursor || fetchingLignes}
                                            onClick={() => setCursor(null)}
                                        >
                                            <RotateCcw className="w-4 h-4 mr-1.5" />
                                            Début
                                        </Button>

                                        <Button
                                            variant="outline"
                                            size="sm"
                                            disabled={
                                                !lignesData?.pagination.has_more ||
                                                !lignesData?.pagination.next_cursor ||
                                                fetchingLignes
                                            }
                                            onClick={() =>
                                                setCursor(
                                                    lignesData?.pagination.next_cursor ?? null
                                                )
                                            }
                                        >
                                            Page suivante
                                            <ChevronRight className="w-4 h-4 ml-1.5" />
                                        </Button>
                                    </div>
                                </>
                            )}
                        </div>
                    )}
                </>
            )}

            {/* Modale données brutes Excel d'une ligne */}
            {selectedLigneId !== null && detailLigne && (
                <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
                    <div className="bg-white rounded-lg max-w-3xl w-full max-h-[85vh] overflow-y-auto p-6 space-y-4 shadow-xl">
                        <div className="flex items-center justify-between border-b pb-3">
                            <div className="flex items-center gap-3">
                                <h3 className="text-lg font-bold text-gray-900">
                                    Ligne Excel #{detailLigne.num_ligne_source}
                                </h3>
                                <Badge status={detailLigne.statut_qualite}>
                                    {detailLigne.statut_qualite}
                                </Badge>
                            </div>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setSelectedLigneId(null)}
                            >
                                <X className="w-4 h-4" />
                            </Button>
                        </div>

                        {detailLigne.message_qualite && (
                            <div className="bg-amber-50 border border-amber-200 rounded p-3 text-sm text-amber-800">
                                {detailLigne.message_qualite}
                            </div>
                        )}

                        {detailLigne.donnees_brutes && (
                            <section>
                                <h4 className="font-semibold text-gray-900 mb-2">
                                    Données brutes (Excel)
                                </h4>
                                <dl className="grid grid-cols-[200px_1fr] gap-y-1 text-xs">
                                    {Object.entries(detailLigne.donnees_brutes).map(
                                        ([k, v]) => (
                                            <div key={k} className="contents">
                                                <dt
                                                    className="text-gray-500 truncate font-mono"
                                                    title={k}
                                                >
                                                    {k}
                                                </dt>
                                                <dd
                                                    className="text-gray-800 break-words"
                                                    title={v !== null ? String(v) : '—'}
                                                >
                                                    {v !== null ? String(v) : '—'}
                                                </dd>
                                            </div>
                                        )
                                    )}
                                </dl>
                            </section>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}