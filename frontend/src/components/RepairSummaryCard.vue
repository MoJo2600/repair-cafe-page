<template>
  <v-card class="mb-4 summary">
    <div class="summary-layout">
      <div class="summary-photo">
        <DevicePhoto :src="photoUrl" :category="repairData.repair_type?.name" height="100%" />
        <v-btn
          v-if="repairData.id"
          class="photo-action"
          variant="flat"
          size="small"
          prepend-icon="mdi-camera"
          @click="openPhotoDialog"
        >
          {{ photoUrl ? 'Foto ändern' : 'Foto hinzufügen' }}
        </v-btn>
      </div>

      <div class="summary-body">
        <v-card-item>
          <template #prepend>
            <RepairNumber :id="repairData.id" :status="repairData.status" />
          </template>
          <v-card-title class="text-headline-small text-wrap">{{ repairData.geraet_art }}</v-card-title>
          <v-card-subtitle v-if="repairData.datum">
            Angenommen am {{ formatDate(repairData.datum) }}
          </v-card-subtitle>
          <template v-if="repairData.id" #append>
            <v-btn icon="mdi-pencil" variant="text" aria-label="Reparatur bearbeiten" @click="openEditDialog" />
          </template>
        </v-card-item>

        <v-card-text>
          <RepairMeta :status="repairData.status" :category="repairData.repair_type?.name" class="mb-4" />

          <div class="text-title-small text-medium-emphasis">Beschreibung des Defekts</div>
          <p class="text-body-large mb-4">{{ repairData.defekt_besch || '–' }}</p>

          <v-row density="compact">
            <v-col cols="12" sm="6">
              <v-list density="compact" class="py-0" bg-color="transparent">
                <v-list-item prepend-icon="mdi-account" :title="personName(repairData.customer)" subtitle="Kunde" />
                <v-list-item
                  v-if="repairData.customer?.telefon"
                  prepend-icon="mdi-phone"
                  :href="`tel:${repairData.customer.telefon}`"
                  :title="repairData.customer.telefon"
                  subtitle="Telefon"
                />
                <v-list-item
                  v-if="repairData.customer?.email"
                  prepend-icon="mdi-email"
                  :href="`mailto:${repairData.customer.email}`"
                  :title="repairData.customer.email"
                  subtitle="E-Mail"
                />
              </v-list>
            </v-col>
            <v-col cols="12" sm="6">
              <v-list density="compact" class="py-0" bg-color="transparent">
                <v-list-item
                  v-if="repairData.user"
                  prepend-icon="mdi-account-wrench"
                  :title="personName(repairData.user)"
                  subtitle="Reparateur"
                />
                <v-list-item
                  v-if="durationLabel"
                  prepend-icon="mdi-timer-outline"
                  :title="durationLabel.value"
                  :subtitle="durationLabel.label"
                />
                <v-list-item
                  v-if="repairData.status_detail"
                  prepend-icon="mdi-flag-outline"
                  :title="repairData.status_detail"
                  subtitle="Abschlussgrund"
                />
              </v-list>
            </v-col>
          </v-row>

      <v-alert
        v-if="isClosed && repairData.reparatur_besch"
        :type="repairData.status === 'Repariert' ? 'success' : 'warning'"
        variant="tonal"
        :title="repairData.status === 'Repariert' ? 'Reparaturergebnis' : 'Begründung'"
        :text="repairData.reparatur_besch"
        class="mt-3"
      />

      <template v-if="vdeTests && vdeTests.length > 0">
        <div class="text-title-small text-medium-emphasis mt-4 mb-2">Letzter VDE-Test</div>
        <v-alert
          v-for="test in vdeTests"
          :key="test.id"
          :type="test.gesamtergebnis === true ? 'success' : 'error'"
          variant="tonal"
          density="compact"
          class="mb-2"
        >
          <strong>{{ test.gesamtergebnis === true ? 'Bestanden' : 'Nicht bestanden' }}</strong>
          <span class="ml-2 text-body-small">{{ formatDateTime(test.created_at) }}</span>
          <div class="text-body-small mt-1">
            Prüfer: {{ test.prufer }} · Gerät: {{ test.pruefgeraet_name || '–' }}
          </div>
          <div v-if="test.bemerkungen" class="text-body-small mt-1">{{ test.bemerkungen }}</div>
        </v-alert>
      </template>
        </v-card-text>
      </div>
    </div>
  </v-card>

  <!-- Device photo (exactly one; it replaces the previous one) -->
  <ResponsiveDialog v-model="photoDialog" max-width="560" persistent>
    <v-card title="Foto des Geräts">
      <v-card-text>
        <DevicePhotoCapture
          v-model="newPhoto"
          :active="photoDialog"
          :category="repairData.repair_type?.name"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" :disabled="savingPhoto" @click="photoDialog = false">Abbrechen</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          :disabled="!newPhoto"
          :loading="savingPhoto"
          @click="savePhoto"
        >
          Speichern
        </v-btn>
      </v-card-actions>
    </v-card>
  </ResponsiveDialog>

  <!-- Edit basic fields dialog -->
  <ResponsiveDialog v-model="editDialog" max-width="500" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-pencil</v-icon>
        Reparatur bearbeiten
      </v-card-title>
      <v-card-text>
        <DateField v-model="editForm.datum" label="Angenommen am" />
        <v-select
v-model="editForm.repair_type_id" :items="repairTypes" item-value="id" item-title="name"
          label="Kategorie" class="mt-3"></v-select>
        <v-text-field
v-model="editForm.geraet_art" label="Geräte Art / Bezeichnung"
          class="mt-3"></v-text-field>
        <v-textarea
v-model="editForm.defekt_besch" label="Beschreibung des Defekts" rows="3"
          class="mt-3"></v-textarea>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="editDialog = false">Abbrechen</v-btn>
        <v-btn color="primary" variant="elevated" :loading="saving" @click="saveEdit">
          Speichern
        </v-btn>
      </v-card-actions>
    </v-card>
  </ResponsiveDialog>
</template>

<script setup lang="ts">
import ResponsiveDialog from '@/components/ResponsiveDialog.vue'
import { api } from '@/api/client'
import { ref, computed } from 'vue'
import type { Repair, VdeTestResponse } from '@/api/types'
import { personName } from '@/utils/person'
import DateField from '@/components/ui/DateField.vue'
import RepairNumber from '@/components/ui/RepairNumber.vue'
import DevicePhoto from '@/components/ui/DevicePhoto.vue'
import DevicePhotoCapture from '@/components/DevicePhotoCapture.vue'
import { asFormData } from '@/api/client'
import RepairMeta from '@/components/ui/RepairMeta.vue'
import { formatDate, formatDateTime } from '@/utils/date'
import { useToast } from '@/composables/useToast'
import { errorMessage } from '@/utils/errors'

// A repair being created: no ids yet, and unselected fields are null.
type RepairDraft = Omit<Partial<Repair>, 'customer' | 'repair_type_id' | 'repair_type'> & {
  customer?: Partial<NonNullable<Repair['customer']>> | null
  repair_type_id?: number | null
  repair_type?: Partial<NonNullable<Repair['repair_type']>> | null
}

interface Props {
  repairData: RepairDraft
  vdeTests?: VdeTestResponse[]
  loggedDuration?: number
  /** Device photo; without one the category placeholder is shown. */
  photoUrl?: string | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  /** A new device photo was saved; the owner should reload the attachments. */
  photoChanged: []
  updated: [
    fields: {
      datum: string
      repair_type_id: number | undefined
      geraet_art: string
      defekt_besch: string
    },
  ]
}>()

const toast = useToast()

const isClosed = computed(
  () => props.repairData.status === 'Repariert' || props.repairData.status === 'Nicht Repariert'
)
const durationLabel = computed(() => {
  if (props.repairData.reparatur_dauer) {
    return { label: 'Reparaturdauer', value: `${props.repairData.reparatur_dauer} Min.` }
  }
  if (props.loggedDuration) {
    return { label: 'Protokollierte Zeit', value: `${props.loggedDuration} Min.` }
  }
  return null
})

// ── Device photo dialog ─────────────────────────────────────────────
const photoDialog = ref(false)
const newPhoto = ref<File | null>(null)
const savingPhoto = ref(false)

function openPhotoDialog() {
  newPhoto.value = null
  photoDialog.value = true
}

async function savePhoto() {
  if (!props.repairData.id || !newPhoto.value) return
  savingPhoto.value = true
  try {
    await api.uploadRepairAttachments(
      { repairId: props.repairData.id },
      asFormData({ files: [newPhoto.value], attachment_type: 'device_photo' })
    )
    photoDialog.value = false
    toast.success('Foto gespeichert')
    emit('photoChanged')
  } catch (err) {
    toast.error('Fehler beim Speichern des Fotos: ' + errorMessage(err, 'Unbekannter Fehler'))
  } finally {
    savingPhoto.value = false
  }
}

// ── Edit dialog ───────────────────────────────────────────────────────
const editDialog = ref(false)
const saving = ref(false)
const repairTypes = ref<Array<{ id: number; name: string }>>([])
const editForm = ref({ datum: '', repair_type_id: null as number | null, geraet_art: '', defekt_besch: '' })

function openEditDialog() {
  editForm.value = {
    datum: props.repairData.datum ? props.repairData.datum.slice(0, 10) : '',
    repair_type_id: props.repairData.repair_type_id ?? null,
    geraet_art: props.repairData.geraet_art ?? '',
    defekt_besch: props.repairData.defekt_besch ?? '',
  }
  if (repairTypes.value.length === 0) {
    api.getDropdownConfig()
      .then((c) => {
        if (c.repair_type) repairTypes.value = c.repair_type
      })
      .catch(() => { })
  }
  editDialog.value = true
}

async function saveEdit() {
  if (!props.repairData.id) return
  saving.value = true
  try {
    await api.updateRepair({ id: props.repairData.id }, {
      datum: editForm.value.datum,
      repair_type_id: editForm.value.repair_type_id ?? undefined,
      geraet_art: editForm.value.geraet_art,
      defekt_besch: editForm.value.defekt_besch,
    })
    emit('updated', {
      ...editForm.value,
      repair_type_id: editForm.value.repair_type_id ?? undefined,
    })
    editDialog.value = false
  } catch (err) {
    toast.error('Fehler beim Speichern: ' + errorMessage(err, 'Unbekannter Fehler'))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
/* Photo beside the details when the card is wide enough, above them otherwise */
.summary {
  container-type: inline-size;
}

.summary-layout {
  display: grid;
  grid-template-columns: 1fr;
}

.summary-photo {
  position: relative;
  height: 180px;
  padding: 16px 16px 0;
}

.photo-action {
  position: absolute;
  right: 24px;
  bottom: 8px;
}

@container (min-width: 640px) {
  .summary-layout {
    grid-template-columns: 240px 1fr;
  }

  .summary-photo {
    height: auto;
    min-height: 220px;
    padding: 16px 0 16px 16px;
  }

  .photo-action {
    right: 8px;
    bottom: 24px;
  }
}
</style>
