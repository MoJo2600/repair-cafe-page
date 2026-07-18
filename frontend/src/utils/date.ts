/**
 * Format a date-only string (YYYY-MM-DD) or ISO datetime using the browser locale.
 */
export function formatDate(dateString: string | undefined | null): string {
  if (!dateString) return ''
  const date = new Date(dateString.length === 10 ? dateString + 'T00:00:00' : dateString)
  return date.toLocaleDateString(undefined, { year: 'numeric', month: '2-digit', day: '2-digit' })
}

/**
 * Format an ISO datetime string using the browser locale.
 */
export function formatDateTime(dateString: string | undefined | null): string {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString(undefined, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
