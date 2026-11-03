// Parametres.tsx
import { useState } from 'react'
import { setJwt, getJwt } from '@/lib/api'

export default function Parametres() {
    const [jwt, setJwtLocal] = useState(getJwt() || '')

    return (
        <div className="max-w-2xl space-y-4">
            <h2 className="text-xl font-bold">Paramètres</h2>
            <div className="border rounded-lg p-4 bg-white space-y-3">
                <label className="block text-sm font-medium">JWT (écriture)</label>
                <textarea
                    className="w-full border rounded p-2 text-sm font-mono"
                    rows={4}
                    value={jwt}
                    onChange={(e) => setJwtLocal(e.target.value)}
                    placeholder="Collez le JWT ici (généré via: docker compose exec backend python -c ...)"
                />
                <button
                    className="px-4 py-2 bg-blue-600 text-white rounded text-sm"
                    onClick={() => {
                        setJwt(jwt || null)
                        alert('JWT sauvegardé')
                    }}
                >
                    Sauvegarder
                </button>
            </div>
        </div>
    )
}