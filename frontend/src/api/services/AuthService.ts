/* Auth API Service */
import type { CancelablePromise } from '../core/CancelablePromise'
import { OpenAPI } from '../core/OpenAPI'
import { request as __request } from '../core/request'
import type {
  APIResponse,
  AuthConfigResponse,
  AuthResponse,
  LoginRequest,
  PinGeneratedResponse,
  PinGenerateRequest,
  PinStatusResponse,
  PinDashboardSummaryResponse,
  PinSessionActionResponse,
  PinSessionStatusResponse,
  PinUnlockRequest,
} from '@/api/types'

export type { AuthResponse, LoginRequest }

export class AuthService {
  /**
   * Authenticate with username and password.
   * Sets an HTTP-only session cookie on success.
   */
  public static login(body: LoginRequest): CancelablePromise<AuthResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/auth/login',
      body,
      errors: {
        401: 'Invalid credentials',
        403: 'Account disabled',
      },
    })
  }

  /**
   * Return the currently authenticated user's profile.
   */
  public static me(): CancelablePromise<AuthResponse> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/auth/me',
      errors: {
        401: 'Not authenticated',
      },
    })
  }

  /**
   * Invalidate the current session cookie.
   */
  public static logout(): CancelablePromise<APIResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/auth/logout',
      errors: {
        401: 'Not authenticated',
      },
    })
  }

  /**
   * Which login methods the server offers (public).
   */
  public static config(): CancelablePromise<AuthConfigResponse> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/auth/config',
    })
  }

  /**
   * URL that starts the SSO login; a full-page navigation, not an XHR call.
   */
  public static oidcLoginUrl(next: string): string {
    return `/api/auth/oidc/login?next=${encodeURIComponent(next)}`
  }

  public static pinStatus(): CancelablePromise<PinStatusResponse> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/auth/me/pin',
    })
  }

  public static generatePin(body: PinGenerateRequest): CancelablePromise<PinGeneratedResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/auth/me/pin',
      body,
      mediaType: 'application/json',
    })
  }

  public static pinSessionStatus(): CancelablePromise<PinSessionStatusResponse> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/auth/pin-session',
    })
  }

  public static lockPinSession(): CancelablePromise<PinSessionActionResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/auth/pin-session/lock',
      mediaType: 'application/json',
    })
  }

  public static recordPinActivity(): CancelablePromise<PinSessionActionResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/auth/pin-session/activity',
      mediaType: 'application/json',
    })
  }

  public static unlockPinSession(body: PinUnlockRequest): CancelablePromise<AuthResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/auth/pin-session/unlock',
      body,
      mediaType: 'application/json',
      errors: {
        401: 'PIN is incorrect',
        423: 'Session is not locked',
        429: 'PIN attempts temporarily limited',
      },
    })
  }

  public static pinDashboardSummary(): CancelablePromise<PinDashboardSummaryResponse> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/auth/pin-session/dashboard',
    })
  }
}
