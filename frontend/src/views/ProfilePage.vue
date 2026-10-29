<template>
  <div class="profile-page pa-4">
    <h1 class="text-h5 font-weight-bold mb-6">Mein Profil</h1>

    <dl class="profile-details mb-8">
      <div>
        <dt class="text-caption text-medium-emphasis">Name</dt>
        <dd>{{ fullName }}</dd>
      </div>
      <div>
        <dt class="text-caption text-medium-emphasis">Benutzername</dt>
        <dd>{{ authStore.currentUser?.username }}</dd>
      </div>
      <div>
        <dt class="text-caption text-medium-emphasis">E-Mail</dt>
        <dd>{{ authStore.currentUser?.email }}</dd>
      </div>
    </dl>

    <v-divider class="mb-6" />
    <section aria-labelledby="pin-heading" :aria-busy="loading || generating">
      <h2 id="pin-heading" class="text-h6 mb-4">PIN</h2>
      <v-progress-linear
        v-if="loading"
        indeterminate
        color="primary"
        aria-label="PIN-Status laden"
      />
      <v-alert v-if="error" type="error" variant="tonal" class="mb-4" role="alert">{{
        error
      }}</v-alert>

      <template v-if="status && !loading">
        <div class="d-flex align-center ga-2 mb-4">
          <v-icon :icon="status.has_pin ? 'mdi-shield-check-outline' : 'mdi-shield-off-outline'" />
          <span>{{ status.has_pin ? 'PIN eingerichtet' : 'Keine PIN eingerichtet' }}</span>
        </div>
        <p v-if="status.mode === 'oidc'" class="text-body-2 text-medium-emphasis">
          PIN-Verwaltung: Identitaetsanbieter. Die PIN ist nur im dortigen Profil abrufbar.
        </p>
        <v-btn
          v-else-if="status.can_generate"
          color="primary"
          :prepend-icon="status.has_pin ? 'mdi-refresh' : 'mdi-key-plus'"
          :loading="generating"
          :disabled="generating"
          @click="requestGeneration"
        >
          {{ status.has_pin ? 'PIN ersetzen' : 'PIN generieren' }}
        </v-btn>
      </template>

      <v-btn
        v-if="error && !loading"
        class="mt-4"
        variant="text"
        prepend-icon="mdi-refresh"
        @click="loadStatus"
      >
        Status erneut laden
      </v-btn>
    </section>

    <v-dialog v-model="confirmDialog" max-width="440" :persistent="generating">
      <v-card>
        <v-card-title class="text-wrap">PIN ersetzen?</v-card-title>
        <v-card-text
          >Die bisherige PIN wird ungueltig. Die neue PIN wird nur einmal angezeigt.</v-card-text
        >
        <v-card-actions class="flex-wrap">
          <v-spacer />
          <v-btn variant="text" :disabled="generating" @click="confirmDialog = false"
            >Abbrechen</v-btn
          >
          <v-btn
            color="primary"
            prepend-icon="mdi-refresh"
            :loading="generating"
            @click="generate(true)"
          >
            PIN ersetzen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog :model-value="Boolean(newPin)" max-width="440" @update:model-value="clearPin">
      <v-card>
        <v-card-title class="text-wrap">Neue PIN</v-card-title>
        <v-card-text>
          <v-text-field
            :model-value="newPin"
            :type="pinVisible ? 'text' : 'password'"
            label="Einmalige PIN"
            readonly
            autocomplete="off"
            hide-details
            class="pin-value mb-4"
          >
            <template #append-inner>
              <v-tooltip :text="pinVisible ? 'PIN verbergen' : 'PIN anzeigen'">
                <template #activator="{ props }">
                  <v-btn
                    v-bind="props"
                    :icon="pinVisible ? 'mdi-eye-off' : 'mdi-eye'"
                    :aria-label="pinVisible ? 'PIN verbergen' : 'PIN anzeigen'"
                    variant="text"
                    size="small"
                    @click="pinVisible = !pinVisible"
                  />
                </template>
              </v-tooltip>
            </template>
          </v-text-field>
          <p class="text-body-2">Nach dem Schliessen ist diese PIN nicht erneut abrufbar.</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" prepend-icon="mdi-check" @click="clearPin">Schliessen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { AuthService } from '@/api/services/AuthService'
import type { PinStatusResponse } from '@/api/types'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()
const fullName = computed(() => {
  const user = authStore.currentUser
  return [user?.vorname, user?.nachname].filter(Boolean).join(' ') || user?.username
})
const status = ref<PinStatusResponse | null>(null)
const loading = ref(true)
const generating = ref(false)
const confirmDialog = ref(false)
const error = ref('')
const newPin = ref('')
const pinVisible = ref(true)
let active = true

function clearPin() {
  newPin.value = ''
  pinVisible.value = true
}

async function loadStatus() {
  loading.value = true
  error.value = ''
  try {
    const result = await AuthService.pinStatus()
    if (active) status.value = result
  } catch {
    if (active) {
      status.value = null
      error.value = 'PIN-Status konnte nicht geladen werden.'
    }
  } finally {
    if (active) loading.value = false
  }
}

function requestGeneration() {
  if (status.value?.has_pin) confirmDialog.value = true
  else void generate(false)
}

async function generate(replace: boolean) {
  if (generating.value) return
  generating.value = true
  error.value = ''
  clearPin()
  try {
    const result = await AuthService.generatePin({ replace })
    if (!active || !authStore.isAuthenticated) return
    newPin.value = result.pin_code
    status.value = { mode: 'local', has_pin: true, can_generate: true }
  } catch {
    if (active) {
      await loadStatus()
      error.value = 'PIN konnte nicht erstellt werden. Bitte Status pruefen und erneut versuchen.'
    }
  } finally {
    if (active) {
      generating.value = false
      confirmDialog.value = false
    }
  }
}

watch(
  () => authStore.isAuthenticated,
  (authenticated) => {
    if (!authenticated) clearPin()
  }
)
onMounted(loadStatus)
onBeforeUnmount(() => {
  active = false
  clearPin()
})
</script>

<style scoped>
.profile-page {
  max-width: 720px;
  margin-inline: auto;
}
.profile-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr));
  gap: 20px;
}
.profile-details dd {
  overflow-wrap: anywhere;
}
.pin-value :deep(input) {
  font-family: monospace;
  font-size: 2rem;
  letter-spacing: 0;
}
</style>
