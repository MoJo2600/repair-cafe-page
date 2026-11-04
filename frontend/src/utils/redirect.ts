import type { LocationQuery, RouteLocationNormalized } from 'vue-router'

/** Pages that never make sense as a "go back here after login/unlock" target. */
const NON_TARGET_PATHS = new Set(['/', '/login', '/lock'])

/** Same-site relative path from the `redirect` query, or '/' (mirrors the backend's _safe_next). */
export function redirectTarget(query: LocationQuery): string {
  const value = query.redirect
  const target = Array.isArray(value) ? value[0] : value
  if (target && target.startsWith('/') && !target.startsWith('//') && !target.includes('\\')) {
    return target
  }
  return '/'
}

/** Query that lets the login/lock page return to `to` afterwards (e.g. a scanned label QR code). */
export function redirectQuery(to: RouteLocationNormalized): LocationQuery {
  return NON_TARGET_PATHS.has(to.path) ? {} : { redirect: to.fullPath }
}
