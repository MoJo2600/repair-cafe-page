<template>
  <v-app>
    <v-app-bar v-if="canUseApp" color="primary">
      <!-- Larger screens have a permanent menu; small ones open it as an overlay -->
      <v-app-bar-nav-icon
        v-if="smAndDown"
        variant="text"
        aria-label="Menü öffnen"
        @click.stop="navOpen = !navOpen"
      ></v-app-bar-nav-icon>
      <v-img src="/api/config/logo" max-height="40" max-width="40" class="mr-3" contain></v-img>
      <!-- Phones: the logo is enough, the actions need the room -->
      <v-toolbar-title class="d-none d-sm-flex">Repair Cafe</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn icon aria-label="Neue Reparatur" @click="router.push('/create-repair')">
        <v-icon>mdi-plus</v-icon>
      </v-btn>
      <v-btn icon aria-label="QR-Code scannen" @click="qrScannerOpen = true">
        <v-icon>mdi-qrcode-scan</v-icon>
      </v-btn>
      <div
        v-if="authStore.pinUnlockAvailable"
        class="lock-control d-flex flex-column align-center justify-center"
      >
        <v-btn
          icon="mdi-lock"
          variant="text"
          aria-label="Bildschirm sperren"
          title="Bildschirm sperren"
          @click="lockNow"
        />
        <span
          v-if="authStore.autoLockEnabled && secondsUntilLock !== null"
          class="lock-countdown"
          aria-live="off"
        >
          {{ formatLockCountdown(secondsUntilLock) }}
        </span>
      </div>
      <AutoLockMenu
        v-if="authStore.pinUnlockAvailable"
        :auto-lock-enabled="authStore.autoLockEnabled"
        :set-auto-lock="setAutoLockForDevice"
      />
    </v-app-bar>

    <AppNavigation v-if="canUseApp" v-model:open="navOpen" />

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
  </v-app>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import { useAuthStore } from '@/stores/authStore'
import { usePinSession } from '@/composables/usePinSession'
import { useToastQueue } from '@/composables/useToast'
import AppNavigation from '@/components/AppNavigation.vue'
import AutoLockMenu from '@/components/AutoLockMenu.vue'
import QrScannerDialog from '@/components/QrScannerDialog.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toastQueue = useToastQueue()
const { canUseApp, lockNow, secondsUntilLock, setAutoLockForDevice } = usePinSession()
const { smAndDown } = useDisplay()

const navOpen = ref(false)
const qrScannerOpen = ref(false)

function formatLockCountdown(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  return `${minutes}:${String(seconds % 60).padStart(2, '0')}`
}

// Nothing from the previous user may stay visible behind the PIN screen
watch(canUseApp, (active) => {
  if (!active) {
    navOpen.value = false
    qrScannerOpen.value = false
    toastQueue.value = []
  }
})

// Set all favicon / touch-icon links to the dynamic logo endpoint
onMounted(() => {
  document
    .querySelectorAll<HTMLLinkElement>('link[rel="icon"], link[rel="apple-touch-icon"]')
    .forEach((el) => {
      el.href = '/api/config/logo'
    })
})
</script>

<style scoped>
.lock-control {
  min-width: 48px;
}

.lock-countdown {
  margin-top: -8px;
  padding-bottom: 3px;
  font-size: 0.75rem;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}
</style>
