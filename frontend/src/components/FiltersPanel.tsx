import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Input } from '@/components/ui/input'

export interface Filters {
    region: string
    departement: string
    sous_prefecture: string
    localite: string
    type_ouvrage: string
    etat: string
    annee_min: string
    annee_max: string
}

interface Props {
    filters: Filters
    onChange: (filters: Filters) => void
    showGeographic?: boolean
}

interface GeoOption {
    id_geo: number
    nom: string
}

export function FiltersPanel({ filters, onChange, showGeographic = true }: Props) {
    const [localites, setLocalites] = useState<{ id: number; nom: string }[]>([])

    // On stocke les objets complets pour avoir les id_geo (parent_id)
    const [regions, setRegions] = useState<GeoOption[]>([])
    const [departements, setDepartements] = useState<GeoOption[]>([])
    const [sousPrefectures, setSousPrefectures] = useState<GeoOption[]>([])

    // 1. Charger les régions (une seule fois)
    useEffect(() => {
        if (!showGeographic) return
        api.refGeo({ niveau: 'region' }).then((res) => {
            setRegions(res.data as GeoOption[])
        }).catch(() => {})
    }, [showGeographic])

    // 2. Charger les départements quand la région change
    useEffect(() => {
        if (!filters.region) {
            setDepartements([])
            return
        }
        const reg = regions.find(r => r.nom === filters.region)
        if (reg) {
            api.refGeo({ niveau: 'departement', parent_id: reg.id_geo }).then((res) => {
                setDepartements(res.data as GeoOption[])
            }).catch(() => {})
        }
    }, [filters.region, regions])

    // 3. Charger les sous-préfectures quand le département change
    useEffect(() => {
        if (!filters.departement) {
            setSousPrefectures([])
            return
        }
        const dept = departements.find(d => d.nom === filters.departement)
        if (dept) {
            api.refGeo({ niveau: 'sous_prefecture', parent_id: dept.id_geo }).then((res) => {
                setSousPrefectures(res.data as GeoOption[])
            }).catch(() => {})
        }
    }, [filters.departement, departements])

    // 4. Charger les localités (autocomplete)
    useEffect(() => {
        if (!showGeographic) return
        const timer = setTimeout(() => {
            if (filters.localite.length >= 2) {
                api.localites({ q: filters.localite, limit: 20 }).then((res) => {
                    setLocalites(res.data.map((l: any) => ({ id: l.id_localite, nom: l.nom_usage })))
                }).catch(() => {})
            } else {
                setLocalites([])
            }
        }, 300)
        return () => clearTimeout(timer)
    }, [filters.localite, showGeographic])

    const update = (key: keyof Filters, value: string) => {
        // Réinitialisation en cascade
        if (key === 'region') {
            onChange({ ...filters, region: value, departement: '', sous_prefecture: '' })
        } else if (key === 'departement') {
            onChange({ ...filters, departement: value, sous_prefecture: '' })
        } else {
            onChange({ ...filters, [key]: value })
        }
    }

    return (
        <div className="bg-white border rounded-lg p-4 space-y-3">
            <h3 className="font-medium text-sm text-gray-700">Filtres</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                {/* Type d'ouvrage */}
                <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
                    <select
                        value={filters.type_ouvrage}
                        onChange={(e) => update('type_ouvrage', e.target.value)}
                        className="w-full h-9 rounded-md border border-gray-300 bg-white px-2 text-sm"
                    >
                        <option value="">Tous</option>
                        <option value="PMH">PMH</option>
                        <option value="HVA">HVA</option>
                        <option value="PEA">PEA</option>
                        <option value="HV">HV</option>
                        <option value="AUTRE">AUTRE</option>
                    </select>
                </div>

                {/* État */}
                <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">État</label>
                    <select
                        value={filters.etat}
                        onChange={(e) => update('etat', e.target.value)}
                        className="w-full h-9 rounded-md border border-gray-300 bg-white px-2 text-sm"
                    >
                        <option value="">Tous</option>
                        <option value="fonctionnel">Fonctionnel</option>
                        <option value="en_panne">En panne</option>
                        <option value="abandonne">Abandonné</option>
                        <option value="inconnu">Inconnu</option>
                    </select>
                </div>

                {showGeographic && (
                    <>
                        {/* Région */}
                        <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Région</label>
                            <select
                                value={filters.region}
                                onChange={(e) => update('region', e.target.value)}
                                className="w-full h-9 rounded-md border border-gray-300 bg-white px-2 text-sm"
                            >
                                <option value="">Toutes</option>
                                {regions.map((r) => (
                                    <option key={r.id_geo} value={r.nom}>{r.nom}</option>
                                ))}
                            </select>
                        </div>

                        {/* Département */}
                        <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Département</label>
                            <select
                                value={filters.departement}
                                onChange={(e) => update('departement', e.target.value)}
                                disabled={!filters.region}
                                className="w-full h-9 rounded-md border border-gray-300 bg-white px-2 text-sm disabled:opacity-50"
                            >
                                <option value="">Tous</option>
                                {departements.map((d) => (
                                    <option key={d.id_geo} value={d.nom}>{d.nom}</option>
                                ))}
                            </select>
                        </div>

                        {/* Sous-préfecture */}
                        <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Sous-préfecture</label>
                            <select
                                value={filters.sous_prefecture}
                                onChange={(e) => update('sous_prefecture', e.target.value)}
                                disabled={!filters.departement}
                                className="w-full h-9 rounded-md border border-gray-300 bg-white px-2 text-sm disabled:opacity-50"
                            >
                                <option value="">Toutes</option>
                                {sousPrefectures.map((sp) => (
                                    <option key={sp.id_geo} value={sp.nom}>{sp.nom}</option>
                                ))}
                            </select>
                        </div>

                        {/* Localité (autocomplete) */}
                        <div className="relative">
                            <label className="block text-xs font-medium text-gray-600 mb-1">Localité</label>
                            <Input
                                placeholder="Rechercher..."
                                value={filters.localite}
                                onChange={(e) => update('localite', e.target.value)}
                                className="h-9"
                            />
                            {localites.length > 0 && (
                                <ul className="absolute z-10 w-full mt-1 bg-white border rounded shadow-lg max-h-40 overflow-y-auto">
                                    {localites.map((l) => (
                                        <li
                                            key={l.id}
                                            onClick={() => {
                                                update('localite', l.nom)
                                                setLocalites([])
                                            }}
                                            className="px-2 py-1 text-sm hover:bg-gray-100 cursor-pointer"
                                        >
                                            {l.nom}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>

                        {/* Année min */}
                        <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Année min</label>
                            <Input
                                type="number"
                                value={filters.annee_min}
                                onChange={(e) => update('annee_min', e.target.value)}
                                placeholder="2010"
                                className="h-9"
                            />
                        </div>

                        {/* Année max */}
                        <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Année max</label>
                            <Input
                                type="number"
                                value={filters.annee_max}
                                onChange={(e) => update('annee_max', e.target.value)}
                                placeholder="2026"
                                className="h-9"
                            />
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}