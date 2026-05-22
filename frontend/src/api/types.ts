/*
 * Re-export generated API types for convenient importing
 * Types are auto-generated from OpenAPI spec using swagger-typescript-api
 *
 * To regenerate: npm run generate-api
 */

export type {
  APIResponse,
  CustomerResponse,
  CustomerWithRepairCountResponse,
  PruefgeraetResponse,
  RepairCreate,
  RepairUpdate,
  RepairResponse,
  RepairCreateResponse,
  RepairLogCreate,
  RepairLogResponse,
  RepairLogListResponse,
  VdeTestCreate,
  VdeTestResponse,
  VdeTestListResponse,
  VdeTestCreateResponse,
  UserResponse,
} from "./generated/data-contracts";

// Convenience type aliases
export type { RepairResponse as Repair } from "./generated/data-contracts";
export type { RepairLogResponse as RepairLog } from "./generated/data-contracts";

// Re-export API client classes
export { Api } from "./generated/Api";
