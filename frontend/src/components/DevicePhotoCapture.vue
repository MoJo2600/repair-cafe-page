<script setup lang="ts">
import { computed, onScopeDispose, ref, shallowRef, watch } from 'vue'
import { useCameraStream } from '@/composables/useCameraStream'
import { useToast } from '@/composables/useToast'
import { dataUrlToFile } from '@/utils/files'
import ResponsiveDialog from '@/components/ResponsiveDialog.vue'

/** Photos of a device taken with the camera; v-model is the list of JPEG files. */
const photos = defineModel<File[]>({ required: true })

const { active = true } = defineProps<{
  /** False while the surrounding step is hidden; stops the camera. */
  active?: boolean
}>()

const toast = useToast()

const videoElement = ref<HTMLVideoElement | null>(null)
const photoCanvas = ref<HTMLCanvasElement | null>(null)
const camera = useCameraStream(videoElement)

// Object URLs for thumbnails; revoked when the list changes or the component goes away
const previews = computed(() => photos.value.map((file) => URL.createObjectURL(file)))
watch(previews, (_next, previous) => previous?.forEach((url) => URL.revokeObjectURL(url)))
onScopeDispose(() => previews.value.forEach((url) => URL.revokeObjectURL(url)))

const previewOpen = shallowRef(false)
const previewUrl = shallowRef('')

async function startCamera() {
  const started = await camera.start()
  if (!started && camera.permissionDenied.value) {
    toast.error('Kein Zugriff auf die Kamera')
  }
}

function capture() {
  const video = videoElement.value
  const canvas = photoCanvas.value
  if (!video || !canvas) return
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  canvas.getContext('2d')?.drawImage(video, 0, 0, canvas.width, canvas.height)
  const file = dataUrlToFile(canvas.toDataURL('image/jpeg', 0.8), `geraet_${Date.now()}.jpg`)
  photos.value = [...photos.value, file]
}

function remove(index: number) {
  photos.value = photos.value.filter((_, i) => i !== index)
}

function showPreview(index: number) {
  previewUrl.value = previews.value[index] ?? ''
  previewOpen.value = true
}

watch(
  () => active,
  (isActive) => {
    if (!isActive) camera.stop()
  }
)
</script>

<template>
  <div>
    <div v-if="camera.active.value" class="mb-3">
      <video ref="videoElement" class="camera-preview" autoplay playsinline></video>
      <canvas ref="photoCanvas" class="d-none"></canvas>
    </div>

    <div class="d-flex flex-wrap ga-2 mb-3">
      <template v-if="camera.active.value">
        <v-btn color="primary" variant="flat" size="large" prepend-icon="mdi-camera" @click="capture">
          Foto aufnehmen
        </v-btn>
        <v-btn variant="text" size="large" prepend-icon="mdi-close" @click="camera.stop()">
          Kamera schließen
        </v-btn>
      </template>
      <v-btn
        v-else
        color="primary"
        variant="tonal"
        size="large"
        prepend-icon="mdi-camera"
        :disabled="camera.permissionDenied.value"
        @click="startCamera"
      >
        Kamera starten
      </v-btn>
    </div>

    <v-alert v-if="camera.permissionDenied.value" type="error" variant="tonal" class="mb-3">
      Kein Kamerazugriff. Bitte den Zugriff in den Browser-Einstellungen erlauben.
    </v-alert>

    <v-row v-if="previews.length > 0" density="compact">
      <v-col v-for="(url, index) in previews" :key="url" cols="6" sm="4" md="3">
        <v-card border>
          <v-img :src="url" aspect-ratio="1" cover class="cursor-pointer" @click="showPreview(index)" />
          <v-card-actions class="py-0">
            <v-spacer />
            <v-btn
              icon="mdi-delete"
              color="error"
              variant="text"
              aria-label="Foto entfernen"
              @click="remove(index)"
            />
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <ResponsiveDialog v-model="previewOpen" max-width="900px">
      <v-card>
        <v-img :src="previewUrl" max-height="80vh" contain />
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="previewOpen = false">Schließen</v-btn>
        </v-card-actions>
      </v-card>
    </ResponsiveDialog>
  </div>
</template>

<style scoped>
.camera-preview {
  width: 100%;
  max-height: 400px;
  background: #000;
  border-radius: 4px;
}
</style>
