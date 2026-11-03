<script setup lang="ts">
import ResponsiveDialog from '@/components/ResponsiveDialog.vue'
import { api, asFormData } from '@/api/client'
import { ref, shallowRef, watch } from 'vue'
import type { VForm } from 'vuetify/components'
import { useAuthStore } from '@/stores/authStore'
import { useUserStore } from '@/stores/userStore'
import { useCameraStream } from '@/composables/useCameraStream'
import { useToast } from '@/composables/useToast'
import { dataUrlToFile } from '@/utils/files'
import { errorMessage } from '@/utils/errors'

/** New work-log entry with optional photos/files for a repair. */
const open = defineModel<boolean>({ required: true })

const { repairId } = defineProps<{ repairId: number }>()

const emit = defineEmits<{
  /** Entry (and possibly attachments) saved; the owner should reload. */
  saved: []
}>()

const authStore = useAuthStore()
const userStore = useUserStore()
const toast = useToast()


const formRef = ref<InstanceType<typeof VForm> | null>(null)
const formValid = shallowRef(false)
const saving = shallowRef(false)
const userId = ref<number | null>(null)
const description = shallowRef('')
const duration = ref<number | null>(null)
const files = ref<File[]>([])

const videoElement = ref<HTMLVideoElement | null>(null)
const photoCanvas = ref<HTMLCanvasElement | null>(null)
const camera = useCameraStream(videoElement)

watch(open, (isOpen) => {
  if (isOpen) {
    userId.value = authStore.currentUser?.id ?? null
    description.value = ''
    duration.value = null
    files.value = []
    formRef.value?.resetValidation()
  } else {
    // Also covers closing via scrim/Esc
    camera.stop()
  }
})

function capturePhoto() {
  const video = videoElement.value
  const canvas = photoCanvas.value
  if (!video || !canvas) return
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.drawImage(video, 0, 0)
  const photo = dataUrlToFile(canvas.toDataURL('image/jpeg', 0.8), `foto_${Date.now()}.jpg`)
  files.value = [...files.value, photo]
}

async function save() {
  const result = await formRef.value?.validate()
  if (!result?.valid) return

  saving.value = true
  try {
    const response = await api.createRepairLog({ repairId: repairId }, { repair_id: repairId, user_id: userId.value ?? undefined,
      reparatur_dauer: duration.value ?? 0,
      reparatur_besch: description.value })
    if (response.reply !== 'done') {
      toast.error(
        'Fehler beim Hinzufügen des Logeintrags: ' + (response.error || 'Unbekannter Fehler')
      )
      return
    }

    if (response.id && files.value.length > 0) {
      try {
        await api.uploadRepairAttachments(
          { repairId },
          asFormData({ files: files.value, attachment_type: 'log_entry', log_id: response.id })
        )
      } catch (err) {
        // The entry itself is saved; don't report the whole save as failed
        toast.warning(
          'Logeintrag gespeichert, aber Anhänge konnten nicht hochgeladen werden: ' +
            errorMessage(err, 'Unbekannter Fehler')
        )
        open.value = false
        emit('saved')
        return
      }
    }

    toast.success('Logeintrag erfolgreich hinzugefügt')
    open.value = false
    emit('saved')
  } catch (err) {
    console.error('Error adding log entry:', err)
    toast.error('Fehler beim Speichern: ' + errorMessage(err, 'Unbekannter Fehler'))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <ResponsiveDialog v-model="open" max-width="600px">
    <v-card>
      <v-card-title class="text-headline-small">Neue Notiz</v-card-title>

      <v-card-text>
        <v-form ref="formRef" v-model="formValid">
          <v-autocomplete
            v-model="userId"
            :items="userStore.userOptions"
            item-value="value"
            item-title="title"
            label="Reparateur"
            required
            :loading="userStore.loading"
            :rules="[(v) => !!v || 'Reparateur ist erforderlich']"
          ></v-autocomplete>

          <v-textarea
            v-model="description"
            label="Was wurde gemacht?"
            rows="3"
            required
            :rules="[(v) => !!v || 'Beschreibung ist erforderlich']"
          ></v-textarea>

          <v-text-field
            v-model.number="duration"
            label="Dauer in Minuten (Optional)"
            type="number"
          ></v-text-field>

          <v-divider class="my-4"></v-divider>
          <div class="text-title-small mb-3">Fotos &amp; Dateien (optional)</div>

          <div v-if="camera.active.value" class="mb-3">
            <video ref="videoElement" class="camera-preview" autoplay playsinline></video>
            <canvas ref="photoCanvas" class="d-none"></canvas>
          </div>

          <div class="d-flex ga-2 flex-wrap mb-3">
            <template v-if="camera.active.value">
              <v-btn color="success" size="small" prepend-icon="mdi-camera" @click="capturePhoto">
                Aufnehmen
              </v-btn>
              <v-btn size="small" prepend-icon="mdi-close" @click="camera.stop()">Stop</v-btn>
            </template>
            <v-btn
              v-else
              size="small"
              prepend-icon="mdi-camera"
              :disabled="camera.permissionDenied.value"
              @click="camera.start()"
            >
              Foto aufnehmen
            </v-btn>
          </div>

          <v-alert
            v-if="camera.permissionDenied.value"
            type="error"
            density="compact"
            class="mb-3"
          >
            Kamerazugriff verweigert.
          </v-alert>

          <v-file-upload
            v-model="files"
            multiple
            inset-file-list
            show-size
            clearable
            title="Fotos &amp; Dateien"
            subtitle="Auswählen oder ablegen"
            browse-text="Durchsuchen"
          ></v-file-upload>
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-btn @click="open = false">Abbrechen</v-btn>
        <v-spacer></v-spacer>
        <v-btn color="primary" :disabled="!formValid" :loading="saving" @click="save">
          Speichern
        </v-btn>
      </v-card-actions>
    </v-card>
  </ResponsiveDialog>
</template>

<style scoped>
.camera-preview {
  width: 100%;
  max-height: 200px;
  background: #000;
  border-radius: 4px;
}
</style>
