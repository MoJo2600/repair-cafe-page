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
  APIResponse,
  AppConfigResponse,
  AuthConfigResponse,
  AuthResponse,
  CreateOrUploadRepairCancellationParams,
  CreateOrUploadRepairCancellationPayload,
  CreateRepairLogParams,
  CreateVdeTestParams,
  CustomerCreate,
  CustomerSearchResponse,
  CustomerSingleResponse,
  CustomerWithRepairCountResponse,
  DeactivateUserParams,
  DeleteCustomerParams,
  DeleteRepairAttachmentParams,
  DeleteRepairLogParams,
  DeleteRepairParams,
  DeleteSettingParams,
  DropdownConfigResponse,
  FeaturesResponse,
  GetCustomerParams,
  GetRepairAttachmentParams,
  GetRepairByQrTokenParams,
  GetRepairCancellationParams,
  GetRepairDisclaimerParams,
  GetRepairLogParams,
  GetStatDataParams,
  GetUserParams,
  GetVdeTestParams,
  GetVdeTestPdfParams,
  IdResponse,
  ListRepairAttachmentsParams,
  ListRepairLogsParams,
  ListRepairsParams,
  ListVdeTestsParams,
  LoginRequest,
  OidcLoginParams,
  PinAutoLockRequest,
  PinDashboardSummaryResponse,
  PinGenerateRequest,
  PinGeneratedResponse,
  PinSessionActionResponse,
  PinSessionStatusResponse,
  PinStatusResponse,
  PinUnlockRequest,
  PrintRepairLabelParams,
  PrintRepairLabelPayload,
  PruefgeraetResponse,
  RepairAttachmentListResponse,
  RepairCreate,
  RepairCreateResponse,
  RepairListResponse,
  RepairLogCreate,
  RepairLogCreateResponse,
  RepairLogListResponse,
  RepairLogSingleResponse,
  RepairLogUpdate,
  RepairResponse,
  RepairSingleResponse,
  RepairUpdate,
  RepairsTimelineResponse,
  SearchCustomersParams,
  SettingCreate,
  SettingResponse,
  SettingSingleResponse,
  SettingUpdate,
  SettingsGroupedResponse,
  UpdateAppConfigPayload,
  UpdateCustomerParams,
  UpdateRepairLogParams,
  UpdateRepairParams,
  UpdateSettingParams,
  UpdateUserParams,
  UploadCancellationTemplatePayload,
  UploadCelebrationSoundPayload,
  UploadDisclaimerTemplatePayload,
  UploadLogoPayload,
  UploadRepairAttachmentsParams,
  UploadRepairAttachmentsPayload,
  UploadRepairDisclaimerParams,
  UploadRepairDisclaimerPayload,
  UserCreate,
  UserListResponse,
  UserSingleResponse,
  UserUpdate,
  VdeTestCreate,
  VdeTestCreateResponse,
  VdeTestListResponse,
  VdeTestSingleResponse,
} from "./data-contracts";
import { ContentType, HttpClient, RequestParams } from "./http-client";

export class Api<
  SecurityDataType = unknown,
> extends HttpClient<SecurityDataType> {
  /**
   * No description
   *
   * @tags Auth
   * @name AuthConfig
   * @summary Login options for the login page.
   * @request GET:/api/auth/config
   */
  authConfig = (params: RequestParams = {}) =>
    this.request<AuthConfigResponse, any>({
      path: `/api/auth/config`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Auth
   * @name Login
   * @summary Authenticate with username and password.
   * @request POST:/api/auth/login
   */
  login = (body: LoginRequest, params: RequestParams = {}) =>
    this.request<AuthResponse, void>({
      path: `/api/auth/login`,
      method: "POST",
      body: body,
      type: ContentType.Json,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Auth
   * @name Logout
   * @summary Invalidate the current session cookie.
   * @request POST:/api/auth/logout
   */
  logout = (params: RequestParams = {}) =>
    this.request<APIResponse, void>({
      path: `/api/auth/logout`,
      method: "POST",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Auth
   * @name Me
   * @summary Return the currently authenticated user's profile.
   * @request GET:/api/auth/me
   */
  me = (params: RequestParams = {}) =>
    this.request<AuthResponse, void>({
      path: `/api/auth/me`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Auth
   * @name PinStatus
   * @summary Return the current user's PIN status, never the PIN itself.
   * @request GET:/api/auth/me/pin
   */
  pinStatus = (params: RequestParams = {}) =>
    this.request<PinStatusResponse, void>({
      path: `/api/auth/me/pin`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Auth
   * @name GeneratePin
   * @summary Generate or explicitly replace the current user's local PIN, revealing it once.
   * @request POST:/api/auth/me/pin
   */
  generatePin = (body: PinGenerateRequest, params: RequestParams = {}) =>
    this.request<PinGeneratedResponse, void>({
      path: `/api/auth/me/pin`,
      method: "POST",
      body: body,
      type: ContentType.Json,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Auth
   * @name OidcCallback
   * @summary SSO callback; logs the user in and redirects into the app.
   * @request GET:/api/auth/oidc/callback
   */
  oidcCallback = (params: RequestParams = {}) =>
    this.request<any, void>({
      path: `/api/auth/oidc/callback`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags Auth
   * @name OidcLogin
   * @summary Start the SSO login (redirects to the identity provider).
   * @request GET:/api/auth/oidc/login
   */
  oidcLogin = (query: OidcLoginParams = {}, params: RequestParams = {}) =>
    this.request<any, void>({
      path: `/api/auth/oidc/login`,
      method: "GET",
      query: query,
      ...params,
    });
  /**
   * No description
   *
   * @tags Auth
   * @name PinSessionStatus
   * @summary Return whether the current authenticated browser session is unlocked.
   * @request GET:/api/auth/pin-session
   */
  pinSessionStatus = (params: RequestParams = {}) =>
    this.request<PinSessionStatusResponse, void>({
      path: `/api/auth/pin-session`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Auth
   * @name RecordPinSessionActivity
   * @summary Record real user activity for the session idle timeout.
   * @request POST:/api/auth/pin-session/activity
   */
  recordPinSessionActivity = (params: RequestParams = {}) =>
    this.request<PinSessionActionResponse, void>({
      path: `/api/auth/pin-session/activity`,
      method: "POST",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Auth
   * @name SetPinAutoLock
   * @summary Switch the idle auto-lock for this browser session (e.g. off on a personal device).
   * @request PUT:/api/auth/pin-session/auto-lock
   */
  setPinAutoLock = (body: PinAutoLockRequest, params: RequestParams = {}) =>
    this.request<PinSessionActionResponse, void>({
      path: `/api/auth/pin-session/auto-lock`,
      method: "PUT",
      body: body,
      type: ContentType.Json,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Auth
   * @name PinDashboardSummary
   * @summary Return aggregate dashboard metrics allowed on the PIN lock screen and unified dashboard.
   * @request GET:/api/auth/pin-session/dashboard
   */
  pinDashboardSummary = (params: RequestParams = {}) =>
    this.request<PinDashboardSummaryResponse, void>({
      path: `/api/auth/pin-session/dashboard`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Auth
   * @name LockPinSession
   * @summary Lock the current authenticated browser session.
   * @request POST:/api/auth/pin-session/lock
   */
  lockPinSession = (params: RequestParams = {}) =>
    this.request<PinSessionActionResponse, void>({
      path: `/api/auth/pin-session/lock`,
      method: "POST",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Auth
   * @name UnlockPinSession
   * @summary Switch to the active helper who owns the submitted PIN.
   * @request POST:/api/auth/pin-session/unlock
   */
  unlockPinSession = (body: PinUnlockRequest, params: RequestParams = {}) =>
    this.request<AuthResponse, void>({
      path: `/api/auth/pin-session/unlock`,
      method: "POST",
      body: body,
      type: ContentType.Json,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Configuration
   * @name GetAppConfig
   * @summary Get application-level configuration (organisation name and website).
   * @request GET:/api/config/app-config
   */
  getAppConfig = (params: RequestParams = {}) =>
    this.request<AppConfigResponse, any>({
      path: `/api/config/app-config`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Configuration
   * @name UpdateAppConfig
   * @summary Update application-level configuration (admin only).
   * @request PUT:/api/config/app-config
   */
  updateAppConfig = (
    body: UpdateAppConfigPayload,
    params: RequestParams = {},
  ) =>
    this.request<AppConfigResponse, void>({
      path: `/api/config/app-config`,
      method: "PUT",
      body: body,
      type: ContentType.Json,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Configuration
   * @name GetCancellationTemplate
   * @summary Serve the active cancellation PDF template for inline display.
   * @request GET:/api/config/cancellation
   */
  getCancellationTemplate = (params: RequestParams = {}) =>
    this.request<void, void>({
      path: `/api/config/cancellation`,
      method: "GET",
      ...params,
    });
  /**
   * @description The PDF must contain AcroForm fields named 'date' and 'signature'.<br/>Takes effect immediately without a server restart.<br/>
   *
   * @tags Configuration
   * @name UploadCancellationTemplate
   * @summary Upload and activate a new cancellation PDF template (admin only).
   * @request POST:/api/config/cancellation
   */
  uploadCancellationTemplate = (
    data: UploadCancellationTemplatePayload,
    params: RequestParams = {},
  ) =>
    this.request<APIResponse, void>({
      path: `/api/config/cancellation`,
      method: "POST",
      body: data,
      type: ContentType.FormData,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Configuration
   * @name ResetCelebrationSound
   * @summary Remove the custom celebration sound and go back to the bundled fanfare (admin only).
   * @request DELETE:/api/config/celebration-sound
   */
  resetCelebrationSound = (params: RequestParams = {}) =>
    this.request<APIResponse, any>({
      path: `/api/config/celebration-sound`,
      method: "DELETE",
      format: "json",
      ...params,
    });
  /**
   * @description Public because the lock screen dashboard celebrates too.<br/>Falls back to the bundled fanfare when no custom sound has been uploaded.<br/>
   *
   * @tags Configuration
   * @name GetCelebrationSound
   * @summary Serve the MP3 played when a repair succeeds.
   * @request GET:/api/config/celebration-sound
   */
  getCelebrationSound = (params: RequestParams = {}) =>
    this.request<Blob, any>({
      path: `/api/config/celebration-sound`,
      method: "GET",
      ...params,
    });
  /**
   * @description Accepts an MP3 file of at most 2 MB. Takes effect on the next page load.<br/>
   *
   * @tags Configuration
   * @name UploadCelebrationSound
   * @summary Upload and activate a custom celebration sound (admin only).
   * @request POST:/api/config/celebration-sound
   */
  uploadCelebrationSound = (
    data: UploadCelebrationSoundPayload,
    params: RequestParams = {},
  ) =>
    this.request<APIResponse, void>({
      path: `/api/config/celebration-sound`,
      method: "POST",
      body: data,
      type: ContentType.FormData,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Configuration
   * @name GetDisclaimerTemplate
   * @summary Serve the active disclaimer PDF template for inline display.
   * @request GET:/api/config/disclaimer
   */
  getDisclaimerTemplate = (params: RequestParams = {}) =>
    this.request<void, void>({
      path: `/api/config/disclaimer`,
      method: "GET",
      ...params,
    });
  /**
   * @description The PDF must contain AcroForm fields named 'date' and 'signature'.<br/>Takes effect immediately without a server restart.<br/>
   *
   * @tags Configuration
   * @name UploadDisclaimerTemplate
   * @summary Upload and activate a new disclaimer PDF template (admin only).
   * @request POST:/api/config/disclaimer
   */
  uploadDisclaimerTemplate = (
    data: UploadDisclaimerTemplatePayload,
    params: RequestParams = {},
  ) =>
    this.request<APIResponse, void>({
      path: `/api/config/disclaimer`,
      method: "POST",
      body: data,
      type: ContentType.FormData,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Configuration
   * @name GetDropdownConfig
   * @summary Get dropdown configuration data from DB.
   * @request GET:/api/config/dropdowns
   */
  getDropdownConfig = (params: RequestParams = {}) =>
    this.request<DropdownConfigResponse, any>({
      path: `/api/config/dropdowns`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Configuration
   * @name GetFeatures
   * @summary Return server-side feature flags derived from environment variables.
   * @request GET:/api/config/features
   */
  getFeatures = (params: RequestParams = {}) =>
    this.request<FeaturesResponse, any>({
      path: `/api/config/features`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * @description Falls back to the bundled default when no custom logo has been uploaded.<br/>
   *
   * @tags Configuration
   * @name GetLogo
   * @summary Serve the active logo image.
   * @request GET:/api/config/logo
   */
  getLogo = (params: RequestParams = {}) =>
    this.request<Blob, void>({
      path: `/api/config/logo`,
      method: "GET",
      ...params,
    });
  /**
   * @description Accepts PNG or JPEG. The image is validated and stored as PNG.<br/>Takes effect immediately without a server restart.<br/>
   *
   * @tags Configuration
   * @name UploadLogo
   * @summary Upload and activate a new logo image (admin only).
   * @request POST:/api/config/logo
   */
  uploadLogo = (data: UploadLogoPayload, params: RequestParams = {}) =>
    this.request<APIResponse, void>({
      path: `/api/config/logo`,
      method: "POST",
      body: data,
      type: ContentType.FormData,
      format: "json",
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
    this.request<PruefgeraetResponse[], any>({
      path: `/api/config/pruefgeraete`,
      method: "GET",
      format: "json",
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
    this.request<
      {
        count?: number;
        data?: CustomerWithRepairCountResponse[];
        reply?: string;
      },
      void
    >({
      path: `/api/customers`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Customers
   * @name CreateCustomer
   * @summary Create a new customer.
   * @request POST:/api/customers
   */
  createCustomer = (body: CustomerCreate, params: RequestParams = {}) =>
    this.request<CustomerSingleResponse, void>({
      path: `/api/customers`,
      method: "POST",
      body: body,
      type: ContentType.Json,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Customers
   * @name SearchCustomers
   * @summary Search customers by name, phone or email.
   * @request GET:/api/customers/search
   */
  searchCustomers = (
    query: SearchCustomersParams = {},
    params: RequestParams = {},
  ) =>
    this.request<CustomerSearchResponse, void>({
      path: `/api/customers/search`,
      method: "GET",
      query: query,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Customers
   * @name DeleteCustomer
   * @summary Delete a customer (sets customer_id to NULL on linked repairs).
   * @request DELETE:/api/customers/{customer_id}
   */
  deleteCustomer = (
    { customerId }: DeleteCustomerParams,
    params: RequestParams = {},
  ) =>
    this.request<IdResponse, void>({
      path: `/api/customers/${customerId}`,
      method: "DELETE",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Customers
   * @name GetCustomer
   * @summary Get a single customer by ID.
   * @request GET:/api/customers/{customer_id}
   */
  getCustomer = (
    { customerId }: GetCustomerParams,
    params: RequestParams = {},
  ) =>
    this.request<CustomerSingleResponse, void>({
      path: `/api/customers/${customerId}`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Customers
   * @name UpdateCustomer
   * @summary Update a customer.
   * @request PUT:/api/customers/{customer_id}
   */
  updateCustomer = (
    { customerId }: UpdateCustomerParams,
    body: CustomerCreate,
    params: RequestParams = {},
  ) =>
    this.request<CustomerSingleResponse, void>({
      path: `/api/customers/${customerId}`,
      method: "PUT",
      body: body,
      type: ContentType.Json,
      format: "json",
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
  listRepairs = (query: ListRepairsParams = {}, params: RequestParams = {}) =>
    this.request<RepairListResponse, void>({
      path: `/api/list`,
      method: "GET",
      query: query,
      format: "json",
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
  createRepair = (body: RepairCreate, params: RequestParams = {}) =>
    this.request<RepairCreateResponse, void>({
      path: `/api/repairs`,
      method: "POST",
      body: body,
      type: ContentType.Json,
      format: "json",
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
    this.request<RepairSingleResponse, void>({
      path: `/api/repairs/by-token/${token}`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Repairs
   * @name GetRepairsTimeline
   * @summary Get repair counts grouped by week and status for the last 12 months.
   * @request GET:/api/repairs/stats/timeline
   */
  getRepairsTimeline = (params: RequestParams = {}) =>
    this.request<RepairsTimelineResponse, any>({
      path: `/api/repairs/stats/timeline`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Repairs
   * @name DeleteRepair
   * @summary Delete a repair record and its associated files on disk.
   * @request DELETE:/api/repairs/{id}
   */
  deleteRepair = ({ id }: DeleteRepairParams, params: RequestParams = {}) =>
    this.request<IdResponse, void>({
      path: `/api/repairs/${id}`,
      method: "DELETE",
      format: "json",
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
  updateRepair = (
    { id }: UpdateRepairParams,
    body: RepairUpdate,
    params: RequestParams = {},
  ) =>
    this.request<
      {
        data?: RepairResponse;
        /** @example "done" */
        reply?: string;
      },
      void
    >({
      path: `/api/repairs/${id}`,
      method: "PUT",
      body: body,
      type: ContentType.Json,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Repairs
   * @name GetRepairCancellation
   * @summary Download the signed cancellation PDF for a repair
   * @request GET:/api/repairs/{id}/cancellation
   */
  getRepairCancellation = (
    { id }: GetRepairCancellationParams,
    params: RequestParams = {},
  ) =>
    this.request<void, void>({
      path: `/api/repairs/${id}/cancellation`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags Repairs
   * @name CreateOrUploadRepairCancellation
   * @summary Generate a signed cancellation PDF from a base64 signature or upload a pre-signed PDF.
   * @request POST:/api/repairs/{id}/cancellation
   */
  createOrUploadRepairCancellation = (
    { id }: CreateOrUploadRepairCancellationParams,
    body: CreateOrUploadRepairCancellationPayload,
    params: RequestParams = {},
  ) =>
    this.request<APIResponse, void>({
      path: `/api/repairs/${id}/cancellation`,
      method: "POST",
      body: body,
      type: ContentType.Json,
      format: "json",
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
   * @tags Repairs
   * @name UploadRepairDisclaimer
   * @summary Upload a pre-signed disclaimer PDF for a repair.
   * @request POST:/api/repairs/{id}/disclaimer
   */
  uploadRepairDisclaimer = (
    { id }: UploadRepairDisclaimerParams,
    data: UploadRepairDisclaimerPayload,
    params: RequestParams = {},
  ) =>
    this.request<APIResponse, void>({
      path: `/api/repairs/${id}/disclaimer`,
      method: "POST",
      body: data,
      type: ContentType.FormData,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Repairs
   * @name PrintRepairLabel
   * @summary Print a QR code label for a repair on a label printer.
   * @request POST:/api/repairs/{id}/print-label
   */
  printRepairLabel = (
    { id }: PrintRepairLabelParams,
    body: PrintRepairLabelPayload,
    params: RequestParams = {},
  ) =>
    this.request<APIResponse, void>({
      path: `/api/repairs/${id}/print-label`,
      method: "POST",
      body: body,
      type: ContentType.Json,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Attachments
   * @name ListRepairAttachments
   * @summary List all attachments for a repair
   * @request GET:/api/repairs/{repair_id}/attachments
   */
  listRepairAttachments = (
    { repairId, ...query }: ListRepairAttachmentsParams,
    params: RequestParams = {},
  ) =>
    this.request<RepairAttachmentListResponse, void>({
      path: `/api/repairs/${repairId}/attachments`,
      method: "GET",
      query: query,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Attachments
   * @name UploadRepairAttachments
   * @summary Upload one or more files to a repair
   * @request POST:/api/repairs/{repair_id}/attachments
   */
  uploadRepairAttachments = (
    { repairId }: UploadRepairAttachmentsParams,
    data: UploadRepairAttachmentsPayload,
    params: RequestParams = {},
  ) =>
    this.request<RepairAttachmentListResponse, void>({
      path: `/api/repairs/${repairId}/attachments`,
      method: "POST",
      body: data,
      type: ContentType.FormData,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Attachments
   * @name DeleteRepairAttachment
   * @summary Delete a repair attachment (record + file on disk)
   * @request DELETE:/api/repairs/{repair_id}/attachments/{attachment_id}
   */
  deleteRepairAttachment = (
    { repairId, attachmentId }: DeleteRepairAttachmentParams,
    params: RequestParams = {},
  ) =>
    this.request<APIResponse, void>({
      path: `/api/repairs/${repairId}/attachments/${attachmentId}`,
      method: "DELETE",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Attachments
   * @name GetRepairAttachment
   * @summary Download / serve a single attachment file
   * @request GET:/api/repairs/{repair_id}/attachments/{attachment_id}
   */
  getRepairAttachment = (
    { repairId, attachmentId }: GetRepairAttachmentParams,
    params: RequestParams = {},
  ) =>
    this.request<void, void>({
      path: `/api/repairs/${repairId}/attachments/${attachmentId}`,
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
    this.request<RepairLogListResponse, void>({
      path: `/api/repairs/${repairId}/logs`,
      method: "GET",
      format: "json",
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
    this.request<RepairLogCreateResponse, void>({
      path: `/api/repairs/${repairId}/logs`,
      method: "POST",
      body: data,
      type: ContentType.Json,
      format: "json",
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
    this.request<APIResponse, void>({
      path: `/api/repairs/${repairId}/logs/${logId}`,
      method: "DELETE",
      format: "json",
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
    this.request<RepairLogSingleResponse, void>({
      path: `/api/repairs/${repairId}/logs/${logId}`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Repair Logs
   * @name UpdateRepairLog
   * @summary Update an existing repair log entry.
   * @request PUT:/api/repairs/{repair_id}/logs/{log_id}
   */
  updateRepairLog = (
    { repairId, logId }: UpdateRepairLogParams,
    body: RepairLogUpdate,
    params: RequestParams = {},
  ) =>
    this.request<RepairLogSingleResponse, void>({
      path: `/api/repairs/${repairId}/logs/${logId}`,
      method: "PUT",
      body: body,
      type: ContentType.Json,
      format: "json",
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
    this.request<VdeTestListResponse, void>({
      path: `/api/repairs/${repairId}/vde-tests`,
      method: "GET",
      format: "json",
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
    this.request<VdeTestCreateResponse, void>({
      path: `/api/repairs/${repairId}/vde-tests`,
      method: "POST",
      body: data,
      type: ContentType.Json,
      format: "json",
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
    this.request<VdeTestSingleResponse, void>({
      path: `/api/repairs/${repairId}/vde-tests/${testId}`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags VDE Tests
   * @name GetVdeTestPdf
   * @summary Download a VDE Prüfprotokoll as PDF for the given test.
   * @request GET:/api/repairs/{repair_id}/vde-tests/{test_id}/pdf
   */
  getVdeTestPdf = (
    { repairId, testId }: GetVdeTestPdfParams,
    params: RequestParams = {},
  ) =>
    this.request<Blob, void>({
      path: `/api/repairs/${repairId}/vde-tests/${testId}/pdf`,
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
    this.request<SettingsGroupedResponse, any>({
      path: `/api/settings`,
      method: "GET",
      format: "json",
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
  createSetting = (body: SettingCreate, params: RequestParams = {}) =>
    this.request<SettingSingleResponse, void>({
      path: `/api/settings`,
      method: "POST",
      body: body,
      type: ContentType.Json,
      format: "json",
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
    this.request<
      {
        data?: SettingResponse[];
        reply?: string;
      },
      any
    >({
      path: `/api/settings/all`,
      method: "GET",
      format: "json",
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
    this.request<APIResponse, void>({
      path: `/api/settings/${settingId}`,
      method: "DELETE",
      format: "json",
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
    body: SettingUpdate,
    params: RequestParams = {},
  ) =>
    this.request<SettingSingleResponse, void>({
      path: `/api/settings/${settingId}`,
      method: "PUT",
      body: body,
      type: ContentType.Json,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Data
   * @name GetStatData
   * @summary Get statistics data for charts
   * @request GET:/api/stat-data/{type}
   */
  getStatData = ({ type }: GetStatDataParams, params: RequestParams = {}) =>
    this.request<void, any>({
      path: `/api/stat-data/${type}`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags Users
   * @name ListUsers
   * @summary List all users.
   * @request GET:/api/users
   */
  listUsers = (params: RequestParams = {}) =>
    this.request<UserListResponse, void>({
      path: `/api/users`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Users
   * @name CreateUser
   * @summary Create a new user.
   * @request POST:/api/users
   */
  createUser = (body: UserCreate, params: RequestParams = {}) =>
    this.request<UserSingleResponse, void>({
      path: `/api/users`,
      method: "POST",
      body: body,
      type: ContentType.Json,
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Users
   * @name DeactivateUser
   * @summary Soft-delete a user by setting is_active=False.
   * @request DELETE:/api/users/{user_id}
   */
  deactivateUser = (
    { userId }: DeactivateUserParams,
    params: RequestParams = {},
  ) =>
    this.request<APIResponse, void>({
      path: `/api/users/${userId}`,
      method: "DELETE",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Users
   * @name GetUser
   * @summary Get a single user by ID.
   * @request GET:/api/users/{user_id}
   */
  getUser = ({ userId }: GetUserParams, params: RequestParams = {}) =>
    this.request<UserSingleResponse, void>({
      path: `/api/users/${userId}`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @tags Users
   * @name UpdateUser
   * @summary Update an existing user.
   * @request PUT:/api/users/{user_id}
   */
  updateUser = (
    { userId }: UpdateUserParams,
    body: UserUpdate,
    params: RequestParams = {},
  ) =>
    this.request<UserSingleResponse, void>({
      path: `/api/users/${userId}`,
      method: "PUT",
      body: body,
      type: ContentType.Json,
      format: "json",
      ...params,
    });
}
