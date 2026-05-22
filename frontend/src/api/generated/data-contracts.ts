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
  error?: string;
  /**
   * Response message
   * @default null
   */
  message?: string;
  /** Response status (done, error) */
  reply: string;
}

export interface CustomerResponse {
  /** @format date-time */
  created_at: string;
  /** @default null */
  email?: string;
  id: number;
  nachname: string;
  /** @default null */
  telefon?: string;
  vorname: string;
}

export interface CustomerWithRepairCountResponse {
  /** @format date-time */
  created_at: string;
  /** @default null */
  email?: string;
  id: number;
  nachname: string;
  /**
   * Number of repairs for this customer
   * @default 0
   */
  repair_count?: number;
  /** @default null */
  telefon?: string;
  vorname: string;
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
  serial_number?: string;
}

export interface RepairCreate {
  /**
   * Link to existing customer
   * @default null
   */
  customer_id?: number;
  /**
   * Date of repair intake
   * @format date
   */
  datum: string;
  /**
   * Defect description
   * @default null
   */
  defekt_besch?: string;
  /**
   * Email address
   * @default null
   */
  email?: string;
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
  /**
   * Repair category
   * @minLength 1
   * @maxLength 100
   */
  reparatur_art: string;
  /**
   * Other repair category
   * @default null
   */
  reparatur_sonstiges?: string;
  /**
   * Phone number
   * @default null
   */
  telefon?: string;
  /**
   * Signature image as base64
   * @default null
   */
  unterschrift?: string;
  /**
   * First name
   * @minLength 1
   * @maxLength 100
   */
  vorname: string;
}

export interface RepairCreateResponse {
  data?: RepairResponse;
  /**
   * Error message if reply is error
   * @default null
   */
  error?: string;
  /**
   * Created repair ID
   * @default null
   */
  id?: number;
  /**
   * Response message
   * @default null
   */
  message?: string;
  /** Response status (done, error) */
  reply: string;
}

export interface RepairLogCreate {
  /** Repair ID this log belongs to */
  repair_id: number;
  /**
   * Entry type: 'work' for work sessions, 'status_change' for status transitions
   * @default "work"
   */
  log_type?: string;
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
  /** Status before the transition */
  status_from?: string;
  /** Status after the transition */
  status_to?: string;
  /**
   * Assigned reparateur (user FK)
   * @default null
   */
  user_id?: number;
}

export interface RepairLogListResponse {
  data: RepairLogResponse[];
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
   * @default "work"
   */
  log_type: string;
  /** Repair ID this log belongs to */
  repair_id: number;
  /**
   * Repair description
   * @maxLength 400
   * @default ""
   */
  reparatur_besch: string;
  /**
   * Repair duration in minutes
   * @min 0
   * @default 0
   */
  reparatur_dauer: number;
  /** Status before the transition */
  status_from?: string | null;
  /** Status after the transition */
  status_to?: string | null;
  user?: UserResponse;
  /**
   * Assigned reparateur (user FK)
   * @default null
   */
  user_id?: number;
}

export interface RepairResponse {
  customer?: CustomerResponse;
  /**
   * Linked customer ID
   * @default null
   */
  customer_id?: number;
  /**
   * Date of repair intake
   * @format date
   */
  datum: string;
  /**
   * Defect description
   * @default null
   */
  defekt_besch?: string;
  /**
   * DIN test performed
   * @default null
   */
  din_pruef?: boolean;
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
  /**
   * Repair category
   * @minLength 1
   * @maxLength 100
   */
  reparatur_art: string;
  /**
   * Repair description
   * @default null
   */
  reparatur_besch?: string;
  /**
   * Repair duration in minutes
   * @default null
   */
  reparatur_dauer?: number;
  /**
   * Other repair category
   * @default null
   */
  reparatur_sonstiges?: string;
  /**
   * Repair status
   * @default "Offen"
   * @pattern ^(Offen|In Bearbeitung|Repariert|Nicht Repariert)$
   */
  status?: string;
  /**
   * Additional detail for repair status
   * @default null
   */
  status_detail?: string;
  /**
   * Signature image as base64
   * @default null
   */
  unterschrift?: string;
  /**
   * Liability disclaimer signed
   * @default null
   */
  unterschrift_haft?: boolean;
  user?: UserResponse;
  /**
   * Assigned reparateur (user FK)
   * @default null
   */
  user_id?: number | null;
}

export interface RepairUpdate {
  /**
   * Date of repair intake
   * @default null
   */
  datum?: string;
  /**
   * Defect description
   * @default null
   */
  defekt_besch?: string;
  /**
   * DIN test performed
   * @default null
   */
  din_pruef?: boolean;
  /**
   * Device type
   * @default null
   */
  geraet_art?: string;
  /**
   * Repair category
   * @default null
   */
  reparatur_art?: string;
  /**
   * Repair description
   * @default null
   */
  reparatur_besch?: string;
  /**
   * Repair duration in minutes
   * @default null
   */
  reparatur_dauer?: number;
  /**
   * Other repair category
   * @default null
   */
  reparatur_sonstiges?: string;
  /**
   * Repair status
   * @default null
   */
  status?: string;
  /**
   * Additional detail for repair status
   * @default null
   */
  status_detail?: string;
  /**
   * Signature image as base64
   * @default null
   */
  unterschrift?: string;
  /**
   * Liability disclaimer signed
   * @default null
   */
  unterschrift_haft?: boolean;
  /**
   * Assigned reparateur (user FK)
   * @default null
   */
  user_id?: number | null;
}

export interface UserResponse {
  /** @format date-time */
  created_at: string;
  email: string;
  id: number;
  is_active: boolean;
  is_admin: boolean;
  /** @default null */
  nachname?: string;
  username: string;
  /** @default null */
  vorname?: string;
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
  bemerkungen?: string;
  /**
   * When this test was performed (defaults to now)
   * @default null
   */
  created_at?: string;
  /**
   * Electrician supervising EuP test
   * @default null
   */
  electrician?: string;
  /** Overall result: True=passed, False=failed */
  gesamtergebnis: boolean;
  /**
   * Insulation test: True=passed, False=failed
   * @default null
   */
  isolationspruefung?: boolean | null;
  /**
   * Testing device name
   * @default null
   */
  pruefgeraet_name?: string;
  /**
   * Testing device serial number
   * @default null
   */
  pruefgeraet_serial?: string;
  /**
   * Tester name (legacy text, derived from prufer_user_id)
   * @default null
   */
  prufer?: string;
  /**
   * FK to users table — who performed the test
   * @default null
   */
  prufer_user_id?: number;
  /** Repair ID this test belongs to */
  repair_id: number;
  /**
   * Protection class
   * @default null
   */
  schutzklasse?: string;
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
  data?: VdeTestResponse;
  /**
   * Error message if reply is error
   * @default null
   */
  error?: string;
  /**
   * Created VDE test ID
   * @default null
   */
  id?: number;
  /**
   * Response message
   * @default null
   */
  message?: string;
  /** Response status (done, error) */
  reply: string;
}

export interface VdeTestListResponse {
  data: VdeTestResponse[];
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
  bemerkungen?: string;
  /**
   * When this test was performed
   * @format date-time
   */
  created_at: string;
  /**
   * Electrician supervising EuP test
   * @default null
   */
  electrician?: string;
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
   * @default null
   */
  pruefgeraet_name?: string;
  /**
   * Testing device serial number
   * @default null
   */
  pruefgeraet_serial?: string;
  /**
   * Tester name (legacy text, derived from prufer_user_id)
   * @default null
   */
  prufer?: string;
  /**
   * FK to users table — who performed the test
   * @default null
   */
  prufer_user_id?: number;
  /** Repair ID this test belongs to */
  repair_id: number;
  /**
   * Protection class
   * @default null
   */
  schutzklasse?: string;
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

export interface GetRepairByQrTokenParams {
  /** QR token of the repair */
  token: string;
}

export interface UpdateRepairParams {
  /** ID of the repair to update */
  id: number;
}

export interface GetRepairDisclaimerParams {
  /** Repair ID */
  id: number;
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

export interface DeleteSettingParams {
  settingId: number;
}

export interface UpdateSettingParams {
  settingId: number;
}

export interface EditRepairParams {
  id: number;
}

export interface EditRepairWithTokenParams {
  id: number;
  token: string;
}

export interface GetStatDataParams {
  type: "repairs" | "devices" | "time";
}

export interface SettingResponse {
  id: number;
  category: string;
  name: string;
  serial_number: string | null;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
