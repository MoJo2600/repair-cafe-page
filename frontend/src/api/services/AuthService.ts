/* Auth API Service */
import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
import type { AuthResponse, LoginRequest } from "../generated/data-contracts";

export type { AuthResponse, LoginRequest };

export class AuthService {
  /**
   * Authenticate with username and password.
   * Sets an HTTP-only session cookie on success.
   */
  public static login(body: LoginRequest): CancelablePromise<AuthResponse> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/auth/login",
      body,
      errors: {
        401: "Invalid credentials",
        403: "Account disabled",
      },
    });
  }

  /**
   * Return the currently authenticated user's profile.
   */
  public static me(): CancelablePromise<AuthResponse> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/auth/me",
      errors: {
        401: "Not authenticated",
      },
    });
  }

  /**
   * Invalidate the current session cookie.
   */
  public static logout(): CancelablePromise<{ reply: string }> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/auth/logout",
      errors: {
        401: "Not authenticated",
      },
    });
  }
}
