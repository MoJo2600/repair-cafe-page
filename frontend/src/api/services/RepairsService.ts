/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
import type { RepairsTimelineResponse } from "../generated/data-contracts";
export class RepairsService {
  /**
   * Get all repairs as JSON
   * @returns any List of all repairs
   * @throws ApiError
   */
  public static listRepairs(customerId?: number): CancelablePromise<any> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/list",
      query: {
        customer_id: customerId,
      },
      errors: {
        500: `Internal Server Error - database query failed`,
      },
    });
  }
  /**
   * Create a new repair record
   * @param body
   * @returns any Repair record created successfully
   * @throws ApiError
   */
  public static createRepair(body: {
    /**
     * Date and time of repair
     */
    datum: string;
    /**
     * Description of defect
     */
    defekt_besch?: string;
    /**
     * Email address
     */
    email?: string;
    /**
     * Type of device
     */
    geraet_art: string;
    /**
     * Last name
     */
    nachname: string;
    /**
     * Type of repair/category
     */
    reparatur_art: string;
    /**
     * Phone number
     */
    telefon?: string;
    /**
     * Base64 encoded signature image
     */
    unterschrift?: string;
    /**
     * First name
     */
    vorname: string;
  }): CancelablePromise<{
    /**
     * Created repair object
     */
    data?: any;
    /**
     * ID of created repair
     */
    id?: number;
    reply?: string;
  }> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/repairs",
      body: body,
      errors: {
        400: `Bad request - missing required fields`,
        500: `Internal server error`,
      },
    });
  }
  /**
   * Get a repair record by QR token
   * @param token QR token of the repair
   * @returns any Repair record found
   * @throws ApiError
   */
  public static getRepairByQrToken(token: string): CancelablePromise<any> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/repairs/by-token/{token}",
      path: {
        token: token,
      },
      errors: {
        404: `Repair not found`,
        500: `Internal server error`,
      },
    });
  }
  /**
   * Update an existing repair record
   * @param id ID of the repair to update
   * @param body
   * @returns any Repair record updated successfully
   * @throws ApiError
   */
  public static updateRepair(
    id: number,
    body: {
      datum?: string;
      defekt_besch?: string;
      din_pruef?: boolean;
      email?: string;
      geraet_art?: string;
      nachname?: string;
      user_id?: number | null;
      reparatur_art?: string;
      reparatur_besch?: string;
      reparatur_dauer?: number;
      status_detail?: string;
      reparatur_sonstiges?: string;
      status?: string;
      telefon?: string;
      vorname?: string;
    },
  ): CancelablePromise<{
    data?: any;
    reply?: string;
  }> {
    return __request(OpenAPI, {
      method: "PUT",
      url: "/api/repairs/{id}",
      path: {
        id: id,
      },
      body: body,
      errors: {
        404: `Repair not found`,
        500: `Internal server error`,
      },
    });
  }

  /**
   * Print a QR code label for a repair on the configured label printer.
   * @param id Repair ID
   * @param baseUrl Optional base URL for the QR code link (defaults to request host).
   */
  public static printLabel(
    id: number,
    baseUrl?: string,
  ): CancelablePromise<{ reply: string; message?: string; error?: string }> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/repairs/{id}/print-label",
      path: { id },
      body: baseUrl ? { base_url: baseUrl } : {},
      errors: {
        404: `Repair not found`,
        500: `Print error`,
      },
    });
  }

  /**
   * Delete a repair by ID
   */
  public static deleteRepair(
    id: number,
  ): CancelablePromise<{ reply: string; id: number }> {
    return __request(OpenAPI, {
      method: "DELETE",
      url: "/api/repairs/{id}",
      path: { id },
      errors: {
        404: `Repair not found`,
        500: `Internal server error`,
      },
    });
  }

  /**
   * Get weekly repair counts per status for the last 12 months.
   * @returns RepairsTimelineResponse
   */
  public static getRepairsTimeline(): CancelablePromise<RepairsTimelineResponse> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/repairs/stats/timeline",
    });
  }
}
