<template>
  <v-container class="lock-page d-flex align-center justify-center" fluid>
    <v-card class="lock-panel" variant="flat">
      <div class="d-flex align-center ga-3 mb-5">
        <v-avatar color="primary" size="48">
          <v-icon icon="mdi-lock-outline" />
        </v-avatar>
        <div>
          <h1 class="text-h5 font-weight-bold">Repair Café gesperrt</h1>
          <div class="text-body-2 text-medium-emphasis">PIN eingeben, um Helfer zu wechseln</div>
        </div>
      </div>

      <v-alert v-if="error" class="mb-4" type="error" variant="tonal" density="compact">
        {{ error }}
      </v-alert>

      <form class="mb-6" @submit.prevent="unlock">
        <v-text-field
          v-model="pinCode"
          autofocus
          autocomplete="one-time-code"
          inputmode="numeric"
          label="Sechsstellige PIN"
          maxlength="6"
          :disabled="submitting"
          :type="showPin ? 'text' : 'password'"
          variant="outlined"
          prepend-inner-icon="mdi-dialpad"
          :append-inner-icon="showPin ? 'mdi-eye-off' : 'mdi-eye'"
          @click:append-inner="showPin = !showPin"
          @update:model-value="sanitizePin"
        />
        <v-btn
          block
          color="primary"
          type="submit"
          :disabled="pinCode.length !== 6 || submitting"
          :loading="submitting"
        >
          Entsperren
        </v-btn>
      </form>

      <div class="d-flex align-center justify-space-between mb-3">
        <h2 class="text-subtitle-1 font-weight-bold">Reparaturübersicht</h2>
        <v-progress-circular v-if="summaryLoading" indeterminate size="18" width="2" />
      </div>
      <v-alert v-if="summaryError" type="warning" variant="tonal" density="compact">
        Übersicht derzeit nicht verfügbar
      </v-alert>
      <template v-else-if="summary">
        <div class="metric-grid">
          <div class="metric metric-total">
            <span>Gesamt</span><strong>{{ summary.total_repairs }}</strong>
          </div>
          <div class="metric">
            <span>Offen</span><strong>{{ summary.open_repairs }}</strong>
          </div>
          <div class="metric">
            <span>In Bearbeitung</span><strong>{{ summary.in_progress_repairs }}</strong>
          </div>
          <div class="metric">
            <span>Abgeschlossen</span><strong>{{ summary.repaired_repairs }}</strong>
          </div>
          <div class="metric">
            <span>Nicht repariert</span><strong>{{ summary.not_repaired_repairs }}</strong>
          </div>
          <div class="metric">
            <span>Erfolgsquote</span>
            <strong>{{ summary.success_rate == null ? '–' : `${summary.success_rate} %` }}</strong>
          </div>
        </div>
        <div v-if="recentWeeks.length" class="mt-5">
          <div class="text-caption text-medium-emphasis mb-2">Letzte Reparaturwochen</div>
          <div v-for="week in recentWeeks" :key="week.week" class="week-row">
            <span>{{ week.label }}</span>
            <span>{{ (week.offen ?? 0) + (week.in_bearbeitung ?? 0) + (week.abgeschlossen ?? 0) + (week.nicht_repariert ?? 0) }}</span>
          </div>
        </div>
      </template>

      <v-divider class="my-5" />
      <v-btn block variant="text" prepend-icon="mdi-logout" :loading="loggingOut" @click="logout">
        Vollständig abmelden
      </v-btn>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { AuthService } from '@/api/services/AuthService'
import type { PinDashboardSummaryResponse } from '@/api/types'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const authStore = useAuthStore()
const pinCode = ref('')
const showPin = ref(false)
const submitting = ref(false)
const loggingOut = ref(false)
const error = ref('')
const summary = ref<PinDashboardSummaryResponse | null>(null)
const summaryLoading = ref(false)
const summaryError = ref(false)
const recentWeeks = computed(() => summary.value?.timeline?.slice(-6).reverse() ?? [])

function sanitizePin(value: string | null) {
  pinCode.value = (value ?? '').replace(/[^0-9]/g, '').slice(0, 6)
  error.value = ''
}

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
  } finally {
    loggingOut.value = false
  }
}

onMounted(async () => {
  summaryLoading.value = true
  try {
    summary.value = await AuthService.pinDashboardSummary()
  } catch {
    summaryError.value = true
  } finally {
    summaryLoading.value = false
  }
})
</script>

<style scoped>
.lock-page {
  min-height: calc(100vh - 32px);
  padding: 24px;
  background-color: #edf2f0;
  background-image: radial-gradient(#c8d7d1 0.7px, transparent 0.7px);
  background-size: 18px 18px;
}

.lock-panel {
  width: min(100%, 560px);
  padding: 28px;
  border: 1px solid rgba(32, 76, 60, 0.16);
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 18px 48px rgba(26, 58, 46, 0.12);
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.metric {
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: space-between;
  gap: 8px;
  padding: 12px;
  border-left: 3px solid #3b8067;
  background: #f2f6f4;
}

.metric span {
  color: #52645c;
  font-size: 0.75rem;
  line-height: 1.25;
}

.metric strong {
  color: #183c2e;
  font-size: 1.45rem;
  line-height: 1;
}

.metric-total {
  border-color: #d68b32;
  background: #fbf5eb;
}

.week-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  border-bottom: 1px solid #e5ebe7;
  color: #45564e;
  font-size: 0.8125rem;
}

@media (max-width: 480px) {
  .lock-panel {
    padding: 20px;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>