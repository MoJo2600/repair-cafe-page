/*
 * Repair status rules (pure, no state). The backend enforces the same rules in
 * PUT /api/repairs/{id}; keep both in sync.
 */
import type { RepairLog } from "@/api/types";

export const REPAIR_STATUSES = [
  "Offen",
  "In Bearbeitung",
  "Repariert",
  "Nicht Repariert",
] as const;

export const REPAIR_STATUS_DETAIL_OPTIONS: Record<RepairStatus, string[]> = {
  Offen: [],
  "In Bearbeitung": ["Ersatzteilbesorgung"],
  Repariert: [],
  "Nicht Repariert": ["Nicht moeglich", "Abbruch", "Wartezeit zu lang"],
};

export const OPEN_REPAIR_STATUSES: RepairStatus[] = ["Offen", "In Bearbeitung"];
export const CLOSED_REPAIR_STATUSES: RepairStatus[] = [
  "Repariert",
  "Nicht Repariert",
];

export type RepairStatus = (typeof REPAIR_STATUSES)[number];

export function normalizeRepairStatus(status?: string): RepairStatus {
  if ((REPAIR_STATUSES as readonly string[]).includes(status || "")) {
    return status as RepairStatus;
  }
  return "Offen";
}

export function getRepairStatusColor(status?: string): string {
  switch (normalizeRepairStatus(status)) {
    case "Offen":
      return "warning";
    case "In Bearbeitung":
      return "info";
    case "Repariert":
      return "success";
    case "Nicht Repariert":
      return "error";
    default:
      return "grey";
  }
}

export function getRepairStatusIcon(status?: string): string {
  switch (normalizeRepairStatus(status)) {
    case "Offen":
      return "mdi-clock-outline";
    case "In Bearbeitung":
      return "mdi-progress-wrench";
    case "Repariert":
      return "mdi-check-circle";
    case "Nicht Repariert":
      return "mdi-close-circle";
    default:
      return "mdi-help-circle";
  }
}

export function getRepairStatusDetailOptions(status?: string): string[] {
  return REPAIR_STATUS_DETAIL_OPTIONS[normalizeRepairStatus(status)] || [];
}

export function isOpenRepairStatus(status?: string): boolean {
  return OPEN_REPAIR_STATUSES.includes(normalizeRepairStatus(status));
}

export function isClosedRepairStatus(status?: string): boolean {
  return CLOSED_REPAIR_STATUSES.includes(normalizeRepairStatus(status));
}

export function requiresCompletionDetailsForTransition(
  fromStatus: RepairStatus,
  toStatus: RepairStatus,
): boolean {
  return fromStatus === "In Bearbeitung" && toStatus === "Repariert";
}

export function requiresFailureDetailsForTransition(
  fromStatus: RepairStatus,
  toStatus: RepairStatus,
): boolean {
  return fromStatus === "In Bearbeitung" && toStatus === "Nicht Repariert";
}

export function calculateRepairDurationFromLogs(logs: RepairLog[]): number {
  return logs.reduce((total, log) => total + (log.reparatur_dauer || 0), 0);
}

/** Allowed status changes; mirrors STATUS_TRANSITIONS in app/api/repairs.py. */
const STATUS_TRANSITIONS: Record<RepairStatus, RepairStatus[]> = {
  Offen: ["In Bearbeitung"],
  "In Bearbeitung": ["Offen", "Repariert", "Nicht Repariert"],
  Repariert: ["Offen", "In Bearbeitung", "Nicht Repariert"],
  "Nicht Repariert": ["Offen", "In Bearbeitung"],
};

export function canTransitionStatus(
  fromStatus: RepairStatus,
  toStatus: RepairStatus,
): boolean {
  if (fromStatus === toStatus) {
    return true;
  }
  return STATUS_TRANSITIONS[fromStatus].includes(toStatus);
}

export function requiresReparateurForTransition(
  fromStatus: RepairStatus,
  toStatus: RepairStatus,
): boolean {
  return fromStatus === "Offen" && toStatus === "In Bearbeitung";
}
