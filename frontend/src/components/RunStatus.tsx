import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Badge } from '@/components/ui/badge'

interface Props {
    idRun: number
    onDone?: () => void
}

export function RunStatus({ idRun, onDone }: Props) {
    const { data: run } = useQuery({
        queryKey: ['run', idRun],
        queryFn: () => api.run(idRun),
        refetchInterval: (query) => {
            const data = query.state.data
            if (data && (data.statut === 'termine' || data.statut === 'erreur')) {
                onDone?.()
                return false
            }
            return 2000
        },
    })

    if (!run) return null

    return (
        <div className="flex items-center gap-3 text-sm">
            <Badge status={run.statut}>
                {run.statut === 'en_cours' ? 'En cours...' : run.statut}
            </Badge>
            <span className="text-gray-600">
        {run.nb_lignes_ingerees} lignes ingérées
      </span>
            {run.statut === 'en_cours' && (
                <span className="text-gray-400 text-xs">polling...</span>
            )}
        </div>
    )
}