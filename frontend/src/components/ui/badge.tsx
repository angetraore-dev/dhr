import { cn } from '@/lib/utils'
import { type ReactNode } from 'react'

const colors: Record<string, string> = {
    // Statuts fichier
    en_attente: 'bg-gray-100 text-gray-800',
    en_cours: 'bg-blue-100 text-blue-800',
    ingere: 'bg-green-100 text-green-800',
    partiel: 'bg-yellow-100 text-yellow-800',
    erreur: 'bg-red-100 text-red-800',
    // Statuts run
    termine: 'bg-green-100 text-green-800',
    annule: 'bg-gray-100 text-gray-800',
    // Statuts qualité
    ok: 'bg-green-100 text-green-800',
    localite_non_resolue: 'bg-yellow-100 text-yellow-800',
    geom_invalide: 'bg-orange-100 text-orange-800',
    type_ouvrage_inconnu: 'bg-orange-100 text-orange-800',
    rejete: 'bg-red-100 text-red-800',
    doublon_suspect: 'bg-purple-100 text-purple-800',
}

export function Badge({ status, children }: { status: string; children: ReactNode }) {
    return (
        <span
            className={cn(
                'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                colors[status] || 'bg-gray-100 text-gray-800',
            )}
        >
      {children}
    </span>
    )
}