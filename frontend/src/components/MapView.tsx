import { useEffect, useRef } from 'react'
import L from 'leaflet'
import type { FeatureCollection } from '@/lib/api'

interface Props {
    data: FeatureCollection | null
    height?: string
}

const TYPE_COLORS: Record<string, string> = {
    PMH: '#2563eb',
    HVA: '#16a34a',
    PEA: '#ea580c',
    HV: '#9333ea',
    AUTRE: '#6b7280',
}

function getColor(type: string | undefined): string {
    return TYPE_COLORS[type || 'AUTRE'] || TYPE_COLORS.AUTRE
}

function _escape(str: unknown): string {
    if (str === null || str === undefined) return ''
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
}

function buildPopupHtml(p: Record<string, any>): string {
    const mainLines: string[] = []

    if (p.type_alimentation) mainLines.push(`<b>${_escape(p.type_alimentation)}</b>`)
    if (p.nature_ouvrage) mainLines.push(`Nature : ${_escape(p.nature_ouvrage)}`)
    if (p.realisation_par) mainLines.push(`Réalisation : ${_escape(p.realisation_par)}`)
    if (p.etat) mainLines.push(`État : ${_escape(p.etat)}`)
    if (p.localite) mainLines.push(`Localité : ${_escape(p.localite)}`)
    if (p.code_ouvrage) mainLines.push(`Code : ${_escape(p.code_ouvrage)}`)
    if (p.annee_realisation) mainLines.push(`Année : ${_escape(p.annee_realisation)}`)
    if (p.statut_qualite) mainLines.push(`Qualité : ${_escape(p.statut_qualite)}`)

    let html = mainLines.join('<br/>')

    // Détails (metadata)
    const meta = p.metadata as Record<string, unknown> | undefined
    if (meta && Object.keys(meta).length > 0) {
        const rows = Object.entries(meta)
            .filter(([, v]) => v !== null && v !== undefined && String(v).trim() !== '')
            .map(
                ([k, v]) =>
                    `<tr>
             <td style="font-weight:500;padding-right:8px;vertical-align:top;color:#374151;">${_escape(k)}</td>
             <td style="color:#111827;">${_escape(v)}</td>
           </tr>`,
            )
            .join('')

        html += `
      <details style="margin-top:8px;">
        <summary style="cursor:pointer;color:#2563eb;font-size:12px;font-weight:500;user-select:none;">
          Détails (${Object.keys(meta).length})
        </summary>
        <table style="font-size:12px;margin-top:6px;border-collapse:collapse;">
          ${rows}
        </table>
      </details>
    `
    }

    // Qualité de l'eau (F2)
    const qualiteEau = p.qualite_eau as Record<string, unknown> | undefined
    if (qualiteEau && Object.keys(qualiteEau).length > 0) {
        const rows = Object.entries(qualiteEau)
            .filter(([, v]) => v !== null && v !== undefined && String(v).trim() !== '')
            .map(
                ([k, v]) =>
                    `<tr>
             <td style="font-weight:500;padding-right:8px;vertical-align:top;color:#374151;">${_escape(k)}</td>
             <td style="color:#111827;">${_escape(v)}</td>
           </tr>`,
            )
            .join('')

        html += `
      <details style="margin-top:8px;">
        <summary style="cursor:pointer;color:#2563eb;font-size:12px;font-weight:500;user-select:none;">
          Qualité de l'eau (${Object.keys(qualiteEau).length})
        </summary>
        <table style="font-size:12px;margin-top:6px;border-collapse:collapse;">
          ${rows}
        </table>
      </details>
    `
    }

    return html
}

export function MapView({ data, height = '600px' }: Props) {
    const containerRef = useRef<HTMLDivElement>(null)
    const mapRef = useRef<L.Map | null>(null)
    const layerRef = useRef<L.GeoJSON | null>(null)

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
                const props = (feature.properties || {}) as Record<string, any>
                const type = props.type_alimentation
                const nature = props.nature_ouvrage
                const color = getColor(type)

                // Carré pour les puits (F2)
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

                // Losange pour les inconnus (F2)
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

                // Cercle plein pour les forages (défaut)
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
                const p = (feature.properties || {}) as Record<string, any>
                layer.bindPopup(buildPopupHtml(p), { maxWidth: 320 })
            },
        }).addTo(map)

        return () => {
            map.remove()
            mapRef.current = null
            layerRef.current = null
        }
    }, [])

    useEffect(() => {
        if (!mapRef.current || !layerRef.current) return

        layerRef.current.clearLayers()
        if (data) {
            layerRef.current.addData(data as any)
        }
    }, [data])

    return <div ref={containerRef} style={{ height }} className="rounded-lg border" />
}