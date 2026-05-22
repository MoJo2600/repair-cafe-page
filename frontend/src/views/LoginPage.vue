<template>
  <v-app>
    <v-main class="bg-surface-variant">
      <v-container class="fill-height" fluid>
        <v-row align="center" justify="center">
          <v-col cols="12" sm="8" md="5" lg="4">
            <v-card elevation="4" rounded="lg">
              <v-card-title class="text-h5 pa-6 pb-2">
                <v-icon class="mr-2" color="primary">mdi-wrench</v-icon>
                RepairCafe
              </v-card-title>
              <v-card-subtitle class="px-6 pb-4">
                Bitte anmelden um fortzufahren
              </v-card-subtitle>

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

                <v-form ref="formRef" @submit.prevent="submit">
                  <v-text-field
                    v-model="username"
                    label="Benutzername"
                    prepend-inner-icon="mdi-account"
                    autocomplete="username"
                    :rules="[required]"
                    variant="outlined"
                    density="comfortable"
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
                    variant="outlined"
                    density="comfortable"
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
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/authStore";

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const formRef = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(
  null
);
const username = ref("");
const password = ref("");
const showPassword = ref(false);
const errorMessage = ref("");

const required = (v: string) => !!v || "Pflichtfeld";

async function submit() {
  const form = formRef.value;
  if (form) {
    const { valid } = await form.validate();
    if (!valid) return;
  }

  errorMessage.value = "";
  const result = await authStore.login(username.value, password.value);

  if (result.success) {
    const redirect = (route.query.redirect as string) || "/";
    router.push(redirect);
  } else {
    errorMessage.value = result.error ?? "Anmeldung fehlgeschlagen";
    password.value = "";
  }
}
</script>
