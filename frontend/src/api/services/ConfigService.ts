/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
import type {
  AppConfigResponse,
  FeaturesResponse,
  PruefgeraetResponse,
} from "../generated/data-contracts";

export class ConfigService {
  /**
   * Get list of testing devices (Prüfgeräte) from DB.
   * @returns List of testing devices with name and serial_number
   * @throws ApiError
   */
  public static getPruefgeraete(): CancelablePromise<PruefgeraetResponse[]> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/config/pruefgeraete",
    });
  }

  /**
   * Get dropdown configuration data from DB.
   * @returns Dropdown configuration data keyed by English category name
   * @throws ApiError
   */
  public static getDropdownConfig(): CancelablePromise<{
    repair_type?: Array<{ id: number; name: string }>;
  }> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/config/dropdowns",
    });
  }

  /**
   * Get application-level configuration (org name and website).
   * @returns AppConfigResponse
   * @throws ApiError
   */
  public static getAppConfig(): CancelablePromise<AppConfigResponse> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/config/app-config",
    });
  }

  /**
   * Update application-level configuration (admin only).
   * @returns AppConfigResponse Updated configuration
   * @throws ApiError
   */
  public static updateAppConfig(
    body: Partial<AppConfigResponse>,
  ): CancelablePromise<AppConfigResponse> {
    return __request(OpenAPI, {
      method: "PUT",
      url: "/api/config/app-config",
      body,
      mediaType: "application/json",
    });
  }

  /**
   * Get server-side feature flags (e.g. whether the label printer is enabled).
   * @returns FeaturesResponse
   * @throws ApiError
   */
  public static getFeatures(): CancelablePromise<FeaturesResponse> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/config/features",
    });
  }
}
