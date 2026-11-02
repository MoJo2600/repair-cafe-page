import { api } from "@/api/client";
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { RepairListItem, RepairUpdate } from "@/api/types";
import {
  canTransitionStatus,
  requiresReparateurForTransition,
  type RepairStatus,
} from "@/domain/repairStatus";

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
  // List items carry each repair's latest log (GET /api/list)
  const repairs = ref<RepairListItem[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const autoRefreshInterval = ref<number | null>(null);
  const autoRefreshEnabled = ref(true);
  const refreshIntervalMs = ref(10000); // 10 seconds default
  let fetchRevision = 0;

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
    const revision = fetchRevision;
    if (showLoading) {
      loading.value = true;
    }
    error.value = null;

    try {
      const response = await api.listRepairs();
      if (response.data && revision === fetchRevision) {
        repairs.value = response.data;
      }
    } catch (err) {
      console.error("Error fetching repairs:", err);
      if (revision === fetchRevision) {
        error.value = "Failed to fetch repairs";
      }
    } finally {
      if (showLoading && revision === fetchRevision) {
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

  function clear() {
    fetchRevision += 1;
    stopAutoRefresh()
    repairs.value = []
    loading.value = false
    error.value = null
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
      await api.updateRepair({ id: id }, updates);
      // Refresh the list after update
      await fetchRepairs(false);
    } catch (err) {
      console.error("Error updating repair:", err);
      throw err;
    }
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

    await api.updateRepair({ id: repairId }, updates);
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

    await api.updateRepair({ id: repairId }, {
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

    await api.updateRepair({ id: repairId }, {
      status: toStatus,
      status_detail: statusDetail || undefined,
      user_id: user_id || undefined,
      reparatur_besch: repairDescription.trim(),
      reparatur_dauer: repairDuration ?? undefined,
    });
    await fetchRepairs(false);
  }

  function getRepairById(id: number): RepairListItem | undefined {
    return repairs.value.find((repair) => repair.id === id);
  }

  function getRepairByQrToken(qrToken: string): RepairListItem | undefined {
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
    clear,
    pauseAutoRefresh,
    resumeAutoRefresh,
    setRefreshInterval,
    updateRepair,
    transitionRepairStatus,
    completeSuccessfulRepair,
    completeFailedRepair,
    getRepairById,
    getRepairByQrToken,
  };
});
