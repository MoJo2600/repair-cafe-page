<script setup lang="ts">
import { computed, onScopeDispose, ref, watch } from 'vue'
import { useCameraStream } from '@/composables/useCameraStream'
import { useToast } from '@/composables/useToast'
import { dataUrlToFile } from '@/utils/files'
import DevicePhoto from '@/components/ui/DevicePhoto.vue'

/**
 * The one photo of a device (more photos belong to log entries). v-model is the
 * JPEG/PNG file or null. Live camera on the PC; "Foto wählen" opens the camera app
 * on tablets and phones.
 */
const photo = defineModel<File | null>({ required: true })

const {
  active = true,
  category = null,
} = defineProps<{
  /** False while the surrounding step/dialog is hidden; stops the camera. */
  active?: boolean
  /** For the placeholder while there is no photo. */
  category?: string | null
}>()

const toast = useToast()

const videoElement = ref<HTMLVideoElement | null>(null)
const photoCanvas = ref<HTMLCanvasElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const camera = useCameraStream(videoElement)

const previewUrl = computed(() => (photo.value ? URL.createObjectURL(photo.value) : null))
watch(previewUrl, (_next, previous) => {
  if (previous) URL.revokeObjectURL(previous)
})
onScopeDispose(() => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})

watch(
  () => active,
  (isActive) => {
    if (!isActive) camera.stop()
  }
)

async function startCamera() {
  const started = await camera.start()
  if (!started && camera.permissionDenied.value) toast.error('Kein Zugriff auf die Kamera')
}

function capture() {
  const video = videoElement.value
  const canvas = photoCanvas.value
  if (!video || !canvas) return
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  canvas.getContext('2d')?.drawImage(video, 0, 0, canvas.width, canvas.height)
  photo.value = dataUrlToFile(canvas.toDataURL('image/jpeg', 0.85), `geraet_${Date.now()}.jpg`)
  camera.stop()
}

function onFileChosen(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) photo.value = file
  ;(event.target as HTMLInputElement).value = ''
}
</script>

<template>
  <div class="device-photo-capture">
    <div v-if="camera.active.value" class="mb-3">
      <video ref="videoElement" class="camera-preview" autoplay playsinline></video>
      <canvas ref="photoCanvas" class="d-none"></canvas>
    </div>
    <DevicePhoto v-else :src="previewUrl" :category="category" :height="200" class="mb-3" />

    <div class="d-flex flex-wrap ga-2">
      <template v-if="camera.active.value">
        <v-btn color="primary" variant="flat" size="large" prepend-icon="mdi-camera" @click="capture">
          Aufnehmen
        </v-btn>
        <v-btn variant="text" size="large" @click="camera.stop()">Abbrechen</v-btn>
      </template>
      <template v-else>
        <v-btn
          color="primary"
          variant="tonal"
          size="large"
          prepend-icon="mdi-camera"
          :disabled="camera.permissionDenied.value"
          @click="startCamera"
        >
          {{ photo ? 'Neu aufnehmen' : 'Kamera starten' }}
        </v-btn>
        <v-btn variant="tonal" size="large" prepend-icon="mdi-image" @click="fileInput?.click()">
          Foto wählen
        </v-btn>
        <v-btn
          v-if="photo"
          color="error"
          variant="text"
          size="large"
          prepend-icon="mdi-delete"
          @click="photo = null"
        >
          Entfernen
        </v-btn>
      </template>
    </div>
    <input
      ref="fileInput"
      type="file"
      accept="image/*"
      capture="environment"
      class="d-none"
      @change="onFileChosen"
    />

    <v-alert v-if="camera.permissionDenied.value" type="error" variant="tonal" class="mt-3">
      Kein Kamerazugriff. Bitte den Zugriff in den Browser-Einstellungen erlauben oder ein Foto
      wählen.
    </v-alert>
  </div>
</template>

<style scoped>
.device-photo-capture {
  max-width: 480px;
}

.camera-preview {
  width: 100%;
  max-height: 360px;
  background: #000;
  border-radius: 4px;
}
</style>
