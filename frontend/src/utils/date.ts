/** Dates are always German, independent of the browser language (docs/STYLEGUIDE.md). */
const LOCALE = 'de-DE'

/**
 * Format a date-only string (YYYY-MM-DD) or ISO datetime as a German date: 03.11.2026
 */
export function formatDate(dateString: string | undefined | null): string {
  if (!dateString) return ''
  const date = new Date(dateString.length === 10 ? dateString + 'T00:00:00' : dateString)
  return date.toLocaleDateString(LOCALE, { year: 'numeric', month: '2-digit', day: '2-digit' })
}

/**
 * Format an ISO datetime as German date and time: 03.11.2026, 16:09
 */
export function formatDateTime(dateString: string | undefined | null): string {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString(LOCALE, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
