/* RepairLogs API Service */
import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
import type {
  RepairLogResponse,
  RepairLogCreate,
  RepairLogListResponse,
} from "../generated/data-contracts";

export class RepairLogsService {
  /**
   * Get all log entries for a specific repair
   * @param repairId The repair ID
   * @returns RepairLogListResponse List of repair log entries
   * @throws ApiError
   */
  public static listRepairLogs(
    repairId: number,
  ): CancelablePromise<RepairLogListResponse> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/repairs/{repair_id}/logs",
      path: {
        repair_id: repairId,
      },
      errors: {
        404: `Repair not found`,
        500: `Internal Server Error`,
      },
    });
  }

  /**
   * Create a new repair log entry
   * @param repairId The repair ID
   * @param body The repair log data
   * @returns RepairLogResponse Repair log created successfully
   * @throws ApiError
   */
  public static createRepairLog(
    repairId: number,
    body: Omit<RepairLogCreate, "repair_id">,
  ): CancelablePromise<{
    reply: string;
    data?: RepairLogResponse;
    message?: string;
    id?: number;
    error?: string;
  }> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/repairs/{repair_id}/logs",
      path: {
        repair_id: repairId,
      },
      body: {
        ...body,
        repair_id: repairId,
      },
      errors: {
        400: `Invalid input`,
        404: `Repair not found`,
        500: `Internal Server Error`,
      },
    });
  }

  /**
   * Get a specific repair log entry
   * @param repairId The repair ID
   * @param logId The repair log ID
   * @returns any Repair log details
   * @throws ApiError
   */
  public static getRepairLog(
    repairId: number,
    logId: number,
  ): CancelablePromise<{
    reply: string;
    data?: RepairLogResponse;
    error?: string;
  }> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/repairs/{repair_id}/logs/{log_id}",
      path: {
        repair_id: repairId,
        log_id: logId,
      },
      errors: {
        404: `Repair log not found`,
        500: `Internal Server Error`,
      },
    });
  }

  /**
   * Update an existing repair log entry
   */
  public static updateRepairLog(
    repairId: number,
    logId: number,
    body: Partial<Omit<RepairLogCreate, "repair_id">>,
  ): CancelablePromise<{
    reply: string;
    data?: RepairLogResponse;
    error?: string;
  }> {
    return __request(OpenAPI, {
      method: "PUT",
      url: "/api/repairs/{repair_id}/logs/{log_id}",
      path: {
        repair_id: repairId,
        log_id: logId,
      },
      body,
      errors: {
        404: `Repair log not found`,
        500: `Internal Server Error`,
      },
    });
  }

  /**
   * Delete a repair log entry
   * @param repairId The repair ID
   * @param logId The repair log ID
   * @returns Deletion confirmation
   * @throws ApiError
   */
  public static deleteRepairLog(
    repairId: number,
    logId: number,
  ): CancelablePromise<{
    reply: string;
    message?: string;
    error?: string;
  }> {
    return __request(OpenAPI, {
      method: "DELETE",
      url: "/api/repairs/{repair_id}/logs/{log_id}",
      path: {
        repair_id: repairId,
        log_id: logId,
      },
      errors: {
        404: `Repair log not found`,
        500: `Internal Server Error`,
      },
    });
  }
}
