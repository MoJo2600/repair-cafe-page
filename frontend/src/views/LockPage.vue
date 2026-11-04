<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import DashboardSummary from '@/components/dashboard/DashboardSummary.vue'
import PinUnlockDialog from '@/components/PinUnlockDialog.vue'
import { redirectTarget } from '@/utils/redirect'

/** Shown while the shared PC is locked: public repair figures plus the way back in. */
const router = useRouter()
const route = useRoute()
const ssoUrl = computed(
  () => `/api/auth/oidc/login?next=${encodeURIComponent(redirectTarget(route.query))}`
)
const authStore = useAuthStore()

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
</script>

<template>
  <div class="lock-page">
    <v-container fluid class="lock-content">
      <v-card border class="mb-4">
        <v-card-item>
          <template #prepend>
            <v-avatar size="48" rounded="lg" color="primary" variant="tonal">
              <v-img v-if="!logoFailed" src="/api/config/logo" alt="Repair Café" @error="logoFailed = true" />
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
                variant="flat"
                size="large"
                prepend-icon="mdi-lock-open-outline"
                @click="unlockOpen = true"
              >
                Entsperren
              </v-btn>
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
              <v-btn
                icon="mdi-logout"
                variant="text"
                aria-label="Vollständig abmelden"
                title="Vollständig abmelden"
                :loading="loggingOut"
                @click="logout"
              />
            </div>
          </template>
        </v-card-item>
        <v-alert v-if="logoutError" type="error" variant="tonal" density="compact" class="ma-4 mt-0">
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
  background-color: rgb(var(--v-theme-background));
}

.lock-content {
  max-width: 1600px;
}
</style>
