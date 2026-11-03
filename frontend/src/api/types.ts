/*
 * API types, generated from frontend/openapi.json (pnpm generate-api).
 * Import types from here, and call the API through `api` from './client'.
 */
export type * from './generated/data-contracts'

// Short names used throughout the app
export type {
  RepairResponse as Repair,
  RepairLogResponse as RepairLog,
} from './generated/data-contracts'
