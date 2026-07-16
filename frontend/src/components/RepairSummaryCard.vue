<template>
  <v-card class="mb-4">
    <v-card-title class="text-h5">
      <div class="d-flex justify-space-between align-center">
        <span>{{ repairData.geraet_art }}</span>
        <div class="d-flex align-center gap-2">
          <v-btn v-if="repairData.id" icon="mdi-pencil" size="small" variant="text" @click="openEditDialog"></v-btn>
          <v-chip :color="getStatusColor(repairData.status ?? '')" variant="tonal"
            :prepend-icon="getStatusIcon(repairData.status ?? '')">
            {{ repairData.status }}
          </v-chip>
        </div>
      </div>
    </v-card-title>
    <v-card-text>
      <v-row>
        <v-col cols="12">
          <div class="text-subtitle-2 text-grey-darken-1">Beschreibung des Defekts</div>
          <div>{{ repairData.defekt_besch }}</div>
        </v-col>
        <v-col cols="6">
          <div class="text-subtitle-2 text-grey-darken-1">Kategorie</div>
          <div>{{ repairData.repair_type?.name }}</div>
        </v-col>
        <v-col cols="6">
          <div class="text-subtitle-2 text-grey-darken-1">Geräte Art / Bezeichnung</div>
          <div>{{ repairData.geraet_art }}</div>
        </v-col>
        <v-col cols="6">
          <div class="text-subtitle-2 text-grey-darken-1">Datum</div>
          <div>{{ formatDate(repairData.datum) }}</div>
        </v-col>
        <v-col cols="6">
          <div class="text-subtitle-2 text-grey-darken-1">Name</div>
          <div>{{ repairData.customer?.vorname }} {{ repairData.customer?.nachname }}</div>
        </v-col>
        <v-col cols="6">
          <div class="text-subtitle-2 text-grey-darken-1">Telefon</div>
          <div>{{ repairData.customer?.telefon || '-' }}</div>
        </v-col>
        <v-col cols="6">
          <div class="text-subtitle-2 text-grey-darken-1">Email</div>
          <div>{{ repairData.customer?.email || '-' }}</div>
        </v-col>
        <v-col v-if="repairData.reparatur_dauer" cols="6">
          <div class="text-subtitle-2 text-grey-darken-1">Reparaturdauer</div>
          <div>{{ repairData.reparatur_dauer }} Min.</div>
        </v-col>
        <v-col v-else-if="loggedDuration > 0" cols="6">
          <div class="text-subtitle-2 text-grey-darken-1">Protokollierte Zeit</div>
          <div>{{ loggedDuration }} Min.</div>
        </v-col>
        <template v-if="repairData.status === 'Repariert' || repairData.status === 'Nicht Repariert'">
          <v-col cols="12">
            <v-divider class="my-3"></v-divider>
          </v-col>
          <v-col v-if="repairData.reparatur_besch" cols="6">
            <div class="text-subtitle-2 text-grey-darken-1">
              {{ repairData.status === 'Repariert' ? 'Reparaturergebnis' : 'Begründung' }}
            </div>
            <div>{{ repairData.reparatur_besch }}</div>
          </v-col>
          <v-col v-if="repairData.status_detail" cols="6">
            <div class="text-subtitle-2 text-grey-darken-1">Abschlussgrund</div>
            <div>{{ repairData.status_detail }}</div>
          </v-col>

        </template>
        <v-col v-if="vdeTests && vdeTests.length > 0" cols="12">
          <v-divider class="my-3"></v-divider>
          <div class="text-subtitle-2 text-grey-darken-1 mb-2">Letztes Test Ergebnis nach VDE</div>
          <v-alert v-for="test in vdeTests" :key="test.id" :type="test.gesamtergebnis === true ? 'success' : 'error'"
            variant="tonal" density="compact" class="mb-2">
            <div class="d-flex align-center">
              <div class="flex-grow-1">
                <strong>{{
                  test.gesamtergebnis === true ? '✓ Bestanden' : '⚠ Nicht bestanden'
                  }}</strong>
                <span class="ml-2 text-caption">{{ formatDateTime(test.created_at) }}</span>
                <div class="text-caption mt-1">
                  Prüfer: {{ test.prufer }} | Gerät: {{ test.pruefgeraet_name || '-' }}
                </div>
                <div v-if="test.bemerkungen" class="text-caption mt-1">
                  {{ test.bemerkungen }}
                </div>
              </div>
            </div>
          </v-alert>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>

  <!-- Edit basic fields dialog -->
  <v-dialog v-model="editDialog" max-width="500" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-pencil</v-icon>
        Reparatur bearbeiten
      </v-card-title>
      <v-card-text>
        <v-text-field v-model="editForm.datum" label="Datum" type="date" density="comfortable"
          variant="outlined"></v-text-field>
        <v-select v-model="editForm.repair_type_id" :items="repairTypes" item-value="id" item-title="name"
          label="Kategorie" density="comfortable" variant="outlined" class="mt-3"></v-select>
        <v-text-field v-model="editForm.geraet_art" label="Geräte Art / Bezeichnung" density="comfortable"
          variant="outlined" class="mt-3"></v-text-field>
        <v-textarea v-model="editForm.defekt_besch" label="Beschreibung des Defekts" rows="3" density="comfortable"
          variant="outlined" class="mt-3"></v-textarea>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="editDialog = false">Abbrechen</v-btn>
        <v-btn color="primary" variant="elevated" :loading="saving" @click="saveEdit">
          Speichern
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Repair, VdeTestResponse } from '@/api/types'
import { getRepairStatusColor, getRepairStatusIcon } from '@/stores/repairStore'
import { RepairsService } from '@/api/services/RepairsService'
import { ConfigService } from '@/api/services/ConfigService'

interface Props {
  repairData: Partial<Repair>
  vdeTests?: VdeTestResponse[]
  loggedDuration?: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  updated: [
    fields: { datum: string; repair_type_id: number | undefined; geraet_art: string; defekt_besch: string }
  ]
}>()

const getStatusColor = getRepairStatusColor
const getStatusIcon = getRepairStatusIcon

const loggedDuration = computed(() => props.loggedDuration ?? 0)

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
    ConfigService.getDropdownConfig()
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
    await RepairsService.updateRepair(props.repairData.id, {
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
  } finally {
    saving.value = false
  }
}

function formatDate(dateString: string | undefined) {
  if (!dateString) return ''
  const [year, month, day] = dateString.slice(0, 10).split('-')
  return `${day}.${month}.${year}`
}

function formatDateTime(dateTimeString: string | undefined) {
  if (!dateTimeString) return ''
  const date = new Date(dateTimeString)
  return date.toLocaleString('de-DE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>
