// Sessions belong to this Mini App launch, never to a previously used account.
let accessToken: string | null = null
type FailureListener = (status: 401 | 403) => void
const listeners = new Set<FailureListener>()

export function getToken(): string | null {
    return accessToken
}

export function setToken(token: string): void {
    accessToken = token
}

export function removeToken(): void {
    accessToken = null
}

export function clearLegacyToken(): void {
    try { localStorage.removeItem("access_token") } catch { /* Storage may be unavailable in WebView. */ }
}

export function onSessionFailure(listener: FailureListener): () => void {
    listeners.add(listener)
    return () => { listeners.delete(listener) }
}

export function reportSessionFailure(token: string | null, status: number, detail: string): void {
    if (!token || token !== accessToken) return
    if (status !== 401 && !(status === 403 && detail === "Access not granted")) return
    removeToken()
    listeners.forEach(listener => listener(status as 401 | 403))
}
