<template>
  <div :class="['unified-dashboard', { 'unified-dashboard--locked': authStore.isLocked }]">
    <v-container fluid class="dashboard-container">
      <!-- Top Header (Full Lock Bar when locked, Compact Action Bar when unlocked) -->
      <v-card v-if="authStore.isLocked" variant="elevated" rounded="lg" class="mb-4 px-4 py-3">
        <div class="d-flex flex-wrap align-center justify-space-between ga-3">
          <div class="d-flex align-center ga-3">
            <v-avatar color="primary" variant="tonal" size="48" rounded="lg">
              <v-img v-if="!logoLoadError" src="/api/config/logo" alt="Repair Café Logo" contain
                @error="logoLoadError = true" />
              <v-icon v-else icon="mdi-tools" size="26" color="primary" />
            </v-avatar>
            <div>
              <div class="text-overline text-medium-emphasis lh-tight">
                Repair Café · Kundenübersicht
              </div>
              <h1 class="text-h5 font-weight-bold">Reparaturen im Überblick</h1>
            </div>
          </div>

          <div class="d-flex flex-wrap align-center ga-3">
            <!-- <v-chip color="success" variant="tonal" size="small" prepend-icon="mdi-sync">
              Live-Anzeige
            </v-chip>
            <v-chip color="warning" variant="tonal" size="small" prepend-icon="mdi-lock">
              Bildschirm gesperrt
            </v-chip> -->
            <v-btn color="primary" variant="elevated" prepend-icon="mdi-lock-open-outline" @click="openUnlock">
              Entsperren
            </v-btn>
            <v-btn icon="mdi-logout" variant="text" aria-label="Vollständig abmelden" title="Vollständig abmelden"
              :loading="loggingOut" @click="logout" />
          </div>
        </div>
      </v-card>

      <!-- <div
        v-else
        class="d-flex flex-wrap align-center justify-space-between ga-3 mb-4" 
      > -->
      <!-- <div class="d-flex align-center ga-3">
          <v-icon icon="mdi-view-dashboard" color="primary" size="32" />
          <div>
            <h1 class="text-h5 font-weight-bold">Kunden-Dashboard</h1>
            <div class="text-caption text-medium-emphasis">
              Wandprojektion · Automatisch aktualisierte Übersicht ohne sensible Kundendaten
            </div>
          </div>
        </div> -->
      <!-- <div class="d-flex align-center ga-2">
          <v-chip
            color="success"
            variant="tonal"
            size="small"
            prepend-icon="mdi-sync"
          >
            Automatische Aktualisierung
          </v-chip>
          <v-btn
            color="primary"
            variant="tonal"
            prepend-icon="mdi-projector-screen-outline"
            :loading="lockingScreen"
            @click="lockForProjection"
          >
            Bildschirm sperren (Wandprojektion)
          </v-btn>
        </div> -->
      <!-- </div> -->

      <!-- Error Alert -->
      <v-alert v-if="summaryError" type="warning" variant="tonal" rounded="lg" class="mb-4">
        <div class="d-flex align-center justify-space-between ga-4">
          <span>Übersicht derzeit nicht verfügbar</span>
          <v-btn size="small" variant="text" :loading="summaryLoading" @click="loadSummary">
            Erneut laden
          </v-btn>
        </div>
      </v-alert>

      <!-- Row 1: Next Repair + In Progress Hero Cards -->
      <v-row>
        <v-col cols="12" md="7">
          <v-card color="primary" variant="elevated" rounded="lg" class="pa-4 d-flex flex-column justify-space-between"
            height="100%">
            <v-card-title class="d-flex align-center justify-space-between flex-wrap ga-2 px-2">
              <div class="d-flex align-center">
                <v-icon size="42" class="mr-3">mdi-tools</v-icon>
                <div>
                  <div class="text-h5 font-weight-bold">Nächste Reparatur</div>
                  <div class="text-caption opacity-80">
                    Bitte diese Reparatur-ID bereithalten
                  </div>
                </div>
              </div>
              <v-chip color="white" variant="tonal" size="default" prepend-icon="mdi-clock-outline"
                class="font-weight-bold">
                {{ summary?.open_repairs ?? '–' }} offen
              </v-chip>
            </v-card-title>

            <v-card-text class="px-2 py-4">
              <div v-if="initialLoading" class="text-center py-6">
                <v-progress-circular indeterminate color="white" size="44" />
              </div>
              <div v-else-if="summary?.next_repair_id != null">
                <div class="d-flex flex-wrap align-center justify-space-between ga-4">
                  <div class="next-repair-id font-weight-black">
                    ID: #{{ summary.next_repair_id }}
                  </div>
                </div>
                <!-- <v-divider class="my-3 opacity-50" /> -->
                <div class="d-flex align-right justify-space-between text-body-1">
                  <!-- <span>Als Nächstes an der Reihe</span> -->
                  <v-chip v-if="summary.next_repair_category" color="white" variant="flat" size="large"
                    prepend-icon="mdi-tag-outline" class="font-weight-bold text-primary">
                    Kategorie: {{ summary.next_repair_category }}
                  </v-chip>
                </div>
              </div>
              <div v-else class="text-h5 font-weight-medium py-4">
                Keine offenen Reparaturen vorhanden
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="5">
          <v-card variant="elevated" rounded="lg" class="pa-4 d-flex flex-column" height="100%">
            <v-card-title class="d-flex align-center justify-space-between flex-wrap ga-2 px-2">
              <div class="d-flex align-center">
                <v-icon size="42" class="mr-3" color="warning">mdi-progress-wrench</v-icon>
                <div>
                  <div class="text-h5 font-weight-bold">In Bearbeitung</div>
                  <div class="text-caption text-medium-emphasis">
                    Aktive Reparaturen in der Werkstatt
                  </div>
                </div>
              </div>
              <v-chip color="warning" variant="tonal" class="font-weight-bold">
                {{ summary?.in_progress_repairs ?? '–' }} aktiv
              </v-chip>
            </v-card-title>

            <v-card-text class="px-2 pt-3 flex-grow-1 d-flex flex-column justify-center">
              <div v-if="initialLoading" class="text-center py-6">
                <v-progress-circular indeterminate color="warning" size="40" />
              </div>
              <div v-else-if="!inProgressItems.length" class="text-body-1 text-medium-emphasis py-4">
                Keine aktiven Reparaturen
              </div>
              <div v-else class="in-progress-grid">
                <v-sheet v-for="item in inProgressItems" :key="item.id" rounded="lg" border
                  class="px-3 py-2 d-flex align-center justify-space-between ga-2">
                  <span class="text-h5 font-weight-bold text-high-emphasis">
                    #{{ item.id }}
                  </span>
                  <v-chip v-if="item.category" size="small" color="warning" variant="tonal" class="font-weight-medium">
                    {{ item.category }}
                  </v-chip>
                  <span v-else class="text-caption text-medium-emphasis">
                    In Arbeit
                  </span>
                </v-sheet>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Row 2: 6 Colored Vuetify Statistics Cards -->
      <v-row class="mt-2">
        <v-col cols="12" sm="6" md="4" lg="2">
          <v-card color="primary" variant="elevated" rounded="lg" class="pa-2" height="100%">
            <v-card-title class="d-flex align-center">
              <v-icon size="36" class="mr-3">mdi-clipboard-list</v-icon>
              <div class="overflow-hidden">
                <div class="text-h6 font-weight-bold text-truncate">Gesamt</div>
                <div class="text-caption text-truncate">Erfasste Reparaturen</div>
              </div>
            </v-card-title>
            <v-card-text>
              <div v-if="initialLoading" class="text-center">
                <v-progress-circular indeterminate color="white" size="28" />
              </div>
              <div v-else class="text-h3 font-weight-bold">
                {{ summary?.total_repairs ?? '–' }}
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="4" lg="2">
          <v-card color="teal" variant="elevated" rounded="lg" class="pa-2" height="100%">
            <v-card-title class="d-flex align-center">
              <v-icon size="36" class="mr-3">mdi-percent</v-icon>
              <div class="overflow-hidden">
                <div class="text-h6 font-weight-bold text-truncate">Erfolgsquote</div>
                <div class="text-caption text-truncate">Repariert / Beendet</div>
              </div>
            </v-card-title>
            <v-card-text>
              <div v-if="initialLoading" class="text-center">
                <v-progress-circular indeterminate color="white" size="28" />
              </div>
              <div v-else-if="summary?.success_rate == null" class="text-h3 font-weight-bold">
                –
              </div>
              <div v-else class="text-h3 font-weight-bold">
                {{ summary.success_rate }} %
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="4" lg="2">
          <v-card color="info" variant="elevated" rounded="lg" class="pa-2" height="100%">
            <v-card-title class="d-flex align-center">
              <v-icon size="36" class="mr-3">mdi-clipboard-text-clock</v-icon>
              <div class="overflow-hidden">
                <div class="text-h6 font-weight-bold text-truncate">Offen</div>
                <div class="text-caption text-truncate">Wartet auf Start</div>
              </div>
            </v-card-title>
            <v-card-text>
              <div v-if="initialLoading" class="text-center">
                <v-progress-circular indeterminate color="white" size="28" />
              </div>
              <div v-else class="text-h3 font-weight-bold">
                {{ summary?.open_repairs ?? '–' }}
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="4" lg="2">
          <v-card color="warning" variant="elevated" rounded="lg" class="pa-2" height="100%">
            <v-card-title class="d-flex align-center">
              <v-icon size="36" class="mr-3">mdi-wrench-clock</v-icon>
              <div class="overflow-hidden">
                <div class="text-h6 font-weight-bold text-truncate">In Bearbeitung</div>
                <div class="text-caption text-truncate">Wird gerade repariert</div>
              </div>
            </v-card-title>
            <v-card-text>
              <div v-if="initialLoading" class="text-center">
                <v-progress-circular indeterminate color="white" size="28" />
              </div>
              <div v-else class="text-h3 font-weight-bold">
                {{ summary?.in_progress_repairs ?? '–' }}
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="4" lg="2">
          <v-card color="success" variant="elevated" rounded="lg" class="pa-2" height="100%">
            <v-card-title class="d-flex align-center">
              <v-icon size="36" class="mr-3">mdi-check-circle</v-icon>
              <div class="overflow-hidden">
                <div class="text-h6 font-weight-bold text-truncate">Abgeschlossen</div>
                <div class="text-caption text-truncate">Erfolgreich beendet</div>
              </div>
            </v-card-title>
            <v-card-text>
              <div v-if="initialLoading" class="text-center">
                <v-progress-circular indeterminate color="white" size="28" />
              </div>
              <div v-else class="text-h3 font-weight-bold">
                {{ summary?.repaired_repairs ?? '–' }}
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="4" lg="2">
          <v-card color="error" variant="elevated" rounded="lg" class="pa-2" height="100%">
            <v-card-title class="d-flex align-center">
              <v-icon size="36" class="mr-3">mdi-close-circle</v-icon>
              <div class="overflow-hidden">
                <div class="text-h6 font-weight-bold text-truncate">Nicht Repariert</div>
                <div class="text-caption text-truncate">Nicht möglich</div>
              </div>
            </v-card-title>
            <v-card-text>
              <div v-if="initialLoading" class="text-center">
                <v-progress-circular indeterminate color="white" size="28" />
              </div>
              <div v-else class="text-h3 font-weight-bold">
                {{ summary?.not_repaired_repairs ?? '–' }}
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Row 3: Timeline Chart + Top Categories Side-by-Side -->
      <v-row class="mt-2">
        <v-col cols="12" md="8">
          <v-card class="pa-3" variant="elevated" rounded="lg" height="100%">
            <v-card-title class="d-flex align-center">
              <v-icon size="38" class="mr-3" color="primary">mdi-chart-line</v-icon>
              <div>
                <div class="text-h5 font-weight-bold">Reparaturen über Zeit</div>
                <div class="text-caption text-medium-emphasis">Kumulativer Verlauf</div>
              </div>
            </v-card-title>
            <v-card-text>
              <div v-if="initialLoading" class="text-center py-8">
                <v-progress-circular indeterminate color="primary" />
              </div>
              <div v-else-if="timelineData.length === 0" class="text-center py-8 text-medium-emphasis">
                Keine Daten vorhanden
              </div>
              <Line v-else :data="chartData" :options="chartOptions" style="max-height: 300px" />
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="4">
          <v-card variant="elevated" rounded="lg" class="pa-3" height="100%">
            <v-card-title class="d-flex align-center">
              <v-icon size="38" class="mr-3" color="primary">mdi-podium</v-icon>
              <div>
                <div class="text-h5 font-weight-bold">Top Kategorien</div>
                <div class="text-caption text-medium-emphasis">Häufigste Reparaturarten</div>
              </div>
            </v-card-title>
            <v-card-text>
              <div v-if="initialLoading" class="text-center py-8">
                <v-progress-circular indeterminate color="primary" />
              </div>
              <div v-else-if="topCategories.length === 0" class="text-medium-emphasis py-4">
                Keine Daten
              </div>
              <v-list v-else density="comfortable" class="pa-0">
                <v-list-item v-for="(entry, i) in topCategories" :key="entry.name" :title="entry.name"
                  class="px-2 py-2 rounded-lg mb-1">
                  <template #prepend>
                    <v-avatar :color="i === 0 ? 'amber-darken-2' : i === 1 ? 'blue-grey' : 'brown'" variant="tonal"
                      size="34" class="mr-3 font-weight-bold">
                      {{ i + 1 }}
                    </v-avatar>
                  </template>
                  <template #append>
                    <v-chip size="default" color="primary" variant="tonal" class="font-weight-bold">
                      {{ entry.count }}
                    </v-chip>
                  </template>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>

    <!-- PIN Unlock Dialog -->
    <v-dialog v-model="unlockDialog" max-width="420" transition="dialog-transition">
      <v-card class="pa-6" rounded="lg" elevation="8">
        <div class="d-flex align-center ga-3 mb-5">
          <v-avatar color="primary" variant="tonal" size="42" rounded="lg">
            <v-icon icon="mdi-dialpad" size="22" />
          </v-avatar>
          <div>
            <div class="text-overline text-medium-emphasis lh-tight">Helferwechsel</div>
            <h2 class="text-h6 font-weight-bold">PIN eingeben</h2>
          </div>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" aria-label="PIN-Eingabe schließen" @click="closeUnlock" />
        </div>

        <v-alert v-if="error" class="mb-4" type="error" variant="tonal" density="compact">
          {{ error }}
        </v-alert>

        <form @submit.prevent="unlock">
          <v-text-field v-model="pinCode" autofocus autocomplete="one-time-code" inputmode="numeric"
            label="Sechsstellige Helfer-PIN" maxlength="6" :disabled="submitting" type="password" variant="outlined"
            prepend-inner-icon="mdi-lock-outline" @update:model-value="sanitizePin" />
          <v-btn block color="primary" size="large" type="submit" :disabled="pinCode.length !== 6 || submitting"
            :loading="submitting">
            Entsperren
          </v-btn>
        </form>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { AuthService } from '@/api/services/AuthService'
import type { PinDashboardSummaryResponse, RepairsTimelinePoint } from '@/api/types'
import { useAuthStore } from '@/stores/authStore'
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
const authStore = useAuthStore()

const pinCode = ref('')
const unlockDialog = ref(false)
const submitting = ref(false)
const loggingOut = ref(false)
const lockingScreen = ref(false)
const logoLoadError = ref(false)
const error = ref('')

const summary = ref<PinDashboardSummaryResponse | null>(null)
const summaryLoading = ref(false)
const summaryError = ref(false)
const prevRepairedCount = ref(-1)
let summaryRefreshInterval: number | null = null

const initialLoading = computed(() => summaryLoading.value && summary.value === null)
const inProgressItems = computed(() => summary.value?.in_progress_items ?? [])
const topCategories = computed(() => summary.value?.top_categories ?? [])
const timelineData = computed(() => summary.value?.timeline ?? [])

watch(
  () => summary.value?.repaired_repairs,
  (newVal) => {
    if (newVal == null) return
    if (prevRepairedCount.value >= 0 && newVal > prevRepairedCount.value) {
      confetti({ particleCount: 150, spread: 80, origin: { y: 0.6 } })
    }
    prevRepairedCount.value = newVal
  }
)

const chartData = computed(() => {
  const cumsum = (key: keyof RepairsTimelinePoint) => {
    let total = 0
    return timelineData.value.map((p) => (total += (p[key] as number) ?? 0))
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

function sanitizePin(value: string | null) {
  pinCode.value = (value ?? '').replace(/[^0-9]/g, '').slice(0, 6)
  error.value = ''
}

function openUnlock() {
  error.value = ''
  unlockDialog.value = true
}

function closeUnlock() {
  unlockDialog.value = false
}

watch(unlockDialog, (isOpen) => {
  if (!isOpen) {
    pinCode.value = ''
    error.value = ''
  }
})

async function unlock() {
  if (pinCode.value.length !== 6 || submitting.value) return
  submitting.value = true
  error.value = ''
  const result = await authStore.unlock(pinCode.value)
  pinCode.value = ''
  submitting.value = false
  if (!result.success) {
    error.value = result.error ?? 'PIN ungültig'
    return
  }
  unlockDialog.value = false
  await router.replace({ name: 'Home' })
}

async function lockForProjection() {
  if (lockingScreen.value || authStore.isLocked) return
  lockingScreen.value = true
  try {
    const locked = await authStore.lockSession()
    if (locked) {
      await router.replace({ name: 'PinLock' })
    }
  } finally {
    lockingScreen.value = false
  }
}

async function logout() {
  if (loggingOut.value) return
  loggingOut.value = true
  try {
    await authStore.logout()
    await router.replace({ name: 'Login' })
  } catch {
    error.value = 'Abmeldung fehlgeschlagen. Bitte erneut versuchen.'
    unlockDialog.value = true
  } finally {
    loggingOut.value = false
  }
}

async function loadSummary() {
  if (summaryLoading.value) return
  summaryLoading.value = true
  summaryError.value = false
  try {
    summary.value = await AuthService.pinDashboardSummary()
  } catch {
    summaryError.value = true
  } finally {
    summaryLoading.value = false
  }
}

onMounted(() => {
  void loadSummary()
  summaryRefreshInterval = window.setInterval(() => void loadSummary(), 15_000)
})

onUnmounted(() => {
  if (summaryRefreshInterval !== null) {
    window.clearInterval(summaryRefreshInterval)
  }
})
</script>

<style scoped>
.unified-dashboard--locked {
  min-height: 100dvh;
  background-color: rgb(var(--v-theme-background));
}

.dashboard-container {
  max-width: 1600px;
  margin: 0 auto;
}

.lh-tight {
  line-height: 1.2;
}

.next-repair-id {
  font-size: clamp(2.6rem, 4.5vw, 4.2rem);
  line-height: 1.05;
  letter-spacing: -0.02em;
}

.in-progress-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(175px, 1fr));
  gap: 10px;
}
</style>
