import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Save, ChevronLeft, CheckCircle2, Tag } from 'lucide-react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const CHAMPS_STANDARDS = [
    { value: 'region_brute', label: 'Région' },
    { value: 'departement_brute', label: 'Département' },
    { value: 'sous_prefecture_brute', label: 'Sous-préfecture' },
    { value: 'localite_brute', label: 'Localité' },
    { value: 'type_localite_brut', label: 'Type de localité' },
    { value: 'latitude_decimal', label: 'Latitude' },
    { value: 'longitude_decimal', label: 'Longitude' },
    { value: 'type_ouvrage_brut', label: "Type d'ouvrage" },
    { value: 'etat_ouvrage_brut', label: "État de l'ouvrage" },
    { value: 'annee_projet', label: 'Année du projet' },
    { value: 'bailleur_brut', label: 'Bailleur' },
    { value: 'a_cgpe', label: 'Existence CGPE' },
]

type Destination = 'standard' | 'ouvrage' | 'localite' | 'cgpe' | 'ignore'

interface ColonneState {
    entete_brut: string
    destination: Destination
    champ_standard: string  // si destination === 'standard'
    metadata_key: string    // si destination !== 'standard' et !== 'ignore'
    confiance: number | null
}

function parseChampCible(champ: string | null): { dest: Destination, std: string, key: string } {
    if (!champ) return { dest: 'ignore', std: '', key: '' }
    if (champ.startsWith('metadata.ouvrage.')) return { dest: 'ouvrage', std: '', key: champ.replace('metadata.ouvrage.', '') }
    if (champ.startsWith('metadata.localite.')) return { dest: 'localite', std: '', key: champ.replace('metadata.localite.', '') }
    if (champ.startsWith('metadata.cgpe.')) return { dest: 'cgpe', std: '', key: champ.replace('metadata.cgpe.', '') }
    return { dest: 'standard', std: champ, key: '' }
}

function buildChampCible(col: ColonneState): string | null {
    if (col.destination === 'ignore') return null
    if (col.destination === 'standard') return col.champ_standard || null
    if (!col.metadata_key) return null
    return `metadata.${col.destination}.${col.metadata_key}`
}

export default function Mapping() {
    const { id } = useParams<{ id: string }>()
    const idFichier = Number(id)
    const queryClient = useQueryClient()

    const [activeFeuilleId, setActiveFeuilleId] = useState<number | null>(null)
    const [colonnes, setColonnes] = useState<ColonneState[]>([])

    const { data: fichier } = useQuery({
        queryKey: ['fichier', idFichier],
        queryFn: () => api.fichier(idFichier),
    })

    const { data: proposals, isLoading } = useQuery({
        queryKey: ['mapping-proposal', idFichier],
        queryFn: () => api.mappingProposal(idFichier),
    })

    // Initialisation
    useEffect(() => {
        if (proposals && proposals.length > 0 && activeFeuilleId === null) {
            const first = proposals[0]
            setActiveFeuilleId(first.id_feuille)
            setColonnes(
                first.colonnes.map((c) => {
                    const { dest, std, key } = parseChampCible(c.champ_cible)
                    return {
                        entete_brut: c.entete_brut,
                        destination: dest,
                        champ_standard: std,
                        metadata_key: key,
                        confiance: c.confiance,
                    }
                })
            )
        }
    }, [proposals, activeFeuilleId])

    // Changer de feuille
    const handleFeuilleChange = (id: number) => {
        setActiveFeuilleId(id)
        const prop = proposals?.find((p) => p.id_feuille === id)
        if (prop) {
            setColonnes(
                prop.colonnes.map((c) => {
                    const { dest, std, key } = parseChampCible(c.champ_cible)
                    return {
                        entete_brut: c.entete_brut,
                        destination: dest,
                        champ_standard: std,
                        metadata_key: key,
                        confiance: c.confiance,
                    }
                })
            )
        }
    }

    const updateCol = (entete: string, changes: Partial<ColonneState>) => {
        setColonnes((prev) =>
            prev.map((c) => (c.entete_brut === entete ? { ...c, ...changes } : c))
        )
    }

    // Mutation
    const saveMutation = useMutation({
        mutationFn: () => {
            const payload = colonnes.map((c) => ({
                entete_brut: c.entete_brut,
                champ_cible: buildChampCible(c),
            }))
            return api.saveMapping(idFichier, activeFeuilleId!, payload)
        },
        onSuccess: () => {
            toast.success('Mapping sauvegardé')
            queryClient.invalidateQueries({ queryKey: ['mapping-proposal', idFichier] })
        },
        onError: (e: any) => toast.error(e.message || 'Erreur'),
    })

    if (isLoading) return <div className="p-8 text-center text-gray-500">Chargement...</div>
    if (!proposals || proposals.length === 0) return <div className="p-8 text-center">Aucune feuille.</div>

    return (
        <div className="space-y-6 max-w-5xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Link to="/fichiers">
                        <Button variant="ghost" size="sm"><ChevronLeft className="w-4 h-4 mr-1" /> Retour</Button>
                    </Link>
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900">Mapping des colonnes</h2>
                        <p className="text-sm text-gray-500">{fichier?.nom_fichier_original}</p>
                    </div>
                </div>
                <Button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending || !activeFeuilleId}>
                    <Save className="w-4 h-4 mr-2" /> {saveMutation.isPending ? 'Sauvegarde...' : 'Sauvegarder'}
                </Button>
            </div>

            {/* Onglets des feuilles */}
            <div className="flex border-b overflow-x-auto">
                {proposals.map((p) => (
                    <button
                        key={p.id_feuille}
                        onClick={() => handleFeuilleChange(p.id_feuille)}
                        className={`px-4 py-2 text-sm font-medium border-b-2 whitespace-nowrap ${
                            activeFeuilleId === p.id_feuille ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500'
                        }`}
                    >
                        {p.nom_feuille} ({p.colonnes.length})
                    </button>
                ))}
            </div>

            {/* Tableau de mapping */}
            <div className="bg-white border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b">
                    <tr>
                        <th className="text-left px-4 py-3 font-medium text-gray-700 w-1/3">Entête Excel</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-700 w-1/4">Destination</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-700 w-1/3">Champ / Clé</th>
                        <th className="text-center px-4 py-3 font-medium text-gray-700">Confiance</th>
                    </tr>
                    </thead>
                    <tbody>
                    {colonnes.map((col, idx) => (
                        <tr key={idx} className="border-b hover:bg-gray-50">
                            <td className="px-4 py-3 font-mono text-xs text-gray-900">{col.entete_brut}</td>

                            {/* Destination */}
                            <td className="px-4 py-3">
                                <select
                                    value={col.destination}
                                    onChange={(e) => updateCol(col.entete_brut, { destination: e.target.value as Destination })}
                                    className="w-full h-9 rounded-md border border-gray-300 bg-white px-2 text-sm"
                                >
                                    <option value="standard">Standard</option>
                                    <option value="ouvrage">Métadonnée Ouvrage</option>
                                    <option value="localite">Métadonnée Localité</option>
                                    <option value="cgpe">Métadonnée CGPE</option>
                                    <option value="ignore">Ignorer</option>
                                </select>
                            </td>

                            {/* Champ / Clé */}
                            <td className="px-4 py-3">
                                {col.destination === 'standard' && (
                                    <select
                                        value={col.champ_standard}
                                        onChange={(e) => updateCol(col.entete_brut, { champ_standard: e.target.value })}
                                        className="w-full h-9 rounded-md border border-gray-300 bg-white px-2 text-sm"
                                    >
                                        <option value="">— Choisir un champ —</option>
                                        {CHAMPS_STANDARDS.map((c) => (
                                            <option key={c.value} value={c.value}>{c.label}</option>
                                        ))}
                                    </select>
                                )}

                                {(col.destination === 'ouvrage' || col.destination === 'localite' || col.destination === 'cgpe') && (
                                    <div className="flex items-center gap-2">
                                        <Tag className="w-4 h-4 text-gray-400" />
                                        <Input
                                            placeholder="Nom de la clé (ex. profondeur_forage_m)"
                                            value={col.metadata_key}
                                            onChange={(e) => updateCol(col.entete_brut, { metadata_key: e.target.value })}
                                            className="h-9"
                                        />
                                    </div>
                                )}

                                {col.destination === 'ignore' && (
                                    <span className="text-gray-400 italic text-xs">Sera ignoré (gardé dans les données brutes)</span>
                                )}
                            </td>

                            {/* Confiance */}
                            <td className="px-4 py-3 text-center">
                                {col.confiance !== null && col.confiance !== undefined && col.destination !== 'ignore' ? (
                                    <div className="flex items-center justify-center gap-1 text-xs">
                                        {col.confiance === 1 && <CheckCircle2 className="w-4 h-4 text-green-500" />}
                                        <span className="text-gray-500">{Math.round(col.confiance * 100)}%</span>
                                    </div>
                                ) : null}
                            </td>
                        </tr>
                    ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}