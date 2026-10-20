<template>
  <section class="login-page bg-surface-variant d-flex align-center">
    <v-container fluid>
      <v-row align="center" justify="center">
        <v-col cols="12" sm="8" md="5" lg="4">
          <v-card elevation="4" rounded="lg">
            <v-card-title class="text-h5 pa-6 pb-2">
              <v-icon class="mr-2" color="primary">mdi-wrench</v-icon>
              RepairCafe
            </v-card-title>
            <v-card-subtitle class="px-6 pb-4"> Bitte anmelden um fortzufahren </v-card-subtitle>

            <v-card-text class="px-6 pt-0">
              <v-alert
                v-if="errorMessage"
                type="error"
                variant="tonal"
                class="mb-4"
                density="compact"
              >
                {{ errorMessage }}
              </v-alert>

              <template v-if="oidcEnabled">
                <v-btn
                  color="primary"
                  block
                  size="large"
                  prepend-icon="mdi-account-key"
                  :href="ssoUrl"
                >
                  Mit SSO anmelden
                </v-btn>

                <v-expansion-panels class="mt-6" variant="accordion">
                  <v-expansion-panel title="Admin-Anmeldung (lokal)">
                    <v-expansion-panel-text>
                      <v-form ref="formRef" @submit.prevent="submit">
                        <v-text-field
                          v-model="username"
                          label="Benutzername"
                          prepend-inner-icon="mdi-account"
                          autocomplete="username"
                          :rules="[required]"
                          class="mb-3"
                        />
                        <v-text-field
                          v-model="password"
                          label="Passwort"
                          prepend-inner-icon="mdi-lock"
                          :type="showPassword ? 'text' : 'password'"
                          :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                          autocomplete="current-password"
                          :rules="[required]"
                          @click:append-inner="showPassword = !showPassword"
                        />
                        <v-btn
                          type="submit"
                          variant="tonal"
                          block
                          :loading="authStore.loading"
                          class="mt-2"
                        >
                          Anmelden
                        </v-btn>
                      </v-form>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </template>

              <v-form v-else ref="formRef" @submit.prevent="submit">
                <v-text-field
                  v-model="username"
                  label="Benutzername"
                  prepend-inner-icon="mdi-account"
                  autocomplete="username"
                  :rules="[required]"
                  class="mb-3"
                  autofocus
                />
                <v-text-field
                  v-model="password"
                  label="Passwort"
                  prepend-inner-icon="mdi-lock"
                  :type="showPassword ? 'text' : 'password'"
                  :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                  autocomplete="current-password"
                  :rules="[required]"
                  @click:append-inner="showPassword = !showPassword"
                />
                <v-btn
                  type="submit"
                  color="primary"
                  block
                  size="large"
                  :loading="authStore.loading"
                  class="mt-2"
                >
                  Anmelden
                </v-btn>
              </v-form>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { AuthService } from '@/api/services/AuthService'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const formRef = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(null)
const username = ref('')
const password = ref('')
const showPassword = ref(false)
const oidcEnabled = ref(false)

// Error codes set by the backend's SSO callback (/login?error=...)
const SSO_ERRORS: Record<string, string> = {
  forbidden: 'Dein SSO-Konto hat keinen Zugriff auf diese Anwendung.',
  disabled: 'Dein Konto wurde deaktiviert. Bitte wende dich an einen Admin.',
  account_conflict:
    'Deine E-Mail-Adresse ist bereits einem lokalen Admin-Konto zugeordnet. Bitte wende dich an einen Admin.',
  sso_failed: 'Die SSO-Anmeldung ist fehlgeschlagen. Bitte erneut versuchen.',
  sso_unavailable: 'Die SSO-Anmeldung ist derzeit nicht verfügbar.',
}
const errorCode = route.query.error as string | undefined
const errorMessage = ref(errorCode ? (SSO_ERRORS[errorCode] ?? SSO_ERRORS.sso_failed) : '')

const redirectTarget = computed(() => (route.query.redirect as string) || '/')
const ssoUrl = computed(() => AuthService.oidcLoginUrl(redirectTarget.value))

const required = (v: string) => !!v || 'Pflichtfeld'

onMounted(async () => {
  try {
    oidcEnabled.value = (await AuthService.config()).oidc_enabled
  } catch {
    oidcEnabled.value = false
  }
})

async function submit() {
  const form = formRef.value
  if (form) {
    const { valid } = await form.validate()
    if (!valid) return
  }

  errorMessage.value = ''
  const result = await authStore.login(username.value, password.value)

  if (result.success) {
    router.push(redirectTarget.value)
  } else {
    errorMessage.value = result.error ?? 'Anmeldung fehlgeschlagen'
    password.value = ''
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  min-height: 100dvh;
}
</style>
