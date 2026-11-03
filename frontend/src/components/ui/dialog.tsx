import { cn } from '@/lib/utils'
import { type ReactNode } from 'react'
import { X } from 'lucide-react'

interface DialogProps {
    open: boolean
    onClose: () => void
    title: string
    children: ReactNode
}

export function Dialog({ open, onClose, title, children }: DialogProps) {
    if (!open) return null
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6 relative">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
                >
                    <X className="w-5 h-5" />
                </button>
                <h2 className="text-lg font-bold mb-4">{title}</h2>
                {children}
            </div>
        </div>
    )
}