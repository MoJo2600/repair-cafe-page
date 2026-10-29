/*
 * Re-export generated API types for convenient importing
 * Types are auto-generated from OpenAPI spec using swagger-typescript-api
 *
 * To regenerate: npm run generate-api
 */

export type {
  APIResponse,
  AppConfigResponse,
  AuthResponse,
  AuthConfigResponse,
  PinStatusResponse,
  PinGenerateRequest,
  PinGeneratedResponse,
  PinDashboardCategoryCount,
  PinDashboardRepairItem,
  PinDashboardSummaryResponse,
  PinSessionActionResponse,
  PinSessionStatusResponse,
  PinUnlockRequest,
  CustomerResponse,
  CustomerWithRepairCountResponse,
  FeaturesResponse,
  LoginRequest,
  PruefgeraetResponse,
  RepairCreate,
  RepairResponse,
  RepairCreateResponse,
  RepairsTimelinePoint,
  RepairsTimelineResponse,
  RepairLogCreate,
  RepairLogResponse,
  RepairLogListResponse,
  SettingResponse,
  VdeTestCreate,
  VdeTestResponse,
  VdeTestListResponse,
  VdeTestCreateResponse,
  UserResponse,
} from './generated/data-contracts'

// The generator drops nullability; user_id: null is how a repairer is unassigned.
import type { RepairUpdate as GeneratedRepairUpdate } from './generated/data-contracts'
export type RepairUpdate = Omit<GeneratedRepairUpdate, 'user_id'> & {
  user_id?: number | null
}

// Convenience type aliases
export type { RepairResponse as Repair } from './generated/data-contracts'
export type { RepairLogResponse as RepairLog } from './generated/data-contracts'

// Re-export API client classes
export { Api } from './generated/Api'
