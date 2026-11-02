<template>
  <v-app>
    <v-app-bar v-if="canUseApp" color="primary" prominent>
      <v-app-bar-nav-icon variant="text" @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
      <v-img src="/api/config/logo" max-height="40" max-width="40" class="mr-3" contain></v-img>
      <v-toolbar-title>Repair Cafe</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn icon @click="router.push('/create-repair')">
        <v-icon>mdi-plus</v-icon>
      </v-btn>
      <v-btn icon aria-label="QR-Code scannen" @click="qrScannerOpen = true">
        <v-icon>mdi-qrcode-scan</v-icon>
      </v-btn>
      <v-btn v-if="authStore.pinUnlockAvailable" icon aria-label="Bildschirm sperren" @click="lockNow">
        <v-icon>mdi-lock-outline</v-icon>
      </v-btn>
      <v-btn icon>
        <v-icon>mdi-magnify</v-icon>
      </v-btn>
    </v-app-bar>

    <v-navigation-drawer
      v-if="canUseApp"
      v-model="drawer"
      :temporary="false"
      width="180"
      app
    >
      <v-list nav>
        <v-list-item :to="'/dashboard'" value="dashboard" class="text-center" min-height="64">
          <div class="d-flex flex-column align-center justify-center py-1">
            <v-icon icon="mdi-view-dashboard" class="mb-1" />
            <span class="text-body-small">Dashboard</span>
          </div>
        </v-list-item>
        <v-list-item :to="'/'" value="home" class="text-center" min-height="64">
          <div class="d-flex flex-column align-center justify-center py-1">
            <v-icon icon="mdi-home" class="mb-1" />
            <span class="text-body-small">Reparaturen</span>
          </div>
        </v-list-item>
        <v-list-item :to="'/repairs'" value="list" class="text-center" min-height="64">
          <div class="d-flex flex-column align-center justify-center py-1">
            <v-icon icon="mdi-format-list-bulleted" class="mb-1" />
            <span class="text-body-small">Reparaturliste</span>
          </div>
        </v-list-item>
        <v-list-item :to="'/customers'" value="customers" class="text-center" min-height="64">
          <div class="d-flex flex-column align-center justify-center py-1">
            <v-icon icon="mdi-account-group" class="mb-1" />
            <span class="text-body-small">Kunden</span>
          </div>
        </v-list-item>
        <v-list-item
          v-if="authStore.isAdmin"
          :to="'/users'"
          value="users"
          class="text-center"
          min-height="64"
        >
          <div class="d-flex flex-column align-center justify-center py-1">
            <v-icon icon="mdi-account-cog" class="mb-1" />
            <span class="text-body-small">Benutzerverwaltung</span>
          </div>
        </v-list-item>
        <v-list-item
          v-if="authStore.isAdmin"
          :to="'/settings'"
          value="settings"
          class="text-center"
          min-height="64"
        >
          <div class="d-flex flex-column align-center justify-center py-1">
            <v-icon icon="mdi-cog" class="mb-1" />
            <span class="text-body-small">Einstellungen</span>
          </div>
        </v-list-item>
      </v-list>
      <template #append>
        <v-divider />
        <v-list v-if="authStore.currentUser" aria-label="Benutzerkonto">
          <v-list-item
            :to="{ name: 'Profile' }"
            prepend-icon="mdi-account-circle"
            aria-label="Mein Profil"
          >
            <v-list-item-title class="text-body-medium text-wrap">{{
              currentUserName
            }}</v-list-item-title>
            <v-list-item-subtitle class="text-wrap">{{
              authStore.currentUser.username
            }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item
            prepend-icon="mdi-logout"
            title="Abmelden"
            :disabled="loggingOut"
            @click="logout"
          >
            <template v-if="loggingOut" #append>
              <v-progress-circular
                indeterminate
                size="20"
                width="2"
                aria-label="Abmeldung laeuft"
              />
            </template>
          </v-list-item>
        </v-list>
        <v-list v-else>
          <v-list-item :to="{ name: 'Login' }" prepend-icon="mdi-login" title="Anmelden" />
        </v-list>
      </template>
    </v-navigation-drawer>

    <v-main>
      <v-container fluid :class="{ 'pa-0': !canUseApp }">
        <router-view v-slot="{ Component }">
          <component
            :is="Component"
            v-if="canUseApp || route.name === 'Login' || route.name === 'PinLock'"
          />
        </router-view>
      </v-container>
    </v-main>

    <!-- Global toasts (useToast); unmounted while locked so nothing shows on the PIN screen -->
    <v-snackbar-queue v-if="canUseApp" v-model="toastQueue" location="bottom right" closable />

    <QrScannerDialog v-if="canUseApp" v-model="qrScannerOpen" />

    <v-footer v-if="canUseApp" app>
      <v-spacer></v-spacer>
      <div>&copy; {{ new Date().getFullYear() }} Repair Cafe</div>
    </v-footer>
  </v-app>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { usePinSession } from '@/composables/usePinSession'
import { useToast, useToastQueue } from '@/composables/useToast'
import QrScannerDialog from '@/components/QrScannerDialog.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toast = useToast()
const toastQueue = useToastQueue()
const { canUseApp, lockNow } = usePinSession()

const drawer = ref(true)
const qrScannerOpen = ref(false)
const loggingOut = ref(false)
const currentUserName = computed(() => {
  const user = authStore.currentUser
  return [user?.vorname, user?.nachname].filter(Boolean).join(' ') || user?.username || ''
})

// Nothing from the previous user may stay visible behind the PIN screen
watch(canUseApp, (active) => {
  if (!active) {
    qrScannerOpen.value = false
    toastQueue.value = []
  }
})

async function logout() {
  if (loggingOut.value) return
  loggingOut.value = true
  try {
    await authStore.logout()
    await router.replace({ name: 'Login' })
  } catch {
    toast.error('Abmelden fehlgeschlagen. Bitte erneut versuchen.')
  } finally {
    loggingOut.value = false
  }
}

// Set all favicon / touch-icon links to the dynamic logo endpoint
onMounted(() => {
  document
    .querySelectorAll<HTMLLinkElement>('link[rel="icon"], link[rel="apple-touch-icon"]')
    .forEach((el) => {
      el.href = '/api/config/logo'
    })
})
</script>
