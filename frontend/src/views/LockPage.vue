<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import DashboardSummary from '@/components/dashboard/DashboardSummary.vue'
import PinUnlockDialog from '@/components/PinUnlockDialog.vue'
import { redirectTarget } from '@/utils/redirect'
import { useCelebration } from '@/composables/useCelebration'

/** Shown while the shared PC is locked: public repair figures plus the way back in. */
const router = useRouter()
const route = useRoute()
const ssoUrl = computed(
  () => `/api/auth/oidc/login?next=${encodeURIComponent(redirectTarget(route.query))}`
)
const authStore = useAuthStore()
const { soundEnabled, setSoundEnabled } = useCelebration()

const unlockOpen = shallowRef(false)
const logoFailed = shallowRef(false)
const loggingOut = shallowRef(false)
const logoutError = shallowRef('')

async function logout() {
  if (loggingOut.value) return
  loggingOut.value = true
  logoutError.value = ''
  try {
    await authStore.logout()
    await router.replace({ name: 'Login' })
  } catch {
    logoutError.value = 'Abmeldung fehlgeschlagen. Bitte erneut versuchen.'
  } finally {
    loggingOut.value = false
  }
}

function toggleSound(enabled: boolean | null) {
  void setSoundEnabled(!!enabled)
}
</script>

<template>
  <div class="lock-page">
    <v-container fluid class="lock-content">
      <v-card border class="mb-4">
        <v-card-item>
          <template #prepend>
            <v-avatar size="48" rounded="lg" color="primary" variant="tonal">
              <v-img
                v-if="!logoFailed"
                src="/api/config/logo"
                alt="Repair Café"
                @error="logoFailed = true"
              />
              <v-icon v-else icon="mdi-tools" />
            </v-avatar>
          </template>
          <v-card-title class="text-headline-small">Reparaturen im Überblick</v-card-title>
          <v-card-subtitle>Repair Café</v-card-subtitle>
          <template #append>
            <div class="d-flex flex-wrap align-center ga-2">
              <v-btn
                v-if="authStore.pinUnlockAvailable"
                color="primary"
                icon="mdi-lock-open-outline"
                variant="tonal"
                aria-label="Entsperren"
                title="Entsperren"
                @click="unlockOpen = true"
              />
              <template v-else>
                <span class="text-body-medium text-medium-emphasis">PIN nur im Werkstattnetz</span>
                <v-btn
                  color="primary"
                  variant="flat"
                  size="large"
                  prepend-icon="mdi-login"
                  :href="ssoUrl"
                >
                  Mit SSO anmelden
                </v-btn>
              </template>
              <v-menu location="bottom end" :close-on-content-click="false">
                <template #activator="{ props: menuProps }">
                  <v-btn
                    v-bind="menuProps"
                    icon="mdi-dots-vertical"
                    variant="text"
                    aria-label="Weitere Aktionen"
                  />
                </template>
                <v-list min-width="260">
                  <v-list-item
                    :prepend-icon="soundEnabled ? 'mdi-volume-high' : 'mdi-volume-off'"
                    title="Ton"
                    :subtitle="soundEnabled ? 'An' : 'Aus'"
                  >
                    <template #append>
                      <v-switch
                        :model-value="soundEnabled"
                        color="primary"
                        density="compact"
                        hide-details
                        :aria-label="soundEnabled ? 'Ton aus' : 'Ton an'"
                        @update:model-value="toggleSound"
                      />
                    </template>
                  </v-list-item>
                  <v-divider />
                  <v-list-item
                    prepend-icon="mdi-logout"
                    title="Abmelden"
                    base-color="error"
                    :disabled="loggingOut"
                    @click="logout"
                  />
                </v-list>
              </v-menu>
            </div>
          </template>
        </v-card-item>
        <v-alert
          v-if="logoutError"
          type="error"
          variant="tonal"
          density="compact"
          class="ma-4 mt-0"
        >
          {{ logoutError }}
        </v-alert>
      </v-card>

      <DashboardSummary />
    </v-container>

    <PinUnlockDialog v-model="unlockOpen" />
  </div>
</template>

<style scoped>
.lock-page {
  min-height: 100dvh;
}

.lock-content {
  max-width: 1600px;
}
</style>
