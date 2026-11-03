import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Upload } from 'lucide-react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog } from '@/components/ui/dialog'

interface Props {
    open: boolean
    onClose: () => void
    onSuccess: (idFichier: number) => void
}

export function UploadDialog({ open, onClose, onSuccess }: Props) {
    const [file, setFile] = useState<File | null>(null)
    const [idSource, setIdSource] = useState(1)
    const [commentaire, setCommentaire] = useState('')
    const [loading, setLoading] = useState(false)

    const { data: sourcesData } = useQuery({
        queryKey: ['sources'],
        queryFn: () => api.sources(),
        enabled: open,
    })

    const handleSubmit = async () => {
        if (!file) {
            toast.error('Sélectionnez un fichier')
            return
        }
        setLoading(true)
        try {
            const res = await api.upload(file, idSource, commentaire || undefined)
            toast.success(`Fichier uploadé : ${res.feuilles_detectees.length} feuilles détectées`)
            onSuccess(res.id_fichier)
            onClose()
            setFile(null)
            setCommentaire('')
        } catch (e: any) {
            toast.error(e.message || 'Erreur upload')
        } finally {
            setLoading(false)
        }
    }

    return (
        <Dialog open={open} onClose={onClose} title="Uploader un fichier">
            <div className="space-y-4">
                <div>
                    <label className="block text-sm font-medium mb-1">Fichier Excel</label>
                    <input
                        type="file"
                        accept=".xlsx,.xls"
                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                        className="block w-full text-sm text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                    {file && <p className="text-xs text-gray-500 mt-1">{file.name} ({(file.size / 1024).toFixed(1)} Ko)</p>}
                </div>

                <div>
                    <label className="block text-sm font-medium mb-1">Source</label>
                    <select
                        value={idSource}
                        onChange={(e) => setIdSource(Number(e.target.value))}
                        className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                    >
                        {sourcesData?.data.map((s) => (
                            <option key={s.id_source} value={s.id_source}>
                                {s.nom} ({s.type_source})
                            </option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium mb-1">Commentaire (optionnel)</label>
                    <Input
                        value={commentaire}
                        onChange={(e) => setCommentaire(e.target.value)}
                        placeholder="Ex. Fichier ONEP 2024"
                    />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                    <Button variant="outline" onClick={onClose} disabled={loading}>
                        Annuler
                    </Button>
                    <Button onClick={handleSubmit} disabled={loading || !file}>
                        <Upload className="w-4 h-4 mr-2" />
                        {loading ? 'Upload...' : 'Uploader'}
                    </Button>
                </div>
            </div>
        </Dialog>
    )
}