/** Best-effort message from API errors (ApiError body, Error, or unknown). */
export function errorMessage(err: unknown, fallback: string): string {
  const maybe = err as { body?: { error?: string }; message?: string } | null
  return maybe?.body?.error || maybe?.message || fallback
}
