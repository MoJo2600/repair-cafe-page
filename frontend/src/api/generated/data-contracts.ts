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

export interface APIResponse {
  /**
   * Error message if reply is error
   * @default null
   */
  error?: string | null;
  /**
   * Response message
   * @default null
   */
  message?: string | null;
  /** Response status (done, error) */
  reply: string;
}

export interface AppConfigResponse {
  /**
   * Application base URL used for QR code links on labels
   * @default ""
   */
  app_url?: string;
  /**
   * Organisation display name
   * @default "Repair Café"
   */
  org_name?: string;
  /**
   * Organisation website URL printed on the label
   * @default ""
   */
  org_website?: string;
}

export interface AuthConfigResponse {
  oidc_enabled: boolean;
}

export interface AuthResponse {
  data?: UserResponse | null;
  /**
   * Error message if reply is error
   * @default null
   */
  error?: string | null;
  /** Response status (done, error) */
  reply: string;
}

export interface CustomerCreate {
  /**
   * @format email
   * @maxLength 100
   * @default null
   */
  email?: string | null;
  /**
   * @minLength 1
   * @maxLength 100
   */
  nachname: string;
  /**
   * @maxLength 40
   * @default null
   */
  telefon?: string | null;
  /**
   * @minLength 1
   * @maxLength 100
   */
  vorname: string;
}

export interface CustomerResponse {
  /** @format date-time */
  created_at: string;
  /** @default null */
  email?: string | null;
  id: number;
  nachname: string;
  /** @default null */
  telefon?: string | null;
  vorname: string;
}

export interface CustomerSearchResponse {
  data: CustomerResponse[];
  /** Response status (done, error) */
  reply: string;
}

export interface CustomerSingleResponse {
  data: CustomerResponse;
  /**
   * Error message if reply is error
   * @default null
   */
  error?: string | null;
  /**
   * Response message
   * @default null
   */
  message?: string | null;
  /** Response status (done, error) */
  reply: string;
}

export interface CustomerWithRepairCountResponse {
  /** @format date-time */
  created_at: string;
  /** @default null */
  email?: string | null;
  id: number;
  nachname: string;
  /**
   * Number of repairs for this customer
   * @default 0
   */
  repair_count?: number;
  /** @default null */
  telefon?: string | null;
  vorname: string;
}

export interface DropdownConfigResponse {
  repair_type: SettingOption[];
}

export interface FeaturesResponse {
  /**
   * Whether the label printer is enabled
   * @default false
   */
  label_printer?: boolean;
}

export interface IdResponse {
  /**
   * Error message if reply is error
   * @default null
   */
  error?: string | null;
  id: number;
  /**
   * Response message
   * @default null
   */
  message?: string | null;
  /** Response status (done, error) */
  reply: string;
}

export interface LoginRequest {
  /** @minLength 1 */
  password: string;
  /**
   * @minLength 1
   * @maxLength 100
   */
  username: string;
}

export interface PinAutoLockRequest {
  enabled: boolean;
}

export interface PinDashboardCategoryCount {
  /** Total repairs in this category */
  count: number;
  /** Predefined repair category name */
  name: string;
}

export interface PinDashboardRepairItem {
  /**
   * Predefined repair category name
   * @default null
   */
  category?: string | null;
  /** Repair ID */
  id: number;
}

export interface PinDashboardSummaryResponse {
  in_progress_items?: PinDashboardRepairItem[];
  in_progress_repairs: number;
  /** @default null */
  next_repair_category?: string | null;
  /** @default null */
  next_repair_id?: number | null;
  not_repaired_repairs: number;
  open_repairs: number;
  repaired_repairs: number;
  /** @default null */
  success_rate?: number | null;
  timeline?: RepairsTimelinePoint[];
  top_categories?: PinDashboardCategoryCount[];
  total_repairs: number;
}

export interface PinGenerateRequest {
  /** @default false */
  replace?: boolean;
}

export interface PinGeneratedResponse {
  /** @pattern ^[0-9]{6}$ */
  pin_code: string;
}

export interface PinSessionActionResponse {
  locked: boolean;
}

export interface PinSessionStatusResponse {
  /**
   * Idle auto-lock active for this session
   * @default true
   */
  auto_lock_enabled?: boolean;
  eligible: boolean;
  /**
   * Seconds without activity until auto-lock
   * @default 60
   */
  idle_timeout_seconds?: number;
  locked: boolean;
  /** @default true */
  pin_unlock_available?: boolean;
  user?: UserResponse | null;
}

export interface PinStatusResponse {
  can_generate: boolean;
  has_pin: boolean;
  mode: "local" | "oidc";
}

export interface PinUnlockRequest {
  /** @pattern ^[0-9]{6}$ */
  pin_code: string;
}

export interface PruefgeraetResponse {
  /** Setting ID */
  id: number;
  /** Device name */
  name: string;
  /**
   * Device serial number
   * @default null
   */
  serial_number?: string | null;
}

export interface RepairAttachmentListResponse {
  /** @default [] */
  data?: RepairAttachmentResponse[];
  /** Response status (done, error) */
  reply: string;
  /** Total number of attachments */
  total: number;
}

export interface RepairAttachmentResponse {
  /** One of: log_entry, device_photo, disclaimer, misc */
  attachment_type: string;
  content_type: string;
  id: number;
  /** @default null */
  log_id?: number | null;
  original_filename: string;
  repair_id: number;
  /** File size in bytes */
  size: number;
  stored_filename: string;
  /** @format date-time */
  uploaded_at: string;
  uploaded_by?: UserResponse | null;
  /** @default null */
  uploaded_by_id?: number | null;
}

export interface RepairCreate {
  /**
   * Link to existing customer
   * @default null
   */
  customer_id?: number | null;
  /**
   * Date of repair intake
   * @format date
   */
  datum: string;
  /**
   * Defect description
   * @maxLength 400
   * @default null
   */
  defekt_besch?: string | null;
  /**
   * Email address
   * @format email
   * @maxLength 100
   * @default null
   */
  email?: string | null;
  /**
   * Device type
   * @minLength 1
   * @maxLength 100
   */
  geraet_art: string;
  /**
   * Last name
   * @minLength 1
   * @maxLength 100
   */
  nachname: string;
  /** FK to repair type setting */
  repair_type_id: number;
  /**
   * Phone number
   * @maxLength 40
   * @default null
   */
  telefon?: string | null;
  /**
   * Signature image as base64
   * @default null
   */
  unterschrift?: string | null;
  /**
   * First name
   * @minLength 1
   * @maxLength 100
   */
  vorname: string;
}

export interface RepairCreateResponse {
  data?: RepairResponse | null;
  /**
   * Error message if reply is error
   * @default null
   */
  error?: string | null;
  /**
   * Created repair ID
   * @default null
   */
  id?: number | null;
  /**
   * Response message
   * @default null
   */
  message?: string | null;
  /** Response status (done, error) */
  reply: string;
}

export interface RepairListItem {
  /**
   * Timestamp when the repair was closed
   * @format date-time
   * @default null
   */
  closed_at?: string | null;
  created_by?: UserResponse | null;
  /**
   * User who created the repair record
   * @default null
   */
  created_by_id?: number | null;
  customer?: CustomerResponse | null;
  /**
   * Linked customer ID
   * @default null
   */
  customer_id?: number | null;
  /**
   * Date of repair intake
   * @format date
   */
  datum: string;
  /**
   * Defect description
   * @maxLength 400
   * @default null
   */
  defekt_besch?: string | null;
  /**
   * Attachment ID of the newest device photo, if any
   * @default null
   */
  device_photo_id?: number | null;
  /**
   * DIN test performed
   * @default null
   */
  din_pruef?: boolean | null;
  /**
   * Device type
   * @minLength 1
   * @maxLength 100
   */
  geraet_art: string;
  /** Repair ID */
  id: number;
  latest_log?: RepairLogResponse | null;
  /**
   * QR code token
   * @maxLength 32
   */
  qr_token: string;
  repair_type?: SettingResponse | null;
  /**
   * FK to repair type setting
   * @default null
   */
  repair_type_id?: number | null;
  /**
   * Repair description
   * @maxLength 400
   * @default null
   */
  reparatur_besch?: string | null;
  /**
   * Repair duration in minutes
   * @min 0
   * @default null
   */
  reparatur_dauer?: number | null;
  /**
   * Repair status
   * @default "Offen"
   * @pattern ^(Offen|In Bearbeitung|Repariert|Nicht Repariert)$
   */
  status?: string;
  /**
   * Additional detail for repair status
   * @maxLength 100
   * @default null
   */
  status_detail?: string | null;
  /**
   * Signature image as base64
   * @default null
   */
  unterschrift?: string | null;
  /**
   * Liability disclaimer signed
   * @default null
   */
  unterschrift_haft?: boolean | null;
  user?: UserResponse | null;
  /**
   * Assigned reparateur (user FK)
   * @default null
   */
  user_id?: number | null;
}

export interface RepairListResponse {
  /** Number of repairs returned */
  count: number;
  data: RepairListItem[];
  /** Response status (done, error) */
  reply: string;
}

export interface RepairLogCreate {
  /**
   * Entry type: 'work' for work sessions, 'status_change' for status transitions
   * @maxLength 20
   * @default "work"
   */
  log_type?: string;
  /** Repair ID this log belongs to */
  repair_id: number;
  /**
   * Repair description
   * @maxLength 400
   * @default ""
   */
  reparatur_besch?: string;
  /**
   * Repair duration in minutes
   * @min 0
   * @default 0
   */
  reparatur_dauer?: number;
  /**
   * Status before the transition
   * @maxLength 20
   * @default null
   */
  status_from?: string | null;
  /**
   * Status after the transition
   * @maxLength 20
   * @default null
   */
  status_to?: string | null;
  /**
   * Assigned reparateur (user FK)
   * @default null
   */
  user_id?: number | null;
}

export interface RepairLogCreateResponse {
  data: RepairLogResponse;
  /**
   * Error message if reply is error
   * @default null
   */
  error?: string | null;
  /** Created repair log ID */
  id: number;
  /**
   * Response message
   * @default null
   */
  message?: string | null;
  /** Response status (done, error) */
  reply: string;
}

export interface RepairLogListResponse {
  data: RepairLogResponse[];
  /** Response status (done, error) */
  reply: string;
  /** Total number of repair logs */
  total: number;
}

export interface RepairLogResponse {
  /**
   * When this log entry was created
   * @format date-time
   */
  created_at: string;
  /** Repair log ID */
  id: number;
  /**
   * Entry type: 'work' for work sessions, 'status_change' for status transitions
   * @maxLength 20
   * @default "work"
   */
  log_type?: string;
  /** Repair ID this log belongs to */
  repair_id: number;
  /**
   * Repair description
   * @maxLength 400
   * @default ""
   */
  reparatur_besch?: string;
  /**
   * Repair duration in minutes
   * @min 0
   * @default 0
   */
  reparatur_dauer?: number;
  /**
   * Status before the transition
   * @maxLength 20
   * @default null
   */
  status_from?: string | null;
  /**
   * Status after the transition
   * @maxLength 20
   * @default null
   */
  status_to?: string | null;
  user?: UserResponse | null;
  /**
   * Assigned reparateur (user FK)
   * @default null
   */
  user_id?: number | null;
}

export interface RepairLogSingleResponse {
  data: RepairLogResponse;
  /**
   * Error message if reply is error
   * @default null
   */
  error?: string | null;
  /**
   * Response message
   * @default null
   */
  message?: string | null;
  /** Response status (done, error) */
  reply: string;
}

export interface RepairLogUpdate {
  /**
   * @minLength 1
   * @maxLength 400
   * @default null
   */
  reparatur_besch?: string | null;
  /**
   * @min 0
   * @default null
   */
  reparatur_dauer?: number | null;
  /**
   * Assigned reparateur (user FK)
   * @default null
   */
  user_id?: number | null;
}

export interface RepairResponse {
  /**
   * Timestamp when the repair was closed
   * @format date-time
   * @default null
   */
  closed_at?: string | null;
  created_by?: UserResponse | null;
  /**
   * User who created the repair record
   * @default null
   */
  created_by_id?: number | null;
  customer?: CustomerResponse | null;
  /**
   * Linked customer ID
   * @default null
   */
  customer_id?: number | null;
  /**
   * Date of repair intake
   * @format date
   */
  datum: string;
  /**
   * Defect description
   * @maxLength 400
   * @default null
   */
  defekt_besch?: string | null;
  /**
   * DIN test performed
   * @default null
   */
  din_pruef?: boolean | null;
  /**
   * Device type
   * @minLength 1
   * @maxLength 100
   */
  geraet_art: string;
  /** Repair ID */
  id: number;
  /**
   * QR code token
   * @maxLength 32
   */
  qr_token: string;
  repair_type?: SettingResponse | null;
  /**
   * FK to repair type setting
   * @default null
   */
  repair_type_id?: number | null;
  /**
   * Repair description
   * @maxLength 400
   * @default null
   */
  reparatur_besch?: string | null;
  /**
   * Repair duration in minutes
   * @min 0
   * @default null
   */
  reparatur_dauer?: number | null;
  /**
   * Repair status
   * @default "Offen"
   * @pattern ^(Offen|In Bearbeitung|Repariert|Nicht Repariert)$
   */
  status?: string;
  /**
   * Additional detail for repair status
   * @maxLength 100
   * @default null
   */
  status_detail?: string | null;
  /**
   * Signature image as base64
   * @default null
   */
  unterschrift?: string | null;
  /**
   * Liability disclaimer signed
   * @default null
   */
  unterschrift_haft?: boolean | null;
  user?: UserResponse | null;
  /**
   * Assigned reparateur (user FK)
   * @default null
   */
  user_id?: number | null;
}

export interface RepairSingleResponse {
  data: RepairResponse;
  /**
   * Error message if reply is error
   * @default null
   */
  error?: string | null;
  /**
   * Response message
   * @default null
   */
  message?: string | null;
  /** Response status (done, error) */
  reply: string;
}

export interface RepairUpdate {
  /**
   * Date of repair intake
   * @format date
   * @default null
   */
  datum?: string | null;
  /**
   * Defect description
   * @maxLength 400
   * @default null
   */
  defekt_besch?: string | null;
  /**
   * DIN test performed
   * @default null
   */
  din_pruef?: boolean | null;
  /**
   * Device type
   * @minLength 1
   * @maxLength 100
   * @default null
   */
  geraet_art?: string | null;
  /**
   * FK to repair type setting
   * @default null
   */
  repair_type_id?: number | null;
  /**
   * Repair description
   * @maxLength 400
   * @default null
   */
  reparatur_besch?: string | null;
  /**
   * Repair duration in minutes
   * @min 0
   * @default null
   */
  reparatur_dauer?: number | null;
  /**
   * Repair status
   * @default null
   * @pattern ^(Offen|In Bearbeitung|Repariert|Nicht Repariert)$
   */
  status?: string | null;
  /**
   * Additional detail for repair status
   * @maxLength 100
   * @default null
   */
  status_detail?: string | null;
  /**
   * Signature image as base64
   * @default null
   */
  unterschrift?: string | null;
  /**
   * Liability disclaimer signed
   * @default null
   */
  unterschrift_haft?: boolean | null;
  /**
   * Assigned reparateur (user FK)
   * @default null
   */
  user_id?: number | null;
}

export interface RepairsTimelinePoint {
  /**
   * Repairs with status 'Repariert'
   * @default 0
   */
  abgeschlossen?: number;
  /**
   * Repairs with status 'In Bearbeitung'
   * @default 0
   */
  in_bearbeitung?: number;
  /** Human-readable label, e.g. 'KW 20 2026' */
  label: string;
  /**
   * Repairs with status 'Nicht Repariert'
   * @default 0
   */
  nicht_repariert?: number;
  /**
   * Repairs with status 'Offen'
   * @default 0
   */
  offen?: number;
  /** ISO year-week, e.g. '2026-20' */
  week: string;
}

export interface RepairsTimelineResponse {
  /** @default [] */
  data?: RepairsTimelinePoint[];
}

export interface SettingCreate {
  /**
   * @minLength 1
   * @maxLength 50
   */
  category: string;
  /**
   * @minLength 1
   * @maxLength 200
   */
  name: string;
  /**
   * @maxLength 100
   * @default null
   */
  serial_number?: string | null;
  /** @default 0 */
  sort_order?: number;
}

export interface SettingOption {
  id: number;
  name: string;
  /**
   * Only set for testing devices
   * @default null
   */
  serial_number?: string | null;
}

export interface SettingResponse {
  category: string;
  /** @format date-time */
  created_at: string;
  id: number;
  is_active: boolean;
  name: string;
  /** @default null */
  serial_number?: string | null;
  sort_order: number;
  /** @format date-time */
  updated_at: string;
}

export interface SettingSingleResponse {
  data: SettingResponse;
  /**
   * Error message if reply is error
   * @default null
   */
  error?: string | null;
  /**
   * Response message
   * @default null
   */
  message?: string | null;
  /** Response status (done, error) */
  reply: string;
}

export interface SettingUpdate {
  /** @default null */
  is_active?: boolean | null;
  /**
   * @minLength 1
   * @maxLength 200
   * @default null
   */
  name?: string | null;
  /** @default null */
  serial_number?: string | null;
  /** @default null */
  sort_order?: number | null;
}

export type SettingsGroupedResponse = Record<string, SettingOption[]>;

export interface UserCreate {
  /**
   * @format email
   * @maxLength 100
   */
  email: string;
  /** @default true */
  is_active?: boolean;
  /** @default false */
  is_admin?: boolean;
  /**
   * @minLength 1
   * @maxLength 100
   */
  nachname: string;
  /** @minLength 8 */
  password: string;
  /**
   * @minLength 1
   * @maxLength 100
   */
  username: string;
  /**
   * @minLength 1
   * @maxLength 100
   */
  vorname: string;
}

export interface UserListResponse {
  count: number;
  data: UserResponse[];
  /** Response status (done, error) */
  reply: string;
}

export interface UserResponse {
  /** @format date-time */
  created_at: string;
  email: string;
  id: number;
  is_active: boolean;
  is_admin: boolean;
  /** @default null */
  nachname?: string | null;
  username: string;
  /** @default null */
  vorname?: string | null;
}

export interface UserSingleResponse {
  data: UserResponse;
  /**
   * Error message if reply is error
   * @default null
   */
  error?: string | null;
  /**
   * Response message
   * @default null
   */
  message?: string | null;
  /** Response status (done, error) */
  reply: string;
}

export interface UserUpdate {
  /**
   * @format email
   * @maxLength 100
   * @default null
   */
  email?: string | null;
  /** @default null */
  is_active?: boolean | null;
  /** @default null */
  is_admin?: boolean | null;
  /**
   * @minLength 1
   * @maxLength 100
   * @default null
   */
  nachname?: string | null;
  /**
   * @minLength 8
   * @default null
   */
  password?: string | null;
  /**
   * @minLength 1
   * @maxLength 100
   * @default null
   */
  username?: string | null;
  /**
   * @minLength 1
   * @maxLength 100
   * @default null
   */
  vorname?: string | null;
}

export interface VdeTestCreate {
  /**
   * Leakage current test: True=passed, False=failed
   * @default null
   */
  ableitstrom_pruefung?: boolean | null;
  /**
   * Comments/Defects
   * @default null
   */
  bemerkungen?: string | null;
  /**
   * When this test was performed (defaults to now)
   * @format date-time
   * @default null
   */
  created_at?: string | null;
  /**
   * Electrician supervising EuP test
   * @maxLength 100
   * @default null
   */
  electrician?: string | null;
  /** Overall result: True=passed, False=failed */
  gesamtergebnis: boolean;
  /**
   * Insulation test: True=passed, False=failed
   * @default null
   */
  isolationspruefung?: boolean | null;
  /**
   * Testing device name
   * @maxLength 100
   * @default null
   */
  pruefgeraet_name?: string | null;
  /**
   * Testing device serial number
   * @maxLength 100
   * @default null
   */
  pruefgeraet_serial?: string | null;
  /**
   * Tester name (legacy text, derived from prufer_user_id)
   * @maxLength 100
   * @default null
   */
  prufer?: string | null;
  /**
   * FK to users table — who performed the test
   * @default null
   */
  prufer_user_id?: number | null;
  /** Repair ID this test belongs to */
  repair_id: number;
  /**
   * Protection class
   * @default null
   */
  schutzklasse?: string | null;
  /**
   * Protective conductor test: True=passed, False=failed
   * @default null
   */
  schutzleiter_pruefung?: boolean | null;
  /**
   * Housing inspection: True=passed, False=failed
   * @default null
   */
  sichtpruefung_gehaeuse?: boolean | null;
  /**
   * Cable inspection: True=passed, False=failed
   * @default null
   */
  sichtpruefung_kabel?: boolean | null;
  /**
   * Safety devices inspection: True=passed, False=failed
   * @default null
   */
  sichtpruefung_sicherheit?: boolean | null;
  /**
   * Plug inspection: True=passed, False=failed
   * @default null
   */
  sichtpruefung_stecker?: boolean | null;
  /**
   * Strain relief inspection: True=passed, False=failed
   * @default null
   */
  sichtpruefung_zugentlastung?: boolean | null;
}

export interface VdeTestCreateResponse {
  data?: VdeTestResponse | null;
  /**
   * Error message if reply is error
   * @default null
   */
  error?: string | null;
  /**
   * Created VDE test ID
   * @default null
   */
  id?: number | null;
  /**
   * Response message
   * @default null
   */
  message?: string | null;
  /** Response status (done, error) */
  reply: string;
}

export interface VdeTestListResponse {
  data: VdeTestResponse[];
  /** Response status (done, error) */
  reply: string;
  /** Total number of VDE tests */
  total: number;
}

export interface VdeTestResponse {
  /**
   * Leakage current test: True=passed, False=failed
   * @default null
   */
  ableitstrom_pruefung?: boolean | null;
  /**
   * Comments/Defects
   * @default null
   */
  bemerkungen?: string | null;
  /**
   * When this test was performed
   * @format date-time
   */
  created_at: string;
  /**
   * Electrician supervising EuP test
   * @maxLength 100
   * @default null
   */
  electrician?: string | null;
  /** Overall result: True=passed, False=failed */
  gesamtergebnis: boolean;
  /** VDE test ID */
  id: number;
  /**
   * Insulation test: True=passed, False=failed
   * @default null
   */
  isolationspruefung?: boolean | null;
  /**
   * Testing device name
   * @maxLength 100
   * @default null
   */
  pruefgeraet_name?: string | null;
  /**
   * Testing device serial number
   * @maxLength 100
   * @default null
   */
  pruefgeraet_serial?: string | null;
  /**
   * Tester name (legacy text, derived from prufer_user_id)
   * @maxLength 100
   * @default null
   */
  prufer?: string | null;
  /**
   * FK to users table — who performed the test
   * @default null
   */
  prufer_user_id?: number | null;
  /** Repair ID this test belongs to */
  repair_id: number;
  /**
   * Protection class
   * @default null
   */
  schutzklasse?: string | null;
  /**
   * Protective conductor test: True=passed, False=failed
   * @default null
   */
  schutzleiter_pruefung?: boolean | null;
  /**
   * Housing inspection: True=passed, False=failed
   * @default null
   */
  sichtpruefung_gehaeuse?: boolean | null;
  /**
   * Cable inspection: True=passed, False=failed
   * @default null
   */
  sichtpruefung_kabel?: boolean | null;
  /**
   * Safety devices inspection: True=passed, False=failed
   * @default null
   */
  sichtpruefung_sicherheit?: boolean | null;
  /**
   * Plug inspection: True=passed, False=failed
   * @default null
   */
  sichtpruefung_stecker?: boolean | null;
  /**
   * Strain relief inspection: True=passed, False=failed
   * @default null
   */
  sichtpruefung_zugentlastung?: boolean | null;
}

export interface VdeTestSingleResponse {
  data: VdeTestResponse;
  /**
   * Error message if reply is error
   * @default null
   */
  error?: string | null;
  /**
   * Response message
   * @default null
   */
  message?: string | null;
  /** Response status (done, error) */
  reply: string;
}

export interface OidcLoginParams {
  /** Relative path to return to after login */
  next?: string;
}

export interface UpdateAppConfigPayload {
  /** Application base URL for QR code links on printed labels */
  app_url?: string;
  org_name?: string;
  org_website?: string;
}

export interface UploadCancellationTemplatePayload {
  /**
   * PDF file with required AcroForm fields
   * @format binary
   */
  file: File;
}

export interface UploadCelebrationSoundPayload {
  /**
   * MP3 file (max. 2 MB)
   * @format binary
   */
  file: File;
}

export interface UploadDisclaimerTemplatePayload {
  /**
   * PDF file with required AcroForm fields
   * @format binary
   */
  file: File;
}

export interface UploadLogoPayload {
  /**
   * PNG or JPEG image file
   * @format binary
   */
  file: File;
}

export interface SearchCustomersParams {
  /** Search text (name, phone or email) */
  q?: string;
}

export interface DeleteCustomerParams {
  /** Customer ID */
  customerId: number;
}

export interface GetCustomerParams {
  /** Customer ID */
  customerId: number;
}

export interface UpdateCustomerParams {
  /** Customer ID */
  customerId: number;
}

export interface ListRepairsParams {
  /** Filter repairs by customer ID */
  customer_id?: number;
}

export interface GetRepairByQrTokenParams {
  /** QR token of the repair */
  token: string;
}

export interface DeleteRepairParams {
  /** Repair ID */
  id: number;
}

export interface UpdateRepairParams {
  /** ID of the repair to update */
  id: number;
}

export interface GetRepairCancellationParams {
  /** Repair ID */
  id: number;
}

/** Signature as PNG data URL (alternatively a multipart "file" with a signed PDF) */
export interface CreateOrUploadRepairCancellationPayload {
  signature: string;
}

export interface CreateOrUploadRepairCancellationParams {
  /** Repair ID */
  id: number;
}

export interface GetRepairDisclaimerParams {
  /** Repair ID */
  id: number;
}

export interface UploadRepairDisclaimerPayload {
  /** Signed disclaimer PDF */
  file: File;
}

export interface UploadRepairDisclaimerParams {
  /** Repair ID */
  id: number;
}

export type PrintRepairLabelPayload = object;

export interface PrintRepairLabelParams {
  /** ID of the repair to print a label for */
  id: number;
}

export interface ListRepairAttachmentsParams {
  attachment_type?: "log_entry" | "device_photo" | "disclaimer" | "misc";
  log_id?: number;
  repairId: number;
}

export interface UploadRepairAttachmentsPayload {
  /** One or more files to upload */
  files: File[];
  /** Attachment type: log_entry, device_photo, disclaimer, misc (default: misc). device_photo takes exactly one image and replaces the previous device photo. */
  attachment_type?: string;
  /** Link to a repair log entry */
  log_id?: number;
  /** User ID of the uploader */
  uploaded_by_id?: number;
}

export interface UploadRepairAttachmentsParams {
  repairId: number;
}

export interface DeleteRepairAttachmentParams {
  repairId: number;
  attachmentId: number;
}

export interface GetRepairAttachmentParams {
  repairId: number;
  attachmentId: number;
}

export interface ListRepairLogsParams {
  /** The repair ID */
  repairId: number;
}

export interface CreateRepairLogParams {
  /** The repair ID */
  repairId: number;
}

export interface DeleteRepairLogParams {
  repairId: number;
  logId: number;
}

export interface GetRepairLogParams {
  /** The repair ID */
  repairId: number;
  /** The repair log ID */
  logId: number;
}

export interface UpdateRepairLogParams {
  /** Repair ID */
  repairId: number;
  /** Repair log ID */
  logId: number;
}

export interface ListVdeTestsParams {
  /** The repair ID */
  repairId: number;
}

export interface CreateVdeTestParams {
  /** The repair ID */
  repairId: number;
}

export interface GetVdeTestParams {
  /** The repair ID */
  repairId: number;
  /** The VDE test ID */
  testId: number;
}

export interface GetVdeTestPdfParams {
  repairId: number;
  testId: number;
}

export interface DeleteSettingParams {
  settingId: number;
}

export interface UpdateSettingParams {
  settingId: number;
}

export interface GetStatDataParams {
  type: "repairs" | "devices" | "time";
}

export interface DeactivateUserParams {
  /** User ID */
  userId: number;
}

export interface GetUserParams {
  /** User ID */
  userId: number;
}

export interface UpdateUserParams {
  /** User ID */
  userId: number;
}
