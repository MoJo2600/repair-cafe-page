<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'
import { useTheme } from 'vuetify'
import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
import { Line } from 'vue-chartjs'
import { api } from '@/api/client'
import { useCelebration } from '@/composables/useCelebration'
import type { PinDashboardSummaryResponse, RepairsTimelinePoint } from '@/api/types'
import { getRepairStatusColor, getRepairStatusIcon } from '@/domain/repairStatus'
import CountBadge from '@/components/ui/CountBadge.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import TagChip from '@/components/ui/TagChip.vue'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

/**
 * Non-identifying repair figures; shown on the dashboard and on the lock screen
 * (also projected on the wall, so no customer data here). Refreshes every 5 s and
 * celebrates every newly repaired device with confetti and the celebration sound.
 */
const REFRESH_MS = 5_000

const theme = useTheme()

const summary = ref<PinDashboardSummaryResponse | null>(null)
const loading = shallowRef(false)
const failed = shallowRef(false)
let refreshTimer: number | null = null

const initialLoading = computed(() => loading.value && summary.value === null)
const inProgressItems = computed(() => summary.value?.in_progress_items ?? [])
const topCategories = computed(() => summary.value?.top_categories ?? [])
const timeline = computed(() => summary.value?.timeline ?? [])

async function load() {
  if (loading.value) return
  loading.value = true
  failed.value = false
  try {
    summary.value = await api.pinDashboardSummary()
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}

// Catch up right away when the tab comes back (background tabs throttle timers)
function onVisibilityChange() {
  if (document.visibilityState === 'visible') void load()
}

onMounted(() => {
  void load()
  refreshTimer = window.setInterval(() => void load(), REFRESH_MS)
  document.addEventListener('visibilitychange', onVisibilityChange)
})
onUnmounted(() => {
  if (refreshTimer !== null) window.clearInterval(refreshTimer)
  document.removeEventListener('visibilitychange', onVisibilityChange)
})

// Celebrate for everyone watching when a repair succeeds (not on the first load)
const { soundEnabled, soundUnlocked, celebrate, setSoundEnabled, testSound } = useCelebration()
let previousRepaired: number | null = null
watch(
  () => summary.value?.repaired_repairs,
  (count) => {
    if (count == null) return
    if (previousRepaired !== null && count > previousRepaired) celebrate()
    previousRepaired = count
  }
)

/** Status tiles use their status color as accent; everything else stays neutral. */
const tiles = computed(() => {
  const s = summary.value
  const statusTile = (status: string, title: string, value: number | undefined) => ({
    title,
    value,
    icon: getRepairStatusIcon(status),
    color: getRepairStatusColor(status),
  })
  return [
    { title: 'Gesamt', value: s?.total_repairs, icon: 'mdi-clipboard-list-outline', color: 'primary' },
    {
      title: 'Erfolgsquote',
      value: s?.success_rate == null ? undefined : `${s.success_rate} %`,
      icon: 'mdi-percent-outline',
      color: 'primary',
    },
    statusTile('Offen', 'Offen', s?.open_repairs),
    statusTile('In Bearbeitung', 'In Bearbeitung', s?.in_progress_repairs),
    statusTile('Repariert', 'Repariert', s?.repaired_repairs),
    statusTile('Nicht Repariert', 'Nicht repariert', s?.not_repaired_repairs),
  ]
})

const chartData = computed(() => {
  const colors = theme.current.value.colors
  const cumulative = (key: keyof RepairsTimelinePoint) => {
    let total = 0
    return timeline.value.map((point) => (total += (point[key] as number) ?? 0))
  }
  const line = (label: string, key: keyof RepairsTimelinePoint, status: string) => {
    // Same status colors as everywhere else in the app (theme tokens)
    const color = String(colors[getRepairStatusColor(status)])
    return { label, data: cumulative(key), borderColor: color, backgroundColor: color, tension: 0.3 }
  }
  return {
    labels: timeline.value.map((point) => point.label),
    datasets: [
      line('Offen', 'offen', 'Offen'),
      line('In Bearbeitung', 'in_bearbeitung', 'In Bearbeitung'),
      line('Repariert', 'abgeschlossen', 'Repariert'),
      line('Nicht repariert', 'nicht_repariert', 'Nicht Repariert'),
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom' as const } },
  scales: { y: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 } } },
}
</script>

<template>
  <div>
    <!-- Sound for the celebration; browsers need one interaction before playing audio -->
    <div class="d-flex justify-end mb-2">
      <v-btn
        v-if="soundEnabled && !soundUnlocked"
        color="primary"
        variant="tonal"
        prepend-icon="mdi-volume-high"
        @click="testSound"
      >
        Ton aktivieren
      </v-btn>
      <v-btn
        v-else
        variant="text"
        :prepend-icon="soundEnabled ? 'mdi-volume-high' : 'mdi-volume-off'"
        :aria-label="soundEnabled ? 'Jubelton ausschalten' : 'Jubelton einschalten'"
        @click="setSoundEnabled(!soundEnabled)"
      >
        {{ soundEnabled ? 'Ton an' : 'Ton aus' }}
      </v-btn>
    </div>

    <v-alert v-if="failed" type="warning" variant="tonal" class="mb-4">
      <div class="d-flex align-center justify-space-between ga-4">
        <span>Übersicht derzeit nicht verfügbar</span>
        <v-btn variant="text" :loading="loading" @click="load">Erneut laden</v-btn>
      </div>
    </v-alert>

    <v-row>
      <!-- Next repair: customers wait for their number to be called -->
      <v-col cols="12" md="7">
        <v-card color="primary" class="h-100">
          <v-card-item prepend-icon="mdi-tools" title="Nächste Reparatur">
            <v-card-subtitle>Bitte diese Nummer bereithalten</v-card-subtitle>
          </v-card-item>
          <v-card-text>
            <v-skeleton-loader v-if="initialLoading" type="heading" color="transparent" />
            <template v-else-if="summary?.next_repair_id != null">
              <div class="next-repair-number font-weight-black mb-2">#{{ summary.next_repair_id }}</div>
              <TagChip v-if="summary.next_repair_category" :label="summary.next_repair_category" />
            </template>
            <div v-else class="text-headline-small">Keine offenen Reparaturen</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="5">
        <v-card class="h-100" border>
          <v-card-text>
            <SectionTitle
              title="In Bearbeitung"
              :icon="getRepairStatusIcon('In Bearbeitung')"
              :count="summary?.in_progress_repairs ?? 0"
            />
            <v-skeleton-loader v-if="initialLoading" type="list-item@2" />
            <p v-else-if="!inProgressItems.length" class="text-body-large text-medium-emphasis">
              Gerade wird nichts repariert
            </p>
            <div v-else class="in-progress-grid">
              <v-sheet
                v-for="item in inProgressItems"
                :key="item.id"
                border
                rounded="lg"
                class="pa-3 d-flex align-center justify-space-between ga-2"
              >
                <span class="text-headline-small font-weight-bold">#{{ item.id }}</span>
                <TagChip v-if="item.category" :label="item.category" />
              </v-sheet>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col v-for="tile in tiles" :key="tile.title" cols="6" sm="4" lg="2">
        <v-card border class="h-100">
          <v-card-text>
            <div class="d-flex align-center ga-2 mb-2">
              <v-icon :icon="tile.icon" :color="tile.color" />
              <span class="text-title-medium text-truncate">{{ tile.title }}</span>
            </div>
            <v-skeleton-loader v-if="initialLoading" type="text" />
            <div v-else class="text-display-small font-weight-bold">{{ tile.value ?? '–' }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="8">
        <v-card border class="h-100">
          <v-card-text>
            <SectionTitle title="Reparaturen über Zeit" icon="mdi-chart-line" />
            <v-skeleton-loader v-if="initialLoading" type="image" />
            <v-empty-state
              v-else-if="timeline.length === 0"
              icon="mdi-chart-line"
              title="Noch keine Daten"
              size="48"
            />
            <div v-else class="chart">
              <Line :data="chartData" :options="chartOptions" />
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card border class="h-100">
          <v-card-text>
            <SectionTitle title="Häufigste Kategorien" icon="mdi-podium" />
            <v-skeleton-loader v-if="initialLoading" type="list-item@3" />
            <p v-else-if="topCategories.length === 0" class="text-medium-emphasis">Noch keine Daten</p>
            <v-list v-else class="pa-0" bg-color="transparent">
              <v-list-item v-for="(entry, index) in topCategories" :key="entry.name" class="px-0">
                <template #prepend>
                  <span class="rank text-title-medium text-medium-emphasis">{{ index + 1 }}.</span>
                </template>
                <v-list-item-title>{{ entry.name }}</v-list-item-title>
                <template #append>
                  <CountBadge :count="entry.count" />
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<style scoped>
.next-repair-number {
  font-size: clamp(3rem, 6vw, 5rem);
  line-height: 1;
  letter-spacing: -0.02em;
}

.in-progress-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 8px;
}

.chart {
  height: 300px;
}

.rank {
  min-width: 2rem;
}
</style>
