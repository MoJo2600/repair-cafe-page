<script setup lang="ts">
import { ref, shallowRef, watch } from 'vue'
import { useRouter } from 'vue-router'
import jsQR from 'jsqr'
import { useCameraStream } from '@/composables/useCameraStream'
import { useToast } from '@/composables/useToast'

/** Scans repair labels and opens the repair. Camera runs only while open. */
const open = defineModel<boolean>({ required: true })

const router = useRouter()
const toast = useToast()

// Labels encode <APP_URL>/edit/<qr_token> (see label_service.py)
const REPAIR_URL_PATTERN = /\/edit\/([a-f0-9]{32})\b/

const videoElement = ref<HTMLVideoElement | null>(null)
const canvasElement = ref<HTMLCanvasElement | null>(null)
const scanning = shallowRef(false)
const camera = useCameraStream(videoElement)
let animationFrameId: number | null = null

watch(open, (isOpen) => {
  if (isOpen) {
    void start()
  } else {
    stop()
  }
})

async function start() {
  const started = await camera.start()
  if (started && open.value) {
    scanning.value = true
    scanFrame()
  } else if (camera.permissionDenied.value) {
    toast.error('Could not access camera. Please check permissions.')
  }
}

function stop() {
  scanning.value = false
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }
  camera.stop()
}

function close() {
  open.value = false
}

function scanFrame() {
  const video = videoElement.value
  const canvas = canvasElement.value
  if (!video || !canvas || !scanning.value) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  canvas.width = video.videoWidth
  canvas.height = video.videoHeight

  if (canvas.width > 0 && canvas.height > 0) {
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const code = jsQR(imageData.data, imageData.width, imageData.height, {
      inversionAttempts: 'dontInvert',
    })
    if (code) {
      handleDetected(code.data)
      return
    }
  }

  animationFrameId = requestAnimationFrame(scanFrame)
}

function handleDetected(data: string) {
  close()
  const token = data.match(REPAIR_URL_PATTERN)?.[1]
  if (token) {
    void router.push(`/edit/${token}`)
    toast.success('QR Code scanned successfully!')
  } else {
    toast.info(`Scanned: ${data}`, 6000)
  }
}
</script>

<template>
  <v-dialog v-model="open" max-width="600px">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon icon="mdi-qrcode-scan" class="mr-2"></v-icon>
        <span>Scan QR Code</span>
        <v-spacer></v-spacer>
        <v-btn icon="mdi-close" variant="text" @click="close"></v-btn>
      </v-card-title>
      <v-card-text>
        <div v-if="!camera.permissionDenied.value">
          <video ref="videoElement" class="qr-video" autoplay playsinline></video>
          <canvas ref="canvasElement" class="d-none"></canvas>
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
        <v-btn color="grey" variant="text" @click="close"> Cancel </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.qr-video {
  width: 100%;
  max-height: 400px;
  background: #000;
}
</style>
