<template>
  <v-container fluid>
    <!-- Next Repair Card -->
    <v-row>
      <v-col cols="12">
        <v-card color="primary" variant="elevated" class="pa-2">
          <v-card-title class="d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <v-icon size="40" class="mr-3">mdi-tools</v-icon>
              <div>
                <div class="text-h5">Nächste Reparatur</div>
              </div>
            </div>
          </v-card-title>
          <v-card-text>
            <div v-if="repairStore.loading" class="text-center">
              <v-progress-circular indeterminate color="white"></v-progress-circular>
            </div>
            <div v-else-if="repairStore.nextRepair">
              <div class="text-h3 font-weight-bold mb-2">ID: {{ repairStore.nextRepair.id }}</div>
              <v-divider class="my-3 opacity-50"></v-divider>
              <div class="text-body-1">
                <div><strong>Gerät:</strong> {{ repairStore.nextRepair.geraet_art }}</div>
                <div><strong>Kunde:</strong> {{ repairStore.nextRepair.customer?.vorname }} {{ repairStore.nextRepair.customer?.nachname }}</div>
                <div><strong>Kategorie:</strong> {{ repairStore.nextRepair.reparatur_art }}</div>
              </div>
            </div>
            <div v-else class="text-h6">
              Keine offenen Reparaturen vorhanden
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Statistics Cards -->
    <v-row class="mt-4">
      <v-col cols="12" md="3">
        <v-card color="info" variant="elevated" class="pa-2">
          <v-card-title class="d-flex align-center">
            <v-icon size="40" class="mr-3">mdi-clipboard-text-clock</v-icon>
            <div>
              <div class="text-h5">Offen</div>
              <div class="text-caption">Wartet auf Bearbeitung</div>
            </div>
          </v-card-title>
          <v-card-text>
            <div v-if="repairStore.loading" class="text-center">
              <v-progress-circular indeterminate color="white"></v-progress-circular>
            </div>
            <div v-else class="text-h2 font-weight-bold">{{ repairStore.openRepairsCount }}</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card color="warning" variant="elevated" class="pa-2">
          <v-card-title class="d-flex align-center">
            <v-icon size="40" class="mr-3">mdi-wrench-clock</v-icon>
            <div>
              <div class="text-h5">In Bearbeitung</div>
              <div class="text-caption">Wird gerade repariert</div>
            </div>
          </v-card-title>
          <v-card-text>
            <div v-if="repairStore.loading" class="text-center">
              <v-progress-circular indeterminate color="white"></v-progress-circular>
            </div>
            <div v-else class="text-h2 font-weight-bold">{{ repairStore.inProgressRepairsCount }}</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card color="success" variant="elevated" class="pa-2">
          <v-card-title class="d-flex align-center">
            <v-icon size="40" class="mr-3">mdi-check-circle</v-icon>
            <div>
              <div class="text-h5">Abgeschlossen</div>
              <div class="text-caption">Erfolgreich beendet</div>
            </div>
          </v-card-title>
          <v-card-text>
            <div v-if="repairStore.loading" class="text-center">
              <v-progress-circular indeterminate color="white"></v-progress-circular>
            </div>
            <div v-else class="text-h2 font-weight-bold">{{ repairStore.closedRepairsCount }}</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card color="error" variant="elevated" class="pa-2">
          <v-card-title class="d-flex align-center">
            <v-icon size="40" class="mr-3">mdi-close-circle</v-icon>
            <div>
              <div class="text-h5">Nicht Repariert</div>
              <div class="text-caption">Reparatur nicht möglich</div>
            </div>
          </v-card-title>
          <v-card-text>
            <div v-if="repairStore.loading" class="text-center">
              <v-progress-circular indeterminate color="white"></v-progress-circular>
            </div>
            <div v-else class="text-h2 font-weight-bold">{{ repairStore.notRepairedRepairsCount }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Timeline Chart -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card class="pa-2">
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-chart-line</v-icon>
            Reparaturen über Zeit
          </v-card-title>
          <v-card-text>
            <div v-if="timelineLoading" class="text-center py-8">
              <v-progress-circular indeterminate color="primary"></v-progress-circular>
            </div>
            <div v-else-if="timelineData.length === 0" class="text-center py-8 text-medium-emphasis">
              Keine Daten vorhanden
            </div>
            <Line v-else :data="chartData" :options="chartOptions" style="max-height: 320px" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Start Repair Dialog -->
    <ReparateurRequiredDialog v-model="startRepairDialog" v-model:userId="startRepairUserId"
      title="Reparatur starten"
      message="Für den Wechsel von 'Offen' zu 'In Bearbeitung' muss ein Reparateur angegeben werden."
      confirm-text="Reparatur starten" :loading="startingRepair" @confirm="confirmStartRepair">
      <template #context>
        <div v-if="selectedRepair" class="mb-4">
          <v-alert type="info" variant="tonal" class="mb-4">
            <div><strong>Reparatur ID:</strong> {{ selectedRepair.id }}</div>
            <div><strong>Gerät:</strong> {{ selectedRepair.geraet_art }}</div>
            <div><strong>Kunde:</strong> {{ selectedRepair.customer?.vorname }} {{ selectedRepair.customer?.nachname }}</div>
          </v-alert>
        </div>
      </template>
    </ReparateurRequiredDialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, inject, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useRepairStore, normalizeRepairStatus } from '@/stores/repairStore'
import { RepairLogsService } from '@/api/services/RepairLogsService'
import { RepairsService } from '@/api/services/RepairsService'
import type { Repair, RepairsTimelinePoint } from '@/api/types'
import ReparateurRequiredDialog from '@/components/ReparateurRequiredDialog.vue'
import confetti from 'canvas-confetti'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

const router = useRouter()
const repairStore = useRepairStore()

const showToast = inject('showToast') as undefined | ((message: string, options?: { color?: string; timeout?: number }) => void)

const startRepairDialog = ref(false)
const selectedRepair = ref<Repair | null>(null)
const startingRepair = ref(false)
const startRepairUserId = ref<number | null>(null)

const timelineLoading = ref(false)
const timelineData = ref<RepairsTimelinePoint[]>([])

const prevRepairedCount = ref(-1)
const repairedCount = computed(() =>
  repairStore.repairs.filter(r => r.status === 'Repariert').length
)
watch(repairedCount, (newVal) => {
  if (prevRepairedCount.value < 0) return
  if (newVal > prevRepairedCount.value) {
    confetti({ particleCount: 150, spread: 80, origin: { y: 0.6 } })
  }
  prevRepairedCount.value = newVal
})

const chartData = computed(() => {
  const cumsum = (key: keyof RepairsTimelinePoint) => {
    let total = 0
    return timelineData.value.map(p => (total += p[key] as number))
  }
  return {
    labels: timelineData.value.map(p => p.label),
    datasets: [
      {
        label: 'Offen',
        data: cumsum('offen'),
        borderColor: '#2196F3',
        backgroundColor: 'rgba(33,150,243,0.1)',
        tension: 0.3,
        fill: false,
      },
    {
      label: 'In Bearbeitung',
      data: cumsum('in_bearbeitung'),
      borderColor: '#FF9800',
      backgroundColor: 'rgba(255,152,0,0.1)',
      tension: 0.3,
      fill: false,
    },
    {
      label: 'Abgeschlossen',
      data: cumsum('abgeschlossen'),
      borderColor: '#4CAF50',
      backgroundColor: 'rgba(76,175,80,0.1)',
      tension: 0.3,
      fill: false,
    },
    {
      label: 'Nicht Repariert',
      data: cumsum('nicht_repariert'),
      borderColor: '#F44336',
      backgroundColor: 'rgba(244,67,54,0.1)',
      tension: 0.3,
      fill: false,
    },
  ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' as const },
    title: { display: false },
  },
  scales: {
    y: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 } },
  },
}

onMounted(async () => {
  await repairStore.fetchRepairs()
  // Set baseline after initial load so the watcher doesn't fire on mount
  prevRepairedCount.value = repairStore.repairs.filter(r => r.status === 'Repariert').length
  repairStore.startAutoRefresh()
  timelineLoading.value = true
  try {
    const response = await RepairsService.getRepairsTimeline()
    timelineData.value = response.data ?? []
  } catch (e) {
    console.error('Failed to load timeline data', e)
  } finally {
    timelineLoading.value = false
  }
})

onUnmounted(() => {
  repairStore.stopAutoRefresh()
})

function openStartRepairDialog(repair: Repair) {
  selectedRepair.value = repair
  startRepairUserId.value = null
  startRepairDialog.value = true
}

function closeStartRepairDialog() {
  startRepairDialog.value = false
  selectedRepair.value = null
  startRepairUserId.value = null
}

async function confirmStartRepair(userId: number) {
  if (!selectedRepair.value) return

  const qrToken = selectedRepair.value.qr_token
  const repairId = selectedRepair.value.id
  const fromStatus = normalizeRepairStatus(selectedRepair.value.status)

  startingRepair.value = true
  try {
    await repairStore.transitionRepairStatus({
      repairId,
      fromStatus,
      toStatus: 'In Bearbeitung',
      user_id: userId,
    })

    await RepairLogsService.createRepairLog(repairId, {
      user_id: userId,
      reparatur_dauer: 0,
      reparatur_besch: '',
      log_type: 'status_change',
      status_from: fromStatus,
      status_to: 'In Bearbeitung',
    })

    showToast?.('Reparatur wurde gestartet', { color: 'success' })
    closeStartRepairDialog()
    router.push(`/edit/${qrToken}`)
  } catch (error) {
    console.error('Error starting repair:', error)
    showToast?.('Fehler beim Starten der Reparatur', { color: 'error' })
  } finally {
    startingRepair.value = false
  }
}
</script>
