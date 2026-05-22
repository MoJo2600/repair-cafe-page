/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
import type { PruefgeraetResponse } from "../generated/data-contracts";

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
}
