import { useEffect, useRef } from 'react'
import L from 'leaflet'
import type { FeatureCollection } from '@/lib/api'

export type MapMode = 'tous' | 'fichier'

interface Props {
    data: FeatureCollection | null
    height?: string
    mode?: MapMode
}

// Palette mode Tous (couleur = alimentation)
const TYPE_COLORS: Record<string, string> = {
    PMH: '#2563eb', // bleu
    HVA: '#16a34a', // vert
    PEA: '#ea580c', // orange
    HV: '#9333ea', // violet
    AUTRE: '#6b7280', // gris
}

// Palette mode Fichier (couleur = qualité)
const QUALITE_COLORS: Record<string, string> = {
    ok: '#16a34a', // vert
    localite_non_resolue: '#f59e0b', // ambre
    geom_invalide: '#dc2626', // rouge
    type_ouvrage_inconnu: '#9333ea', // violet
    doublon_suspect: '#eab308', // jaune
    rejete: '#6b7280', // gris (jamais affiché, mais sécurité)
}

function getColor(mode: MapMode, props: Record<string, unknown>): string {
    if (mode === 'fichier') {
        const statut = props.statut_qualite as string | undefined
        return QUALITE_COLORS[statut || ''] || '#6b7280'
    }
    const type = props.type_alimentation as string | undefined
    return TYPE_COLORS[type || 'AUTRE'] || TYPE_COLORS.AUTRE
}

function _escape(str: unknown): string {
    if (str === null || str === undefined) return ''
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
}

function _renderDetails(
    title: string,
    obj: Record<string, unknown> | undefined | null,
): string {
    if (!obj) return ''
    const entries = Object.entries(obj).filter(
        ([, v]) => v !== null && v !== undefined && String(v).trim() !== '',
    )
    if (entries.length === 0) return ''
    const rows = entries
        .map(
            ([k, v]) =>
                `<tr>
           <td style="font-weight:500;padding-right:8px;vertical-align:top;color:#374151;">${_escape(k)}</td>
           <td style="color:#111827;">${_escape(v)}</td>
         </tr>`,
        )
        .join('')
    return `
    <details style="margin-top:8px;">
      <summary style="cursor:pointer;color:#2563eb;font-size:12px;font-weight:500;user-select:none;">
        ${_escape(title)} (${entries.length})
      </summary>
      <table style="font-size:12px;margin-top:6px;border-collapse:collapse;">
        ${rows}
      </table>
    </details>`
}

function buildPopupHtml(
    p: Record<string, unknown>,
    mode: MapMode,
): string {
    const mainLines: string[] = []

    if (mode === 'fichier') {
        // Mode Fichier : on affiche le brut + le statut qualité
        if (p.statut_qualite)
            mainLines.push(`<b>${_escape(p.statut_qualite)}</b>`)
        if (p.nom_feuille) mainLines.push(`Feuille : ${_escape(p.nom_feuille)}`)
        if (p.num_ligne_source)
            mainLines.push(`Ligne Excel : #${_escape(p.num_ligne_source)}`)
        if (p.type_ouvrage_brut)
            mainLines.push(`Type brut : ${_escape(p.type_ouvrage_brut)}`)
        if (p.etat_ouvrage_brut)
            mainLines.push(`État brut : ${_escape(p.etat_ouvrage_brut)}`)
        if (p.bailleur_brut)
            mainLines.push(`Bailleur brut : ${_escape(p.bailleur_brut)}`)
    } else {
        // Mode Tous : métier consolidé
        if (p.type_alimentation)
            mainLines.push(`<b>${_escape(p.type_alimentation)}</b>`)
        if (p.nature_ouvrage)
            mainLines.push(`Nature : ${_escape(p.nature_ouvrage)}`)
        if (p.realisation_par)
            mainLines.push(`Réalisation : ${_escape(p.realisation_par)}`)
        if (p.etat) mainLines.push(`État : ${_escape(p.etat)}`)
        if (p.localite) mainLines.push(`Localité : ${_escape(p.localite)}`)
        if (p.code_ouvrage) mainLines.push(`Code : ${_escape(p.code_ouvrage)}`)
        if (p.annee_realisation)
            mainLines.push(`Année : ${_escape(p.annee_realisation)}`)
    }

    let html = mainLines.join('<br/>')

    // Détails metadata (mode Tous)
    if (mode === 'tous') {
        html += _renderDetails(
            'Détails',
            p.metadata as Record<string, unknown> | undefined,
        )
        html += _renderDetails(
            "Qualité de l'eau",
            p.qualite_eau as Record<string, unknown> | undefined,
        )
    }

    return html
}

export function MapView({ data, height = '600px', mode = 'tous' }: Props) {
    const containerRef = useRef<HTMLDivElement>(null)
    const mapRef = useRef<L.Map | null>(null)
    const layerRef = useRef<L.GeoJSON | null>(null)
    const modeRef = useRef<MapMode>(mode)

    // Re-créer la couche quand le mode change (palette différente)
    useEffect(() => {
        modeRef.current = mode
    }, [mode])

    useEffect(() => {
        if (!containerRef.current || mapRef.current) return

        const map = L.map(containerRef.current, {
            center: [7.5, -5.5],
            zoom: 7,
            maxZoom: 19,
            zoomControl: true,
        })

        L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            {
                attribution: 'Tiles &copy; Esri',
                maxZoom: 19,
                maxNativeZoom: 16,
            },
        ).addTo(map)

        L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
            { attribution: '&copy; Esri', maxZoom: 19, opacity: 0.7 },
        ).addTo(map)

        mapRef.current = map

        layerRef.current = L.geoJSON(undefined, {
            pointToLayer: (feature, latlng) => {
                const props = (feature.properties || {}) as Record<string, unknown>
                const color = getColor(modeRef.current, props)

                // En mode Fichier : tout en cercle (pas de nature en brut)
                if (modeRef.current === 'fichier') {
                    return L.circleMarker(latlng, {
                        radius: 6,
                        fillColor: color,
                        color: '#ffffff',
                        weight: 1.5,
                        opacity: 1,
                        fillOpacity: 0.9,
                    })
                }

                // En mode Tous : formes selon la nature
                const nature = props.nature_ouvrage

                if (nature === 'puits') {
                    return L.marker(latlng, {
                        icon: L.divIcon({
                            className: 'dhr-marker',
                            html: `<svg width="14" height="14" viewBox="0 0 14 14"><rect x="1" y="1" width="12" height="12" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg>`,
                            iconSize: [14, 14],
                            iconAnchor: [7, 7],
                        }),
                    })
                }

                if (nature === 'inconnu') {
                    return L.marker(latlng, {
                        icon: L.divIcon({
                            className: 'dhr-marker',
                            html: `<svg width="14" height="14" viewBox="0 0 14 14"><polygon points="7,1 13,7 7,13 1,7" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg>`,
                            iconSize: [14, 14],
                            iconAnchor: [7, 7],
                        }),
                    })
                }

                // Forage (défaut)
                return L.circleMarker(latlng, {
                    radius: 6,
                    fillColor: color,
                    color: '#ffffff',
                    weight: 1.5,
                    opacity: 1,
                    fillOpacity: 0.9,
                })
            },
            onEachFeature: (feature, layer) => {
                const p = (feature.properties || {}) as Record<string, unknown>
                layer.bindPopup(buildPopupHtml(p, modeRef.current), {
                    maxWidth: 320,
                })
            },
        }).addTo(map)

        return () => {
            map.remove()
            mapRef.current = null
            layerRef.current = null
        }
    }, [])

    // Mise à jour des données
    useEffect(() => {
        if (!mapRef.current || !layerRef.current) return

        layerRef.current.clearLayers()
        if (data) {
            layerRef.current.addData(data as never)
        }
    }, [data])

    // Mise à jour du mode : on force un re-render des couches
    useEffect(() => {
        if (!layerRef.current || !data) return

        layerRef.current.clearLayers()
        layerRef.current.addData(data as never)
    }, [mode, data])

    return (
        <div
            ref={containerRef}
            style={{ height }}
            className="rounded-lg border"
        />
    )
}