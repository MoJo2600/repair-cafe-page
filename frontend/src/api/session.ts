/**
 * Central reaction to session-level HTTP errors, shared by the generated API client
 * (client.ts) and the few direct requests via `sessionFetch` (HEAD checks).
 *
 * 401 → session ended, go to login; 423 → PIN session locked, go to lock screen.
 */
export function handleSessionStatus(url: string, status: number): void {
  if (status !== 401 && status !== 423) return
  // Auth endpoints report their own failures (wrong password, wrong PIN, ...)
  if (url.startsWith('/api/auth/')) return

  // Lazy imports avoid a store/router <-> api import cycle at module init
  void Promise.all([import('@/stores/authStore'), import('@/router')]).then(
    ([{ useAuthStore }, { default: router }]) => {
      const authStore = useAuthStore()
      const current = router.currentRoute.value
      if (status === 423) {
        authStore.markLocked()
        if (current.name !== 'PinLock') void router.push({ name: 'PinLock' })
      } else {
        authStore.markSessionEnded()
        if (current.name !== 'Login') {
          void router.push({ name: 'Login', query: { redirect: current.fullPath } })
        }
      }
    }
  )
}

/** Drop-in replacement for fetch() on /api URLs that applies session handling. */
export async function sessionFetch(url: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(url, init)
  handleSessionStatus(url, response.status)
  return response
}
