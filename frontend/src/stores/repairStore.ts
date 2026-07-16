import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { RepairsService } from "@/api/services/RepairsService";
import type { Repair, RepairLog, RepairUpdate } from "@/api/types";

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

const STATUS_TRANSITIONS: Record<RepairStatus, RepairStatus[]> = {
  Offen: ["In Bearbeitung"],
  "In Bearbeitung": ["Offen", "Repariert", "Nicht Repariert"],
  Repariert: ["Offen", "In Bearbeitung", "Nicht Repariert"],
  "Nicht Repariert": ["Offen", "In Bearbeitung"],
};

type RepairStatusTransitionInput = {
  repairId: number;
  fromStatus: RepairStatus;
  toStatus: RepairStatus;
  statusDetail?: string;
  user_id?: number;
};

type CompleteSuccessfulRepairInput = {
  repairId: number;
  fromStatus: RepairStatus;
  statusDetail?: string;
  user_id?: number;
  repairDescription: string;
  repairDuration: number;
};

type CompleteFailedRepairInput = {
  repairId: number;
  fromStatus: RepairStatus;
  statusDetail?: string;
  user_id?: number;
  repairDescription: string;
  repairDuration?: number;
};

export const useRepairStore = defineStore("repair", () => {
  // State
  const repairs = ref<Repair[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const autoRefreshInterval = ref<number | null>(null);
  const autoRefreshEnabled = ref(true);
  const refreshIntervalMs = ref(10000); // 10 seconds default

  // Computed properties
  const openRepairs = computed(() => {
    return repairs.value
      .filter((repair) => repair.status === "Offen")
      .sort((a, b) => a.id - b.id);
  });

  const inProgressRepairs = computed(() => {
    return repairs.value.filter((repair) => repair.status === "In Bearbeitung");
  });

  const closedRepairs = computed(() => {
    return repairs.value.filter(
      (repair) =>
        repair.status === "Repariert" || repair.status === "Nicht Repariert",
    );
  });

  const notRepairedRepairs = computed(() =>
    repairs.value.filter((repair) => repair.status === "Nicht Repariert"),
  );

  const repairedRepairs = computed(() =>
    repairs.value.filter((repair) => repair.status === "Repariert"),
  );

  const openRepairsCount = computed(() => openRepairs.value.length);
  const inProgressRepairsCount = computed(() => inProgressRepairs.value.length);
  const closedRepairsCount = computed(() => closedRepairs.value.length);
  const repairedRepairsCount = computed(() => repairedRepairs.value.length);
  const notRepairedRepairsCount = computed(
    () => notRepairedRepairs.value.length,
  );
  const totalRepairsCount = computed(() => repairs.value.length);

  const nextRepair = computed(() => {
    // Return the first open repair (already sorted by ID)
    return openRepairs.value.length > 0 ? openRepairs.value[0] : null;
  });

  // Actions
  async function fetchRepairs(showLoading = true) {
    if (showLoading) {
      loading.value = true;
    }
    error.value = null;

    try {
      const response = await RepairsService.listRepairs();
      if (response.data) {
        repairs.value = response.data;
      }
    } catch (err) {
      console.error("Error fetching repairs:", err);
      error.value = "Failed to fetch repairs";
    } finally {
      if (showLoading) {
        loading.value = false;
      }
    }
  }

  function startAutoRefresh() {
    if (autoRefreshInterval.value) {
      return; // Already running
    }

    autoRefreshEnabled.value = true;
    autoRefreshInterval.value = window.setInterval(async () => {
      if (autoRefreshEnabled.value) {
        // Don't show loading spinner during background refresh
        await fetchRepairs(false);
      }
    }, refreshIntervalMs.value);
  }

  function stopAutoRefresh() {
    autoRefreshEnabled.value = false;
    if (autoRefreshInterval.value) {
      clearInterval(autoRefreshInterval.value);
      autoRefreshInterval.value = null;
    }
  }

  function pauseAutoRefresh() {
    autoRefreshEnabled.value = false;
  }

  function resumeAutoRefresh() {
    autoRefreshEnabled.value = true;
  }

  function setRefreshInterval(intervalMs: number) {
    refreshIntervalMs.value = intervalMs;

    // Restart interval with new timing
    if (autoRefreshInterval.value) {
      stopAutoRefresh();
      startAutoRefresh();
    }
  }

  async function updateRepair(id: number, updates: RepairUpdate) {
    try {
      await RepairsService.updateRepair(id, updates);
      // Refresh the list after update
      await fetchRepairs(false);
    } catch (err) {
      console.error("Error updating repair:", err);
      throw err;
    }
  }

  function canTransitionStatus(
    fromStatus: RepairStatus,
    toStatus: RepairStatus,
  ): boolean {
    if (fromStatus === toStatus) {
      return true;
    }
    return STATUS_TRANSITIONS[fromStatus].includes(toStatus);
  }

  function requiresReparateurForTransition(
    fromStatus: RepairStatus,
    toStatus: RepairStatus,
  ): boolean {
    return fromStatus === "Offen" && toStatus === "In Bearbeitung";
  }

  async function transitionRepairStatus(input: RepairStatusTransitionInput) {
    const { repairId, fromStatus, toStatus, statusDetail, user_id } = input;

    if (!canTransitionStatus(fromStatus, toStatus)) {
      throw new Error(
        `Status transition not allowed: ${fromStatus} -> ${toStatus}`,
      );
    }

    if (requiresReparateurForTransition(fromStatus, toStatus) && !user_id) {
      throw new Error("Reparateur ist für diesen Statuswechsel erforderlich");
    }

    const updates: RepairUpdate = {
      status: toStatus,
      status_detail: statusDetail || undefined,
    };

    // Business rule: reopening a repair clears the assigned repairer.
    if (fromStatus === "In Bearbeitung" && toStatus === "Offen") {
      updates.user_id = null;
    } else if (user_id) {
      updates.user_id = user_id;
    }

    await RepairsService.updateRepair(repairId, updates);
    await fetchRepairs(false);
  }

  async function completeSuccessfulRepair(
    input: CompleteSuccessfulRepairInput,
  ) {
    const {
      repairId,
      fromStatus,
      statusDetail,
      user_id,
      repairDescription,
      repairDuration,
    } = input;

    const toStatus: RepairStatus = "Repariert";

    if (!canTransitionStatus(fromStatus, toStatus)) {
      throw new Error(
        `Status transition not allowed: ${fromStatus} -> ${toStatus}`,
      );
    }

    if (!repairDescription.trim()) {
      throw new Error("Reparaturbeschreibung ist erforderlich");
    }

    if (repairDuration < 0) {
      throw new Error("Reparaturdauer muss 0 oder groesser sein");
    }

    await RepairsService.updateRepair(repairId, {
      status: toStatus,
      status_detail: statusDetail || undefined,
      user_id: user_id || undefined,
      reparatur_besch: repairDescription.trim(),
      reparatur_dauer: repairDuration,
    });
    await fetchRepairs(false);
  }

  async function completeFailedRepair(input: CompleteFailedRepairInput) {
    const { repairId, fromStatus, statusDetail, user_id, repairDescription, repairDuration } =
      input;

    const toStatus: RepairStatus = "Nicht Repariert";

    if (!canTransitionStatus(fromStatus, toStatus)) {
      throw new Error(
        `Status transition not allowed: ${fromStatus} -> ${toStatus}`,
      );
    }

    if (!repairDescription.trim()) {
      throw new Error("Begründung ist erforderlich");
    }

    await RepairsService.updateRepair(repairId, {
      status: toStatus,
      status_detail: statusDetail || undefined,
      user_id: user_id || undefined,
      reparatur_besch: repairDescription.trim(),
      reparatur_dauer: repairDuration ?? undefined,
    });
    await fetchRepairs(false);
  }

  function getRepairById(id: number): Repair | undefined {
    return repairs.value.find((repair) => repair.id === id);
  }

  function getRepairByQrToken(qrToken: string): Repair | undefined {
    return repairs.value.find((repair) => repair.qr_token === qrToken);
  }

  return {
    // State
    repairs,
    loading,
    error,
    autoRefreshEnabled,
    refreshIntervalMs,

    // Computed
    openRepairs,
    inProgressRepairs,
    closedRepairs,
    notRepairedRepairs,
    repairedRepairs,
    openRepairsCount,
    inProgressRepairsCount,
    closedRepairsCount,
    repairedRepairsCount,
    notRepairedRepairsCount,
    totalRepairsCount,
    nextRepair,

    // Actions
    fetchRepairs,
    startAutoRefresh,
    stopAutoRefresh,
    pauseAutoRefresh,
    resumeAutoRefresh,
    setRefreshInterval,
    updateRepair,
    canTransitionStatus,
    requiresReparateurForTransition,
    requiresCompletionDetailsForTransition,
    transitionRepairStatus,
    completeSuccessfulRepair,
    completeFailedRepair,
    getRepairById,
    getRepairByQrToken,
  };
});
