<template>
  <v-app>
    <v-app-bar color="primary" prominent>
      <v-app-bar-nav-icon variant="text" @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
      <v-img src="/api/config/logo" max-height="40" max-width="40" class="mr-3" contain></v-img>
      <v-toolbar-title>Repair Cafe</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn icon @click="openQrScanner">
        <v-icon>mdi-qrcode-scan</v-icon>
      </v-btn>
      <v-btn icon>
        <v-icon>mdi-magnify</v-icon>
      </v-btn>
    </v-app-bar>

    <v-navigation-drawer v-model="drawer" temporary>
      <v-list>
        <v-list-item prepend-icon="mdi-home" title="Home" value="home" :to="'/'"></v-list-item>
        <v-list-item prepend-icon="mdi-format-list-bulleted" title="Repairs List" value="list"
          :to="'/repairs'"></v-list-item>
        <v-list-item prepend-icon="mdi-account-group" title="Kunden" value="customers" :to="'/customers'"></v-list-item>
        <v-list-item v-if="authStore.isAdmin" prepend-icon="mdi-account-cog" title="Benutzerverwaltung" value="users"
          :to="'/users'"></v-list-item>
        <v-list-item v-if="authStore.isAdmin" prepend-icon="mdi-cog" title="Einstellungen" value="settings"
          :to="'/settings'"></v-list-item>
        <!-- <v-list-item 
          prepend-icon="mdi-pencil" 
          title="Edit" 
          value="edit"
          :to="'/edit'"
        ></v-list-item> -->
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <v-container fluid>
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </v-container>
    </v-main>

    <!-- Global snackbar -->
    <v-snackbar v-model="toastVisible" :timeout="toastTimeout" :color="toastColor" location="bottom right">
      {{ toastMessage }}
      <template #actions>
        <v-btn icon="mdi-close" variant="text" @click="toastVisible = false"></v-btn>
      </template>
    </v-snackbar>

    <!-- QR Scanner Dialog -->
    <v-dialog v-model="qrScannerDialog" max-width="600px">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon icon="mdi-qrcode-scan" class="mr-2"></v-icon>
          <span>Scan QR Code</span>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" @click="closeQrScanner"></v-btn>
        </v-card-title>
        <v-card-text>
          <div v-if="!cameraPermissionDenied">
            <video ref="videoElement" autoplay playsinline
              style="width: 100%; max-height: 400px; background: #000;"></video>
            <canvas ref="canvasElement" style="display: none;"></canvas>
            <div v-if="scanning" class="text-center mt-3">
              <v-progress-circular indeterminate color="primary"></v-progress-circular>
              <p class="mt-2">Scanning for QR codes...</p>
            </div>
          </div>
          <v-alert v-else type="error" class="mt-3">
            Camera permission denied. Please allow camera access in your browser settings.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="closeQrScanner">
            Cancel
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-footer app>
      <v-spacer></v-spacer>
      <div>&copy; {{ new Date().getFullYear() }} Repair Cafe</div>
    </v-footer>
  </v-app>
</template>

<script setup lang="ts">
import { ref, provide, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import jsQR from 'jsqr'

const router = useRouter()
const authStore = useAuthStore()
const drawer = ref(false)

// Set all favicon / touch-icon links to the dynamic logo endpoint
onMounted(() => {
  const logoUrl = '/api/config/logo'
  document.querySelectorAll<HTMLLinkElement>('link[rel="icon"], link[rel="apple-touch-icon"]').forEach(el => {
    el.href = logoUrl
  })
})

// Global toast state
const toastVisible = ref(false)
const toastMessage = ref('')
const toastColor = ref<'success' | 'error' | 'warning' | 'info' | string>('info')
const toastTimeout = ref(4000)

// QR Scanner state
const qrScannerDialog = ref(false)
const videoElement = ref<HTMLVideoElement | null>(null)
const canvasElement = ref<HTMLCanvasElement | null>(null)
const scanning = ref(false)
const cameraPermissionDenied = ref(false)
let mediaStream: MediaStream | null = null
let animationFrameId: number | null = null

function showToast(message: string, options?: { color?: string; timeout?: number }) {
  toastMessage.value = message
  toastColor.value = options?.color ?? 'error'
  toastTimeout.value = options?.timeout ?? 4000
  toastVisible.value = true
}

async function openQrScanner() {
  qrScannerDialog.value = true
  cameraPermissionDenied.value = false

  try {
    // Request camera access
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' } // Use back camera on mobile
    })

    if (videoElement.value) {
      videoElement.value.srcObject = mediaStream
      videoElement.value.play()
      scanning.value = true
      scanQRCode()
    }
  } catch (error) {
    console.error('Error accessing camera:', error)
    cameraPermissionDenied.value = true
    showToast('Could not access camera. Please check permissions.', { color: 'error' })
  }
}

function scanQRCode() {
  if (!videoElement.value || !canvasElement.value || !scanning.value) return

  const video = videoElement.value
  const canvas = canvasElement.value
  const ctx = canvas.getContext('2d')

  if (!ctx) return

  // Set canvas size to match video
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight

  if (canvas.width > 0 && canvas.height > 0) {
    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

    // Get image data
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)

    // Scan for QR code
    const code = jsQR(imageData.data, imageData.width, imageData.height, {
      inversionAttempts: 'dontInvert',
    })

    if (code) {
      handleQRCodeDetected(code.data)
      return
    }
  }

  // Continue scanning
  animationFrameId = requestAnimationFrame(scanQRCode)
}

function handleQRCodeDetected(data: string) {
  console.log('QR Code detected:', data)

  // Extract token from URL or use data directly
  let token = data

  // Check if it's a URL containing /edit/<id>/<token>
  const urlMatch = data.match(/\/edit\/(\d+)\/([a-f0-9]+)/)
  if (urlMatch) {
    const id = urlMatch[1]
    token = urlMatch[2]

    // Navigate to edit page with token
    closeQrScanner()
    router.push(`/edit/${id}/${token}`)
    showToast('QR Code scanned successfully!', { color: 'success' })
    return
  }

  // If it's just a token or repair ID, show it
  closeQrScanner()
  showToast(`Scanned: ${data}`, { color: 'info', timeout: 6000 })
}

function closeQrScanner() {
  scanning.value = false
  qrScannerDialog.value = false

  // Stop animation frame
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }

  // Stop media stream
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }

  // Clear video source
  if (videoElement.value) {
    videoElement.value.srcObject = null
  }
}

// Cleanup on component unmount
onUnmounted(() => {
  closeQrScanner()
})

// Expose globally via provide/inject
provide('showToast', showToast)
</script>
