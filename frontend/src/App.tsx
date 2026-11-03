import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { FileText, Map, List, Activity, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'

import Fichiers from '@/pages/Fichiers'
import Mapping from '@/pages/Mapping'
import Carte from '@/pages/Carte'
import Liste from '@/pages/Liste'
import Qualite from '@/pages/Qualite'
import Parametres from '@/pages/Parametres'

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: 1,
            refetchOnWindowFocus: false,
            staleTime: 30_000,
        },
    },
})

const NAV = [
    { path: '/fichiers', label: 'Fichiers', icon: FileText },
    { path: '/carte', label: 'Carte', icon: Map },
    { path: '/liste', label: 'Liste', icon: List },
    { path: '/qualite', label: 'Qualité', icon: Activity },
    { path: '/parametres', label: 'Paramètres', icon: Settings },
]

function Layout({ children }: { children: React.ReactNode }) {
    const location = useLocation()

    return (
        <div className="min-h-screen flex flex-col">
            {/* Header */}
            <header className="border-b bg-white px-6 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <h1 className="text-lg font-bold text-gray-900">DHR</h1>
                    <span className="text-xs text-gray-500">
            Centralisation des ouvrages hydrauliques ruraux
          </span>
                </div>
            </header>

            <div className="flex flex-1">
                {/* Sidebar */}
                <aside className="w-56 border-r bg-gray-50 p-4">
                    <nav className="space-y-1">
                        {NAV.map(({ path, label, icon: Icon }) => {
                            const active = location.pathname.startsWith(path)
                            return (
                                <Link
                                    key={path}
                                    to={path}
                                    className={cn(
                                        'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition',
                                        active
                                            ? 'bg-blue-100 text-blue-700'
                                            : 'text-gray-700 hover:bg-gray-100',
                                    )}
                                >
                                    <Icon className="w-4 h-4" />
                                    {label}
                                </Link>
                            )
                        })}
                    </nav>
                </aside>

                {/* Main */}
                <main className="flex-1 p-6">{children}</main>
            </div>
        </div>
    )
}

export default function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>
                <Layout>
                    <Routes>
                        <Route path="/" element={<Navigate to="/fichiers" replace />} />
                        <Route path="/fichiers" element={<Fichiers />} />
                        <Route path="/fichiers/:id/mapping" element={<Mapping />} />
                        <Route path="/carte" element={<Carte />} />
                        <Route path="/liste" element={<Liste />} />
                        <Route path="/qualite" element={<Qualite />} />
                        <Route path="/parametres" element={<Parametres />} />
                    </Routes>
                </Layout>
                <Toaster position="top-right" richColors />
            </BrowserRouter>
        </QueryClientProvider>
    )
}