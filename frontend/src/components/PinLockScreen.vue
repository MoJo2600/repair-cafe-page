<template>
  <main class="lock-dashboard">
    <header class="dashboard-header">
      <div class="brand-lockup">
        <div class="brand-mark" aria-hidden="true">
          <v-icon icon="mdi-tools" size="25" />
        </div>
        <div>
          <p class="eyebrow">Repair Café · Kundenübersicht</p>
          <h1>Reparaturen im Überblick</h1>
        </div>
      </div>

      <div class="header-actions">
        <div class="lock-status">
          <v-icon icon="mdi-lock" size="16" />
          <span>Bildschirm gesperrt</span>
        </div>
        <v-btn class="unlock-trigger" color="primary" prepend-icon="mdi-lock-open-outline" @click="openUnlock">
          Entsperren
        </v-btn>
        <v-btn icon="mdi-logout" variant="text" aria-label="Vollständig abmelden" title="Vollständig abmelden"
          :loading="loggingOut" @click="logout" />
      </div>
    </header>

    <section class="dashboard-content" aria-label="Reparaturübersicht">
      <v-alert v-if="summaryError" class="load-error" type="warning" variant="tonal">
        <div class="d-flex align-center justify-space-between ga-4">
          <span>Übersicht derzeit nicht verfügbar</span>
          <v-btn size="small" variant="text" :loading="summaryLoading" @click="loadSummary">
            Erneut laden
          </v-btn>
        </div>
      </v-alert>

      <div class="hero-grid">
        <section class="next-repair-panel">
          <div class="next-repair-copy">
            <p class="eyebrow">Warteschlange</p>
            <h2>Nächste Reparatur</h2>
            <div v-if="summaryLoading && !summary" class="hero-loading">
              <v-progress-circular indeterminate color="white" size="30" width="3" />
            </div>
            <p v-else-if="summary?.next_repair_id != null" class="repair-number">
              <span class="repair-prefix">#</span>{{ summary.next_repair_id }}
            </p>
            <p v-else class="no-repair">Keine offene Reparatur</p>
          </div>
          <div class="repair-symbol" aria-hidden="true">
            <v-icon icon="mdi-wrench-clock" size="42" />
          </div>
          <div class="next-repair-footer">
            <span>Bitte diese Reparatur-ID bereithalten</span>
            <span class="open-count">
              <span class="status-dot" />
              {{ summary?.open_repairs ?? '–' }} offen
            </span>
          </div>
        </section>

        <section class="queue-panel">
          <div class="panel-heading">
            <span class="panel-icon"><v-icon icon="mdi-progress-wrench" /></span>
            <div>
              <p class="eyebrow">Werkstatt</p>
              <h2>In Bearbeitung</h2>
            </div>
          </div>
          <div v-if="summaryLoading && !summary" class="queue-loading">
            <v-progress-circular indeterminate color="primary" size="32" />
          </div>
          <div v-else class="queue-value">
            {{ summary?.in_progress_repairs ?? '–' }}
          </div>
          <p class="queue-caption">Reparaturen werden gerade bearbeitet</p>
          <div class="queue-total">
            <span>Insgesamt erfasst</span>
            <strong>{{ summary?.total_repairs ?? '–' }}</strong>
          </div>
        </section>
      </div>

      <section class="metric-grid" aria-label="Reparaturkennzahlen">
        <article v-for="metric in metrics" :key="metric.label" class="metric-panel">
          <span class="metric-label">{{ metric.label }}</span>
          <strong :class="['metric-value', `tone-${metric.tone}`]">{{ metric.value }}</strong>
        </article>
        <article v-if="summaryLoading && !summary" class="metric-panel metric-loading">
          <v-progress-circular indeterminate color="primary" size="24" />
        </article>
      </section>

      <section class="timeline-panel">
        <div class="timeline-heading">
          <div>
            <p class="eyebrow">Verlauf</p>
            <h2>Reparaturen über Zeit</h2>
          </div>
          <v-icon icon="mdi-chart-timeline-variant" size="25" color="primary" />
        </div>

        <p v-if="summaryLoading && !summary" class="timeline-empty">Lade Übersicht …</p>
        <p v-else-if="recentWeeks.length === 0" class="timeline-empty">
          Noch keine Reparaturen im Jahresverlauf
        </p>
        <div v-else class="timeline-list">
          <div v-for="week in recentWeeks" :key="week.week" class="timeline-row">
            <span class="week-label">{{ week.label }}</span>
            <div class="week-bar" role="img" :aria-label="`${weekTotal(week)} Reparaturen`">
              <span class="bar-open" :style="{ flexGrow: week.offen ?? 0 }" />
              <span class="bar-progress" :style="{ flexGrow: week.in_bearbeitung ?? 0 }" />
              <span class="bar-complete" :style="{ flexGrow: week.abgeschlossen ?? 0 }" />
              <span class="bar-failed" :style="{ flexGrow: week.nicht_repariert ?? 0 }" />
            </div>
            <strong class="week-total">{{ weekTotal(week) }}</strong>
          </div>
        </div>

        <div class="timeline-legend" aria-label="Statuslegende">
          <span><i class="legend-open" />Offen</span>
          <span><i class="legend-progress" />In Bearbeitung</span>
          <span><i class="legend-complete" />Abgeschlossen</span>
          <span><i class="legend-failed" />Nicht repariert</span>
        </div>
      </section>

      <footer class="dashboard-footer">
        <span>Aktuelle Werkstattübersicht</span>
        <span>Repair Café</span>
      </footer>
    </section>

    <v-dialog v-model="unlockDialog" max-width="420" transition="dialog-transition">
      <v-card class="glass-panel" elevation="0">
        <div class="unlock-heading">
          <div class="unlock-icon" aria-hidden="true">
            <v-icon icon="mdi-dialpad" size="23" />
          </div>
          <div>
            <p class="eyebrow">Helferwechsel</p>
            <h2>PIN eingeben</h2>
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
          <v-btn block color="primary" type="submit" :disabled="pinCode.length !== 6 || submitting"
            :loading="submitting">
            Entsperren
          </v-btn>
        </form>
      </v-card>
    </v-dialog>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { AuthService } from '@/api/services/AuthService'
import type { PinDashboardSummaryResponse, RepairsTimelinePoint } from '@/api/types'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const authStore = useAuthStore()
const pinCode = ref('')
const unlockDialog = ref(false)
const submitting = ref(false)
const loggingOut = ref(false)
const error = ref('')
const summary = ref<PinDashboardSummaryResponse | null>(null)
const summaryLoading = ref(false)
const summaryError = ref(false)
let summaryRefreshInterval: number | null = null

const recentWeeks = computed(() => summary.value?.timeline?.slice(-6).reverse() ?? [])
const metrics = computed(() => {
  if (!summary.value) return []
  return [
    { label: 'Gesamt', value: summary.value.total_repairs, tone: 'neutral' },
    { label: 'Offen', value: summary.value.open_repairs, tone: 'open' },
    { label: 'In Bearbeitung', value: summary.value.in_progress_repairs, tone: 'progress' },
    { label: 'Abgeschlossen', value: summary.value.repaired_repairs, tone: 'complete' },
    { label: 'Nicht repariert', value: summary.value.not_repaired_repairs, tone: 'failed' },
    {
      label: 'Erfolgsquote',
      value: summary.value.success_rate == null ? '–' : `${summary.value.success_rate} %`,
      tone: 'success',
    },
  ]
})

function weekTotal(week: RepairsTimelinePoint) {
  return (week.offen ?? 0) + (week.in_bearbeitung ?? 0) +
    (week.abgeschlossen ?? 0) + (week.nicht_repariert ?? 0)
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
  await router.replace({ name: 'Home' })
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
  summaryRefreshInterval = window.setInterval(() => void loadSummary(), 30_000)
})

onUnmounted(() => {
  if (summaryRefreshInterval !== null) {
    window.clearInterval(summaryRefreshInterval)
  }
})
</script>

<style scoped>
.lock-dashboard {
  --forest: #205640;
  --ink: #1d382d;
  --muted: #687b70;
  min-height: 100dvh;
  padding: 26px clamp(16px, 4vw, 56px) 20px;
  color: var(--ink);
  background-color: #edf3ef;
  background-image:
    linear-gradient(rgba(38, 84, 64, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(38, 84, 64, 0.035) 1px, transparent 1px);
  background-size: 32px 32px;
}

.dashboard-header,
.dashboard-content {
  width: min(100%, 1380px);
  margin: 0 auto;
}

.dashboard-header,
.brand-lockup,
.header-actions,
.panel-heading,
.timeline-heading,
.unlock-heading {
  display: flex;
  align-items: center;
}

.dashboard-header {
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 22px;
  border-bottom: 1px solid rgba(35, 75, 58, 0.14);
}

.brand-lockup {
  min-width: 0;
  gap: 14px;
}

.brand-mark,
.panel-icon,
.unlock-icon {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
}

.brand-mark {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  color: white;
  background: var(--forest);
}

.eyebrow {
  margin: 0 0 5px;
  color: #678173;
  font-size: 0.72rem;
  font-weight: 700;
  line-height: 1.2;
  text-transform: uppercase;
}

.dashboard-header h1 {
  margin: 0;
  color: #19382b;
  font-size: 1.55rem;
  font-weight: 700;
  line-height: 1.2;
}

.header-actions {
  flex: 0 0 auto;
  gap: 12px;
}

.lock-status {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: #465e51;
  font-size: 0.82rem;
  font-weight: 600;
}

.unlock-trigger {
  border-radius: 6px;
  font-weight: 700;
}

.dashboard-content {
  display: grid;
  gap: 16px;
  padding-top: 22px;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(250px, 0.85fr);
  gap: 14px;
}

.next-repair-panel,
.queue-panel,
.metric-panel,
.timeline-panel {
  border: 1px solid rgba(35, 75, 58, 0.1);
  border-radius: 8px;
}

.next-repair-panel {
  position: relative;
  display: flex;
  min-height: 208px;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  padding: 22px 26px 16px;
  color: white;
  background: var(--forest);
}

.next-repair-panel::after {
  position: absolute;
  top: -72px;
  right: 12%;
  width: 270px;
  height: 270px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  content: '';
  pointer-events: none;
}

.next-repair-copy,
.next-repair-footer {
  position: relative;
  z-index: 1;
}

.next-repair-copy .eyebrow {
  color: #c4d9cc;
}

.next-repair-panel h2,
.queue-panel h2,
.timeline-heading h2,
.unlock-heading h2 {
  margin: 0;
  font-size: 1.08rem;
  font-weight: 700;
  line-height: 1.25;
}

.repair-number {
  margin: 8px 0 0;
  color: white;
  font-size: 3.4rem;
  font-weight: 750;
  line-height: 1;
}

.repair-prefix {
  margin-right: 3px;
  color: #e8ad55;
  font-size: 2rem;
  vertical-align: 0.3em;
}

.no-repair {
  margin: 20px 0 8px;
  color: #e5eee8;
  font-size: 1.2rem;
  font-weight: 600;
}

.hero-loading {
  display: flex;
  height: 76px;
  align-items: center;
}

.repair-symbol {
  position: absolute;
  right: 28px;
  bottom: 52px;
  display: grid;
  width: 72px;
  height: 72px;
  place-items: center;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 8px;
  color: #f0bf70;
  background: rgba(255, 255, 255, 0.08);
}

.next-repair-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  color: #d3e2d9;
  font-size: 0.78rem;
}

.open-count {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: white;
  font-weight: 700;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #efb35c;
}

.queue-panel {
  display: flex;
  min-height: 208px;
  flex-direction: column;
  padding: 20px 22px 16px;
  background: white;
}

.panel-heading {
  gap: 12px;
}

.panel-heading .eyebrow,
.timeline-heading .eyebrow,
.unlock-heading .eyebrow {
  margin-bottom: 4px;
}

.panel-icon {
  width: 40px;
  height: 40px;
  border-radius: 7px;
  color: #a45b25;
  background: #fbf0e2;
}

.queue-value {
  margin: 12px 0 0 52px;
  color: var(--ink);
  font-size: 2.8rem;
  font-weight: 750;
  line-height: 1;
}

.queue-loading {
  display: flex;
  height: 50px;
  align-items: center;
  margin-left: 52px;
}

.queue-caption {
  margin: 5px 0 12px 52px;
  color: #718078;
  font-size: 0.78rem;
}

.queue-total {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid #e8eeea;
  color: #68776f;
  font-size: 0.8rem;
}

.queue-total strong {
  color: #263f33;
  font-size: 1.05rem;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
}

.metric-panel {
  display: flex;
  min-height: 100px;
  flex-direction: column;
  justify-content: space-between;
  gap: 12px;
  padding: 15px 16px;
  background: rgba(255, 255, 255, 0.9);
}

.metric-label {
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 600;
  line-height: 1.25;
}

.metric-value {
  color: #213d30;
  font-size: 1.8rem;
  font-weight: 750;
  line-height: 1;
}

.tone-open {
  color: #b16a1f;
}

.tone-progress {
  color: #347b79;
}

.tone-complete,
.tone-success {
  color: #34704e;
}

.tone-failed {
  color: #a74e43;
}

.metric-loading {
  align-items: center;
  justify-content: center;
}

.timeline-panel {
  padding: 18px 22px 16px;
  background: rgba(255, 255, 255, 0.92);
}

.timeline-heading {
  justify-content: space-between;
  margin-bottom: 16px;
}

.timeline-empty {
  margin: 24px 0;
  color: var(--muted);
  font-size: 0.88rem;
}

.timeline-list {
  display: grid;
  gap: 11px;
}

.timeline-row {
  display: grid;
  grid-template-columns: minmax(90px, 140px) minmax(0, 1fr) 32px;
  align-items: center;
  gap: 14px;
}

.week-label,
.week-total {
  color: #566a5e;
  font-size: 0.78rem;
}

.week-total {
  text-align: right;
}

.week-bar {
  display: flex;
  height: 10px;
  overflow: hidden;
  border-radius: 5px;
  background: #eef2ef;
}

.week-bar span {
  min-width: 0;
}

.bar-open,
.legend-open {
  background: #d69a43;
}

.bar-progress,
.legend-progress {
  background: #438d8a;
}

.bar-complete,
.legend-complete {
  background: #4a8a5e;
}

.bar-failed,
.legend-failed {
  background: #bd6557;
}

.timeline-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin-top: 18px;
  color: #6a7b71;
  font-size: 0.72rem;
}

.timeline-legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.timeline-legend i {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.dashboard-footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 2px;
  color: #7d8c83;
  font-size: 0.72rem;
}

.glass-panel {
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.65);
  border-radius: 8px;
  background: rgba(248, 251, 249, 0.78) !important;
  box-shadow: 0 24px 70px rgba(13, 37, 26, 0.24);
  backdrop-filter: blur(24px) saturate(150%);
  -webkit-backdrop-filter: blur(24px) saturate(150%);
}

.unlock-heading {
  gap: 12px;
  margin-bottom: 22px;
}

.unlock-icon {
  width: 42px;
  height: 42px;
  border-radius: 7px;
  color: var(--forest);
  background: rgba(36, 92, 70, 0.1);
}

:deep(.v-overlay__scrim) {
  background: rgba(15, 35, 27, 0.34) !important;
  backdrop-filter: blur(5px);
}

@media (max-width: 1100px) {
  .metric-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .lock-dashboard {
    padding: 18px 16px;
  }

  .dashboard-header {
    align-items: flex-start;
    flex-direction: column;
    gap: 16px;
    padding-bottom: 18px;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .hero-grid {
    grid-template-columns: 1fr;
  }

  .next-repair-panel,
  .queue-panel {
    min-height: 190px;
  }

  .timeline-panel {
    padding: 17px 14px;
  }
}

@media (max-width: 480px) {
  .dashboard-header h1 {
    font-size: 1.3rem;
  }

  .brand-mark {
    width: 42px;
    height: 42px;
  }

  .lock-status {
    font-size: 0.72rem;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .metric-panel {
    min-height: 88px;
    padding: 12px;
  }

  .metric-value {
    font-size: 1.55rem;
  }

  .timeline-row {
    grid-template-columns: 84px minmax(0, 1fr) 24px;
    gap: 8px;
  }

  .week-label,
  .week-total {
    font-size: 0.68rem;
  }

  .glass-panel {
    padding: 20px;
  }
}
</style>