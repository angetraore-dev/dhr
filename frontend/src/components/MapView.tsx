import { useEffect, useRef } from 'react'
import L from 'leaflet'
import type { FeatureCollection } from '@/lib/api'

interface Props {
    data: FeatureCollection | null
    height?: string
}

const TYPE_COLORS: Record<string, string> = {
    PMH: '#2563eb',   // bleu
    HVA: '#16a34a',   // vert
    PEA: '#ea580c',   // orange
    HV: '#9333ea',    // violet
    AUTRE: '#6b7280', // gris
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

    if (p.type_ouvrage) mainLines.push(`<b>${_escape(p.type_ouvrage)}</b>`)
    if (p.etat) mainLines.push(`État : ${_escape(p.etat)}`)
    if (p.localite) mainLines.push(`Localité : ${_escape(p.localite)}`)
    if (p.code_ouvrage) mainLines.push(`Code : ${_escape(p.code_ouvrage)}`)
    if (p.annee_realisation) mainLines.push(`Année : ${_escape(p.annee_realisation)}`)
    if (p.statut_qualite) mainLines.push(`Qualité : ${_escape(p.statut_qualite)}`)

    let html = mainLines.join('<br/>')

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

    return html
}

export function MapView({ data, height = '600px' }: Props) {
    const containerRef = useRef<HTMLDivElement>(null)
    const mapRef = useRef<L.Map | null>(null)
    const layerRef = useRef<L.GeoJSON | null>(null)

    // Initialisation de la carte (une seule fois)
    useEffect(() => {
        if (!containerRef.current || mapRef.current) return

        const map = L.map(containerRef.current, {
            center: [7.5, -5.5],  // Côte d'Ivoire
            zoom: 7,
            maxZoom: 19,
            zoomControl: true,
        })

        // Esri World Imagery (satellite)
        L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            {
                attribution: 'Tiles &copy; Esri',
                maxZoom: 19,
            },
        ).addTo(map)

        // Labels (noms de villes, routes)
        L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
            { attribution: '&copy; Esri', maxZoom: 19, opacity: 0.7 },
        ).addTo(map)

        mapRef.current = map
        layerRef.current = L.geoJSON(undefined, {
            pointToLayer: (feature, latlng) => {
                const type = feature.properties?.type_ouvrage
                const color = getColor(type)
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

    // Mise à jour des données
    useEffect(() => {
        if (!mapRef.current || !layerRef.current) return

        layerRef.current.clearLayers()
        if (data) {
            layerRef.current.addData(data as any)
        }
    }, [data])

    return <div ref={containerRef} style={{ height }} className="rounded-lg border" />
}