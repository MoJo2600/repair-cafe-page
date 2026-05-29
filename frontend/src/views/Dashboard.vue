<template>
  <v-container fluid>
    <!-- Next Repair + In Progress -->
    <v-row>
      <v-col cols="12" md="8">
        <v-card color="primary" variant="elevated" class="pa-2" height="100%">
          <v-card-title class="d-flex align-center">
            <v-icon size="40" class="mr-3">mdi-tools</v-icon>
            <div>
              <div class="text-h5">Nächste Reparatur</div>
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
                <div>
                  <strong>Kunde:</strong> {{ repairStore.nextRepair.customer?.vorname }}
                  {{ repairStore.nextRepair.customer?.nachname }}
                </div>
                <div><strong>Kategorie:</strong> {{ repairStore.nextRepair.reparatur_art }}</div>
              </div>
            </div>
            <div v-else class="text-h6">Keine offenen Reparaturen vorhanden</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card variant="elevated" class="pa-2" height="100%">
          <v-card-title class="d-flex align-center">
            <v-icon size="40" class="mr-3" color="warning">mdi-progress-wrench</v-icon>
            <div>
              <div class="text-h5">In Bearbeitung</div>
              <div class="text-caption">Aktive Reparaturen</div>
            </div>
          </v-card-title>
          <v-card-text>
            <div v-if="repairStore.loading" class="text-center py-4">
              <v-progress-circular indeterminate color="warning"></v-progress-circular>
            </div>
            <div
              v-else-if="repairStore.inProgressRepairs.length === 0"
              class="text-medium-emphasis"
            >
              Keine aktiven Reparaturen
            </div>
            <v-list v-else density="compact">
              <v-list-item
                v-for="r in repairStore.inProgressRepairs"
                :key="r.id"
                :subtitle="r.user_id ? userStore.getUserDisplayName(r.user_id) : 'Nicht zugewiesen'"
              >
                <template #title>
                  <span class="font-weight-bold">#{{ r.id }}</span>
                  &nbsp;{{ r.geraet_art }}
                </template>
              </v-list-item>
            </v-list>
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
            <div v-else class="text-h2 font-weight-bold">
              {{ repairStore.inProgressRepairsCount }}
            </div>
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
            <div v-else class="text-h2 font-weight-bold">
              {{ repairStore.notRepairedRepairsCount }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Repaired by user + Timeline Chart -->
    <v-row class="mt-4">
      <v-col cols="12" md="4">
        <v-card class="pa-2" variant="elevated" height="100%">
          <v-card-title class="d-flex align-center">
            <v-icon size="40" class="mr-3">mdi-account-wrench</v-icon>
            <div>
              <div class="text-h5">Reparaturen pro Reparateur</div>
              <div class="text-caption">Erfolgreich repariert</div>
            </div>
          </v-card-title>
          <v-card-text>
            <div v-if="repairStore.loading" class="text-center py-4">
              <v-progress-circular indeterminate color="primary" />
            </div>
            <div v-else-if="repairedByUser.length === 0" class="text-medium-emphasis py-2">
              Keine abgeschlossenen Reparaturen
            </div>
            <v-list v-else density="compact">
              <v-list-item v-for="entry in repairedByUser" :key="entry.name" :title="entry.name">
                <template #append>
                  <v-chip color="success" size="small">{{ entry.count }}</v-chip>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <v-card class="pa-2" variant="elevated">
          <v-card-title class="d-flex align-center">
            <v-icon size="40" class="mr-3">mdi-chart-line</v-icon>
            <div>
              <div class="text-h5">Reparaturen über Zeit</div>
              <div class="text-caption">Kumulativer Verlauf</div>
            </div>
          </v-card-title>
          <v-card-text>
            <div v-if="timelineLoading" class="text-center py-8">
              <v-progress-circular indeterminate color="primary"></v-progress-circular>
            </div>
            <div
              v-else-if="timelineData.length === 0"
              class="text-center py-8 text-medium-emphasis"
            >
              Keine Daten vorhanden
            </div>
            <Line v-else :data="chartData" :options="chartOptions" style="max-height: 320px" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRepairStore } from '@/stores/repairStore'
import { useUserStore } from '@/stores/userStore'
import { RepairsService } from '@/api/services/RepairsService'
import type { RepairsTimelinePoint } from '@/api/types'
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

const repairStore = useRepairStore()
const userStore = useUserStore()

// ── Timeline ──────────────────────────────────────────────────────────
const timelineLoading = ref(false)
const timelineData = ref<RepairsTimelinePoint[]>([])

const prevRepairedCount = ref(-1)
const repairedByUser = computed(() => {
  const counts: Record<string, number> = {}
  for (const r of repairStore.repairs) {
    if (r.status !== 'Repariert') continue
    const name = r.user
      ? `${r.user.vorname ?? ''} ${r.user.nachname ?? ''}`.trim() || r.user.username
      : 'Unbekannt'
    counts[name] = (counts[name] ?? 0) + 1
  }
  return Object.entries(counts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
})
const repairedCount = computed(
  () => repairStore.repairs.filter((r) => r.status === 'Repariert').length
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
    return timelineData.value.map((p) => (total += p[key] as number))
  }
  return {
    labels: timelineData.value.map((p) => p.label),
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
  await userStore.fetchUsers()
  await repairStore.fetchRepairs()
  // Set baseline after initial load so the watcher doesn't fire on mount
  prevRepairedCount.value = repairStore.repairs.filter((r) => r.status === 'Repariert').length
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
</script>
