/* eslint-disable */
/* tslint:disable */
// @ts-nocheck
/*
 * ---------------------------------------------------------------
 * ## THIS FILE WAS GENERATED VIA SWAGGER-TYPESCRIPT-API        ##
 * ##                                                           ##
 * ## AUTHOR: acacode                                           ##
 * ## SOURCE: https://github.com/acacode/swagger-typescript-api ##
 * ---------------------------------------------------------------
 */

import {
  CreateRepairLogParams,
  CreateVdeTestParams,
  DeleteRepairLogParams,
  DeleteSettingParams,
  GetRepairByQrTokenParams,
  GetRepairDisclaimerParams,
  GetRepairLogParams,
  GetVdeTestParams,
  ListRepairLogsParams,
  ListVdeTestsParams,
  RepairLogCreate,
  UpdateRepairParams,
  UpdateSettingParams,
  VdeTestCreate,
} from "./data-contracts";
import { ContentType, HttpClient, RequestParams } from "./http-client";

export class Api<
  SecurityDataType = unknown,
> extends HttpClient<SecurityDataType> {
  /**
   * No description
   *
   * @tags Configuration
   * @name GetDropdownConfig
   * @summary Get dropdown configuration data from DB.
   * @request GET:/api/config/dropdowns
   */
  getDropdownConfig = (params: RequestParams = {}) =>
    this.request<void, any>({
      path: `/api/config/dropdowns`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags Configuration
   * @name GetPruefgeraete
   * @summary Get list of testing devices (Prüfgeräte) from DB.
   * @request GET:/api/config/pruefgeraete
   */
  getPruefgeraete = (params: RequestParams = {}) =>
    this.request<void, any>({
      path: `/api/config/pruefgeraete`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags Customers
   * @name ListCustomers
   * @summary List all customers with their repair count.
   * @request GET:/api/customers
   */
  listCustomers = (params: RequestParams = {}) =>
    this.request<void, void>({
      path: `/api/customers`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags Health
   * @name Healthcheck
   * @summary Health check endpoint
   * @request GET:/api/healthz
   */
  healthcheck = (params: RequestParams = {}) =>
    this.request<void, void>({
      path: `/api/healthz`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags Repairs
   * @name ListRepairs
   * @summary Get all repairs as JSON
   * @request GET:/api/list
   */
  listRepairs = (params: RequestParams = {}) =>
    this.request<void, void>({
      path: `/api/list`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags Repairs
   * @name CreateRepair
   * @summary Create a new repair record
   * @request POST:/api/repairs
   */
  createRepair = (params: RequestParams = {}) =>
    this.request<void, void>({
      path: `/api/repairs`,
      method: "POST",
      ...params,
    });
  /**
   * No description
   *
   * @tags Repairs
   * @name GetRepairByQrToken
   * @summary Get a repair record by QR token
   * @request GET:/api/repairs/by-token/{token}
   */
  getRepairByQrToken = (
    { token }: GetRepairByQrTokenParams,
    params: RequestParams = {},
  ) =>
    this.request<void, void>({
      path: `/api/repairs/by-token/${token}`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags Repairs
   * @name UpdateRepair
   * @summary Update an existing repair record
   * @request PUT:/api/repairs/{id}
   */
  updateRepair = ({ id }: UpdateRepairParams, params: RequestParams = {}) =>
    this.request<void, void>({
      path: `/api/repairs/${id}`,
      method: "PUT",
      ...params,
    });
  /**
   * No description
   *
   * @tags Repairs
   * @name GetRepairDisclaimer
   * @summary Download the signed disclaimer PDF for a repair
   * @request GET:/api/repairs/{id}/disclaimer
   */
  getRepairDisclaimer = (
    { id }: GetRepairDisclaimerParams,
    params: RequestParams = {},
  ) =>
    this.request<void, void>({
      path: `/api/repairs/${id}/disclaimer`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags Repair Logs
   * @name ListRepairLogs
   * @summary Get all log entries for a specific repair
   * @request GET:/api/repairs/{repair_id}/logs
   */
  listRepairLogs = (
    { repairId }: ListRepairLogsParams,
    params: RequestParams = {},
  ) =>
    this.request<void, void>({
      path: `/api/repairs/${repairId}/logs`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags Repair Logs
   * @name CreateRepairLog
   * @summary Create a new repair log entry
   * @request POST:/api/repairs/{repair_id}/logs
   */
  createRepairLog = (
    { repairId }: CreateRepairLogParams,
    data: RepairLogCreate,
    params: RequestParams = {},
  ) =>
    this.request<void, void>({
      path: `/api/repairs/${repairId}/logs`,
      method: "POST",
      body: data,
      type: ContentType.Json,
      ...params,
    });
  /**
   * No description
   *
   * @tags Repair Logs
   * @name DeleteRepairLog
   * @summary Delete a repair log entry
   * @request DELETE:/api/repairs/{repair_id}/logs/{log_id}
   */
  deleteRepairLog = (
    { repairId, logId }: DeleteRepairLogParams,
    params: RequestParams = {},
  ) =>
    this.request<void, void>({
      path: `/api/repairs/${repairId}/logs/${logId}`,
      method: "DELETE",
      ...params,
    });
  /**
   * No description
   *
   * @tags Repair Logs
   * @name GetRepairLog
   * @summary Get a specific repair log entry
   * @request GET:/api/repairs/{repair_id}/logs/{log_id}
   */
  getRepairLog = (
    { repairId, logId }: GetRepairLogParams,
    params: RequestParams = {},
  ) =>
    this.request<void, void>({
      path: `/api/repairs/${repairId}/logs/${logId}`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags VDE Tests
   * @name ListVdeTests
   * @summary Get all VDE test entries for a specific repair
   * @request GET:/api/repairs/{repair_id}/vde-tests
   */
  listVdeTests = (
    { repairId }: ListVdeTestsParams,
    params: RequestParams = {},
  ) =>
    this.request<void, void>({
      path: `/api/repairs/${repairId}/vde-tests`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags VDE Tests
   * @name CreateVdeTest
   * @summary Create a new VDE test entry
   * @request POST:/api/repairs/{repair_id}/vde-tests
   */
  createVdeTest = (
    { repairId }: CreateVdeTestParams,
    data: VdeTestCreate,
    params: RequestParams = {},
  ) =>
    this.request<void, void>({
      path: `/api/repairs/${repairId}/vde-tests`,
      method: "POST",
      body: data,
      type: ContentType.Json,
      ...params,
    });
  /**
   * No description
   *
   * @tags VDE Tests
   * @name GetVdeTest
   * @summary Get a specific VDE test entry
   * @request GET:/api/repairs/{repair_id}/vde-tests/{test_id}
   */
  getVdeTest = (
    { repairId, testId }: GetVdeTestParams,
    params: RequestParams = {},
  ) =>
    this.request<void, void>({
      path: `/api/repairs/${repairId}/vde-tests/${testId}`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags Settings
   * @name ListSettings
   * @summary List all active settings grouped by category.
   * @request GET:/api/settings
   */
  listSettings = (params: RequestParams = {}) =>
    this.request<void, any>({
      path: `/api/settings`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags Settings
   * @name CreateSetting
   * @summary Create a new setting entry.
   * @request POST:/api/settings
   */
  createSetting = (params: RequestParams = {}) =>
    this.request<void, void>({
      path: `/api/settings`,
      method: "POST",
      ...params,
    });
  /**
   * No description
   *
   * @tags Settings
   * @name ListAllSettings
   * @summary List all settings (including inactive) for admin management.
   * @request GET:/api/settings/all
   */
  listAllSettings = (params: RequestParams = {}) =>
    this.request<void, any>({
      path: `/api/settings/all`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags Settings
   * @name DeleteSetting
   * @summary Delete a setting entry.
   * @request DELETE:/api/settings/{setting_id}
   */
  deleteSetting = (
    { settingId }: DeleteSettingParams,
    params: RequestParams = {},
  ) =>
    this.request<void, void>({
      path: `/api/settings/${settingId}`,
      method: "DELETE",
      ...params,
    });
  /**
   * No description
   *
   * @tags Settings
   * @name UpdateSetting
   * @summary Update a setting entry.
   * @request PUT:/api/settings/{setting_id}
   */
  updateSetting = (
    { settingId }: UpdateSettingParams,
    params: RequestParams = {},
  ) =>
    this.request<void, void>({
      path: `/api/settings/${settingId}`,
      method: "PUT",
      ...params,
    });
}
