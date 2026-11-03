/**
 * Gestion du JWT (stockage localStorage).
 * En Phase 6, pas d'écran de login : on génère un JWT via un script et on le colle.
 */

import { setJwt, getJwt } from './api'

export function loginWithJwt(jwt: string) {
    setJwt(jwt)
}

export function logout() {
    setJwt(null)
}

export function isAuthenticated(): boolean {
    return getJwt() !== null
}