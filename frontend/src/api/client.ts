/**
 * The one API client. Generated from frontend/openapi.json (pnpm generate-api);
 * this module only adds what the generated code can't know:
 * - session handling: 401 -> login, 423 -> PIN lock screen (see session.ts)
 * - errors as `ApiError` (an Error with HTTP status and parsed body)
 */
import { Api } from './generated/Api'
import type { HttpResponse } from './generated/http-client'
import { handleSessionStatus } from './session'

export class ApiError extends Error {
  readonly status: number
  /** Parsed error body, usually `{ reply: "error", error: "..." }`. */
  readonly body: { error?: string; [key: string]: unknown } | null

  constructor(status: number, body: ApiError['body'], fallback: string) {
    super(body?.error || fallback)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

function toApiError(thrown: unknown): unknown {
  // The generated client throws the failed Response with the parsed body in `error`
  if (thrown instanceof Response) {
    const response = thrown as HttpResponse<unknown, unknown>
    const body =
      response.error && typeof response.error === 'object'
        ? (response.error as ApiError['body'])
        : null
    return new ApiError(response.status, body, `HTTP ${response.status}`)
  }
  return thrown
}

const client = new Api({
  baseUrl: '',
  customFetch: async (input, init) => {
    const response = await fetch(input, init)
    const url = typeof input === 'string' ? input : input instanceof URL ? input.pathname : input.url
    handleSessionStatus(url, response.status)
    return response
  },
})

// Every generated method calls `this.request`, so wrapping it covers all of them
const request = client.request
client.request = ((params) =>
  request(params).catch((err) => Promise.reject(toApiError(err)))) as typeof request

export const api = client

/**
 * Multipart payload for upload endpoints. The generated serializer JSON-encodes
 * arrays and sends `undefined` as "undefined"; this appends each file separately
 * and skips empty fields. Returns FormData typed as the generated payload type.
 */
export function asFormData<T extends object>(payload: T): T {
  const form = new FormData()
  for (const [key, value] of Object.entries(payload)) {
    if (value === undefined || value === null) continue
    for (const item of Array.isArray(value) ? value : [value]) {
      form.append(key, item instanceof Blob ? item : String(item))
    }
  }
  return form as unknown as T
}
