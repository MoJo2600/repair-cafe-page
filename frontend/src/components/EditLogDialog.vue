<script setup lang="ts">
import { computed, ref, shallowRef, watch } from 'vue'
import type { VForm } from 'vuetify/components'
import { RepairLogsService } from '@/api/services/RepairLogsService'
import type { RepairLog } from '@/api/types'
import type { LogAttachment } from '@/composables/useRepairDetail'
import { useAuthStore } from '@/stores/authStore'
import { useUserStore } from '@/stores/userStore'
import { useToast } from '@/composables/useToast'
import { fileIcon, isImage } from '@/utils/files'
import { errorMessage } from '@/utils/errors'

/** Edit or delete an existing work-log entry. */
const open = defineModel<boolean>({ required: true })

const { repairId, log, attachments } = defineProps<{
  repairId: number
  log: RepairLog | null
  attachments: LogAttachment[]
}>()

const emit = defineEmits<{
  /** Entry was updated or deleted; the owner should reload. */
  changed: []
}>()

const authStore = useAuthStore()
const userStore = useUserStore()
const toast = useToast()

const userItems = computed(() =>
  userStore.users.map((u) => ({ value: u.id, title: `${u.vorname} ${u.nachname}` }))
)
const canDelete = computed(() => authStore.canDeleteOwnedBy(log?.user_id))
const attachmentItems = computed(() =>
  attachments.map((att) => {
    const image = isImage(att.content_type)
    return {
      ...att,
      icon: fileIcon(att.content_type),
      openIcon: image ? 'mdi-open-in-new' : 'mdi-download',
      download: image ? undefined : att.name,
      target: image ? '_blank' : undefined,
    }
  })
)

const formRef = ref<InstanceType<typeof VForm> | null>(null)
const formValid = shallowRef(false)
const saving = shallowRef(false)
const deleting = shallowRef(false)
const confirmDelete = shallowRef(false)
const userId = ref<number | null>(null)
const description = shallowRef('')
const duration = ref<number | null>(null)

watch(open, (isOpen) => {
  if (!isOpen || !log) return
  userId.value = log.user_id ?? null
  description.value = log.reparatur_besch ?? ''
  duration.value = log.reparatur_dauer ?? null
  confirmDelete.value = false
  formRef.value?.resetValidation()
})

async function save() {
  if (!log) return
  const result = await formRef.value?.validate()
  if (!result?.valid) return

  saving.value = true
  try {
    const response = await RepairLogsService.updateRepairLog(repairId, log.id, {
      user_id: userId.value ?? undefined,
      reparatur_besch: description.value,
      reparatur_dauer: duration.value ?? 0,
    })
    if (response.reply === 'done') {
      toast.success('Logeintrag aktualisiert')
      open.value = false
      emit('changed')
    } else {
      toast.error(response.error || 'Fehler beim Speichern')
    }
  } catch (err) {
    toast.error('Fehler beim Speichern: ' + errorMessage(err, 'Unbekannter Fehler'))
  } finally {
    saving.value = false
  }
}

async function remove() {
  if (!log) return
  deleting.value = true
  try {
    const response = await RepairLogsService.deleteRepairLog(repairId, log.id)
    if (response.reply === 'done') {
      toast.success('Logeintrag gelöscht')
      confirmDelete.value = false
      open.value = false
      emit('changed')
    } else {
      toast.error(response.error || 'Fehler beim Löschen')
    }
  } catch (err) {
    toast.error('Fehler beim Löschen: ' + errorMessage(err, 'Unbekannter Fehler'))
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <v-dialog v-model="open" max-width="600px">
    <v-card>
      <v-card-title class="text-headline-small">Logeintrag bearbeiten</v-card-title>
      <v-card-text>
        <v-form ref="formRef" v-model="formValid">
          <v-autocomplete
            v-model="userId"
            :items="userItems"
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
        </v-form>

        <template v-if="attachmentItems.length > 0">
          <v-divider class="my-4"></v-divider>
          <div class="text-title-small mb-1">Anhänge</div>
          <v-list density="compact" class="pa-0">
            <v-list-item
              v-for="att in attachmentItems"
              :key="att.url"
              :prepend-icon="att.icon"
              :href="att.url"
              target="_blank"
            >
              <v-list-item-title>{{ att.name }}</v-list-item-title>
              <template #append>
                <v-btn
                  :icon="att.openIcon"
                  variant="text"
                  size="small"
                  :href="att.url"
                  :download="att.download"
                  :target="att.target"
                  @click.stop
                ></v-btn>
              </template>
            </v-list-item>
          </v-list>
        </template>
      </v-card-text>
      <v-card-actions>
        <v-btn
          v-if="canDelete"
          color="error"
          variant="text"
          prepend-icon="mdi-delete"
          @click="confirmDelete = true"
        >
          Löschen
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn @click="open = false">Abbrechen</v-btn>
        <v-btn color="primary" :disabled="!formValid" :loading="saving" @click="save">
          Speichern
        </v-btn>
      </v-card-actions>
    </v-card>

    <v-dialog v-model="confirmDelete" max-width="400px">
      <v-card>
        <v-card-title class="text-headline-small">Logeintrag löschen</v-card-title>
        <v-card-text>
          Soll dieser Logeintrag wirklich gelöscht werden? Diese Aktion kann nicht rückgängig
          gemacht werden.
        </v-card-text>
        <v-card-actions>
          <v-btn @click="confirmDelete = false">Abbrechen</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="error" :loading="deleting" @click="remove">Löschen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-dialog>
</template>
