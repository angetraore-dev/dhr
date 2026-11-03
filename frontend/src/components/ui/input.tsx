import { cn } from '@/lib/utils'
import { type InputHTMLAttributes, forwardRef } from 'react'

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
    ({ className, ...props }, ref) => (
        <input
            ref={ref}
            className={cn(
                'flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50',
                className,
            )}
            {...props}
        />
    ),
)
Input.displayName = 'Input'