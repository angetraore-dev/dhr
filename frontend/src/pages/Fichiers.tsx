import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { Upload, Play, FileSpreadsheet } from 'lucide-react'
import { api, type Fichier } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { UploadDialog } from '@/components/UploadDialog'
import { RunStatus } from '@/components/RunStatus'

export default function Fichiers() {
    const queryClient = useQueryClient()
    const [uploadOpen, setUploadOpen] = useState(false)
    const [runsActifs, setRunsActifs] = useState<Record<number, number>>({})

    const { data, isLoading } = useQuery({
        queryKey: ['fichiers'],
        queryFn: () => api.fichiers(),
    })

    const lancerRunMutation = useMutation({
        mutationFn: (idFichier: number) => api.lancerRun(idFichier, 'complet'),
        onSuccess: (res, idFichier) => {
            toast.success(`Run ${res.id_run} lancé pour le fichier ${idFichier}`)
            setRunsActifs((prev) => ({ ...prev, [idFichier]: res.id_run }))
        },
        onError: (e: any) => toast.error(e.message || 'Erreur lancement run'),
    })

    const handleRunDone = (idFichier: number) => {
        queryClient.invalidateQueries({ queryKey: ['fichiers'] })
        setRunsActifs((prev) => {
            const copy = { ...prev }
            delete copy[idFichier]
            return copy
        })
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Fichiers</h2>
                    <p className="text-sm text-gray-500">
                        {data?.pagination.total ?? 0} fichier(s) enregistré(s)
                    </p>
                </div>
                <Button onClick={() => setUploadOpen(true)}>
                    <Upload className="w-4 h-4 mr-2" />
                    Uploader un fichier
                </Button>
            </div>

            {isLoading && <p className="text-gray-500">Chargement...</p>}

            {!isLoading && data?.data.length === 0 && (
                <div className="border-2 border-dashed rounded-lg p-12 text-center">
                    <FileSpreadsheet className="w-12 h-12 mx-auto text-gray-300 mb-3" />
                    <p className="text-gray-500">Aucun fichier. Uploadez votre premier fichier.</p>
                </div>
            )}

            {data && data.data.length > 0 && (
                <div className="bg-white border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                        <thead className="bg-gray-50 border-b">
                        <tr>
                            <th className="text-left px-4 py-3 font-medium text-gray-700">Nom</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-700">Source</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-700">Statut</th>
                            <th className="text-right px-4 py-3 font-medium text-gray-700">Lignes</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-700">Date réception</th>
                            <th className="text-right px-4 py-3 font-medium text-gray-700">Actions</th>
                        </tr>
                        </thead>
                        <tbody>
                        {data.data.map((f) => (
                            <tr key={f.id_fichier} className="border-b hover:bg-gray-50">
                                <td className="px-4 py-3">
                                    <div className="font-medium text-gray-900">{f.nom_fichier_original}</div>
                                    {f.commentaire && <div className="text-xs text-gray-500">{f.commentaire}</div>}
                                </td>
                                <td className="px-4 py-3 text-gray-700">{f.source.nom}</td>
                                <td className="px-4 py-3">
                                    <Badge status={f.statut}>{f.statut}</Badge>
                                    {runsActifs[f.id_fichier] && (
                                        <div className="mt-1">
                                            <RunStatus
                                                idRun={runsActifs[f.id_fichier]}
                                                onDone={() => handleRunDone(f.id_fichier)}
                                            />
                                        </div>
                                    )}
                                </td>
                                <td className="px-4 py-3 text-right text-gray-700">{f.nb_lignes_total}</td>
                                <td className="px-4 py-3 text-gray-500 text-xs">
                                    {new Date(f.date_reception).toLocaleString('fr-FR')}
                                </td>
                                <td className="px-4 py-3 text-right space-x-2">
                                    <Link to={`/fichiers/${f.id_fichier}/mapping`}>
                                        <Button variant="outline" size="sm">Mapping</Button>
                                    </Link>
                                    <Button
                                        size="sm"
                                        onClick={() => lancerRunMutation.mutate(f.id_fichier)}
                                        disabled={lancerRunMutation.isPending || !!runsActifs[f.id_fichier]}
                                    >
                                        <Play className="w-3 h-3 mr-1" />
                                        Run
                                    </Button>
                                </td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>
            )}

            <UploadDialog
                open={uploadOpen}
                onClose={() => setUploadOpen(false)}
                onSuccess={(idFichier) => {
                    queryClient.invalidateQueries({ queryKey: ['fichiers'] })
                    toast.success(`Fichier ${idFichier} uploadé`)
                }}
            />
        </div>
    )
}