import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],

    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },

    server: {
        host: '0.0.0.0',
        port: 5173,
        strictPort: true,
        // Proxy pour éviter les problèmes de CORS en dev
        // Le front appelle /api/... et Vite redirige vers le back
        proxy: {
            '/api': {
                target: process.env.VITE_API_URL?.replace('/v1', '') || 'http://localhost:8000',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, '/v1'),
            },
        },
        // Nécessaire pour Docker sur certaines plateformes
        watch: {
            usePolling: true,
        },
    },

    build: {
        outDir: 'dist',
        sourcemap: true,
    },
})