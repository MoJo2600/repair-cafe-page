<template>
  <v-container class="d-flex justify-center align-center" style="min-height: 80vh;">
    <v-card max-width="1000px" width="100%">
      <!-- <v-card-title v-if="formData" class="text-h5">{{ formData.geraet_art }}</v-card-title> -->

      <v-card-text v-if="loading">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
        <span class="ml-3">Lade Reparaturdaten...</span>
      </v-card-text>

      <v-card-text v-else-if="error">
        <v-alert type="error">{{ error }}</v-alert>
      </v-card-text>

      <v-card-text v-else-if="repairRecord">
        <RepairSummaryCard :repair-data="repairRecord" :vde-tests="summaryVdeTests" />

        <v-alert v-if="repairRecord.user" type="info" variant="tonal" class="mb-4">
          <div class="d-flex align-center justify-space-between flex-wrap ga-2">
            <div>
              <strong>Aktuell zustaendig:</strong> {{ repairRecord.user.vorname }} {{ repairRecord.user.nachname }}
            </div>
            <v-chip size="small" :color="selectedRepairStatus === 'In Bearbeitung' ? 'info' : 'default'">
              {{ selectedRepairStatus === 'In Bearbeitung' ? 'Arbeitet gerade an der Reparatur' : 'Zuletzt zugewiesen'
              }}
            </v-chip>
          </div>
        </v-alert>

        <!-- Status Quick-Select Section -->
        <div class="mt-6">
          <h3 class="text-h6 mb-3">Status</h3>
          <v-btn-group divided variant="outlined">
            <v-btn v-for="status in repairStatusOptions" :key="status" :color="getStatusColor(status)"
              :disabled="isStatusChangeDisabled(status)"
              :variant="selectedRepairStatus === status ? 'flat' : 'outlined'" :prepend-icon="getStatusIcon(status)"
              class="pr-2" @click="handleCloseRepair(status)">
              {{ status }}
            </v-btn>
          </v-btn-group>
        </div>

        <!-- Repair Logs Section -->
        <div class="mt-6">
          <h3 class="text-h6 mb-4">Reparatur Logeinträge</h3>

          <!-- Unified Activity Thread -->
          <v-card variant="outlined" class="mb-4" v-if="threadEntries.length > 0">
            <v-list lines="two" class="py-0">
              <v-list-item v-for="entry in threadEntries" :key="entry.uniqueKey" class="py-3">
                <template #prepend>
                  <v-avatar size="28"
                    :color="entry.type === 'repair' ? 'primary'
                      : entry.type === 'status_change' ? 'warning'
                      : entry.vdePassed ? 'success' : 'error'"
                    variant="tonal">
                    <v-icon size="16">{{
                      entry.type === 'repair' ? 'mdi-wrench'
                      : entry.type === 'status_change' ? 'mdi-swap-horizontal'
                      : entry.vdePassed ? 'mdi-flash' : 'mdi-flash-off'
                    }}</v-icon>
                  </v-avatar>
                </template>

                <v-list-item-title class="d-flex align-center justify-space-between flex-wrap ga-2">
                  <div class="d-flex align-center ga-2 flex-wrap">
                    <strong>{{ entry.person }}</strong>
                    <!-- <v-chip size="x-small"
                      :color="entry.type === 'repair' ? 'primary' : entry.type === 'status_change' ? 'warning' : 'success'"
                      variant="tonal">
                      {{ entry.type === 'repair' ? 'Reparatur-Log' : entry.type === 'status_change' ? 'Statusänderung' : 'VDE-Test' }}
                    </v-chip> -->
                    <v-chip v-if="entry.type === 'repair' && (logAttachments[entry.id]?.length ?? 0) > 0" size="x-small"
                      color="grey-darken-1" variant="tonal">
                      <v-icon size="12" start>mdi-paperclip</v-icon>
                      {{ logAttachments[entry.id].length }}
                    </v-chip>
                  </div>
                  <span class="text-caption text-grey-darken-1">{{ formatDateTime(entry.created_at) }}</span>
                </v-list-item-title>

                <!-- Status change entry: show from → to chips -->
                <template v-if="entry.type === 'status_change'">
                  <div class="d-flex align-center ga-1 flex-wrap pt-1">
                    <v-chip size="x-small" variant="tonal" :color="getStatusColor(entry.status_from ?? '')">
                      {{ entry.status_from || '?' }}
                    </v-chip>
                    <v-icon size="14" color="grey">mdi-arrow-right</v-icon>
                    <v-chip size="x-small" variant="tonal" :color="getStatusColor(entry.status_to ?? '')">
                      {{ entry.status_to || '?' }}
                    </v-chip>
                  </div>
                </template>

                <!-- Work log entry with optional status transition -->
                <template v-else-if="entry.type === 'repair'">
                  <v-list-item-subtitle v-if="entry.description" class="pt-1 text-body-2 text-high-emphasis" style="white-space: normal;">
                    {{ entry.description }}
                  </v-list-item-subtitle>
                  <div class="d-flex align-center ga-2 flex-wrap mt-1">
                    <span class="text-caption text-grey-darken-1">Dauer: {{ entry.duration }} Min.</span>
                    <template v-if="entry.status_from || entry.status_to">
                      <v-chip size="x-small" variant="tonal" :color="getStatusColor(entry.status_from ?? '')">
                        {{ entry.status_from || '?' }}
                      </v-chip>
                      <v-icon size="14" color="grey">mdi-arrow-right</v-icon>
                      <v-chip size="x-small" variant="flat" :color="getStatusColor(entry.status_to ?? '')">
                        {{ entry.status_to || '?' }}
                      </v-chip>
                    </template>
                  </div>
                  <div class="mt-1 d-flex ga-1">
                    <v-btn size="x-small" variant="text" prepend-icon="mdi-pencil" @click="openEditLogDialog(entry.id)">
                      Bearbeiten
                    </v-btn>
                    <v-btn size="x-small" variant="text" color="error" prepend-icon="mdi-delete" @click="openDeleteLogDialog(entry.id)">
                      Löschen
                    </v-btn>
                  </div>
                </template>

                <template v-else-if="entry.type === 'vde'">
                  <v-list-item-subtitle class="pt-1 text-body-2 text-high-emphasis" style="white-space: normal;">
                    {{ entry.description }}
                  </v-list-item-subtitle>
                  <div class="mt-1">
                    <v-btn size="x-small" variant="text" prepend-icon="mdi-file-pdf-box" color="error"
                      @click="downloadVdePdf(entry.id)">
                      PDF herunterladen
                    </v-btn>
                  </div>
                </template>
              </v-list-item>
            </v-list>
          </v-card>

          <v-alert v-else type="info" variant="tonal" class="mb-4">
            Noch keine Logeinträge vorhanden.
          </v-alert>

          <v-row>
            <v-col cols="12" sm="auto">
              <!-- Button to Add New Log Entry -->
              <v-btn color="primary" prepend-icon="mdi-plus" @click="openLogDialog" class="mb-4" block>
                Neuer Logeintrag
              </v-btn>
            </v-col>

            <v-col cols="12" sm="auto">
              <v-btn color="primary" prepend-icon="mdi-flash" @click="openVdeDialog" class="mb-4" block>
                VDE Test protokollieren
              </v-btn>
            </v-col>

            <v-col v-if="labelPrinterEnabled" cols="12" sm="auto">
              <v-btn color="secondary" prepend-icon="mdi-printer" @click="printLabel" :loading="printingLabel" class="mb-4" block>
                Label drucken
              </v-btn>
            </v-col>
          </v-row>

        </div>

        <!-- Attachments Section -->
        <div class="mt-6">
          <h3 class="text-h6 mb-3">Anhänge</h3>
          <v-card variant="outlined">
            <v-list lines="one" class="py-0">
              <v-list-item prepend-icon="mdi-file-pdf-box" :href="disclaimerUrl" target="_blank"
                :disabled="!disclaimerExists" :subtitle="disclaimerExists ? 'PDF herunterladen' : 'Nicht vorhanden'">
                <v-list-item-title>Haftungsausschluss</v-list-item-title>
                <template #append>
                  <v-btn v-if="disclaimerExists" icon="mdi-download" variant="text" size="small" :href="disclaimerUrl"
                    :download="`haftungsausschluss_${repairRecord?.id}.pdf`" @click.stop></v-btn>
                  <v-icon v-else color="grey" size="small">mdi-minus</v-icon>
                </template>
              </v-list-item>

              <template v-for="item in allLogAttachmentItems" :key="item.url">
                <v-divider></v-divider>
                <v-list-item :prepend-icon="getAttachmentIcon(item.content_type)" :href="item.url" target="_blank"
                  :subtitle="item.logLabel">
                  <v-list-item-title>{{ item.name }}</v-list-item-title>
                  <template #append>
                    <v-btn :icon="item.content_type.startsWith('image/') ? 'mdi-open-in-new' : 'mdi-download'"
                      variant="text" size="small" :href="item.url"
                      :download="item.content_type.startsWith('image/') ? undefined : item.name"
                      :target="item.content_type.startsWith('image/') ? '_blank' : undefined" @click.stop></v-btn>
                  </template>
                </v-list-item>
              </template>

              <v-list-item v-if="!disclaimerExists && allLogAttachmentItems.length === 0"
                prepend-icon="mdi-information-outline" subtitle="Noch keine Anhänge vorhanden">
              </v-list-item>
            </v-list>
          </v-card>
        </div>
      </v-card-text>

      <v-card-actions v-if="!loading && !error" class="flex-wrap ga-2">
        <v-btn @click="goBack">
          <v-icon start>mdi-arrow-left</v-icon>
          Zurück
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- Success Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.message }}
    </v-snackbar>

    <!-- Log Entry Dialog -->
    <v-dialog v-model="logDialog" max-width="600px">
      <v-card>
        <v-card-title class="text-h5">Neue Notiz</v-card-title>

        <v-card-text>
          <v-form ref="logForm" v-model="logFormValid">
            <v-select v-model="newLog.user_id" :items="userStore.users" item-value="id" label="Reparateur" required
              :loading="userStore.loading" :rules="[v => !!v || 'Reparateur ist erforderlich']">
              <template #item="{ props, item }">
                <v-list-item v-bind="props" :title="`${item.raw.vorname} ${item.raw.nachname}`"
                  :subtitle="item.raw.email"></v-list-item>
              </template>
              <template #selection="{ item }">
                {{ item.raw.vorname }} {{ item.raw.nachname }}
              </template>
            </v-select>

            <v-textarea v-model="newLog.reparatur_besch" label="Was wurde gemacht?" rows="3" required
              :rules="[v => !!v || 'Beschreibung ist erforderlich']">
            </v-textarea>

            <v-text-field v-model.number="newLog.reparatur_dauer" label="Dauer in Minuten (Optional)" type="number">
            </v-text-field>

            <v-divider class="my-4"></v-divider>
            <div class="text-subtitle-2 mb-3">Fotos &amp; Dateien (optional)</div>

            <!-- Camera preview -->
            <div v-if="logCameraActive" class="mb-3">
              <video ref="logVideoElement" autoplay playsinline
                style="width: 100%; max-height: 200px; background: #000; border-radius: 4px;"></video>
              <canvas ref="logPhotoCanvas" style="display: none;"></canvas>
            </div>

            <div class="d-flex ga-2 flex-wrap mb-3">
              <v-btn v-if="!logCameraActive" variant="outlined" size="small" prepend-icon="mdi-camera"
                :disabled="logCameraPermissionDenied" @click="startLogCamera">
                Foto aufnehmen
              </v-btn>
              <v-btn v-if="logCameraActive" color="success" size="small" prepend-icon="mdi-camera"
                @click="captureLogPhoto">
                Aufnehmen
              </v-btn>
              <v-btn v-if="logCameraActive" variant="outlined" size="small" prepend-icon="mdi-close"
                @click="stopLogCamera">
                Stop
              </v-btn>
            </div>

            <v-alert v-if="logCameraPermissionDenied" type="error" density="compact" class="mb-3">
              Kamerazugriff verweigert.
            </v-alert>

            <!-- Photo thumbnails -->
            <div v-if="pendingPhotos.length > 0" class="d-flex flex-wrap ga-2 mb-3">
              <div v-for="(photo, i) in pendingPhotos" :key="i" style="position: relative; width: 72px;">
                <v-img :src="photo" width="72" height="72" cover
                  style="border-radius: 4px; border: 1px solid #ccc;"></v-img>
                <v-btn icon="mdi-close" size="x-small" color="error" variant="flat"
                  style="position: absolute; top: -6px; right: -6px;" @click="removePhoto(i)"></v-btn>
              </div>
            </div>

            <!-- File upload -->
            <v-file-input v-model="pendingFiles" label="Dateien hochladen (optional)" multiple
              prepend-icon="mdi-paperclip" variant="outlined" density="compact" hide-details
              accept="*/*"></v-file-input>

          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-btn @click="closeLogDialog">Abbrechen</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="addLogEntry" :disabled="!logFormValid" :loading="saving">
            Speichern
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <ReparateurRequiredDialog v-model="transitionDialog" v-model:userId="transitionUserId" title="Reparatur starten"
      message="Für den Wechsel von 'Offen' zu 'In Bearbeitung' muss ein Reparateur angegeben werden."
      confirm-text="Weiter" @confirm="confirmTransitionWithReparateur" />

    <RepairCompletionDialog v-model="completionDialog" v-model:description="completionData.description"
      v-model:duration="completionData.duration" v-model:needs-vde-test="completionData.needsVdeTest"
      :suggested-duration="suggestedRepairDuration" :has-any-vde-test="hasVdeTest"
      :last-vde-test-passed="lastVdeTestPassed" :loading="saving" @confirm="confirmRepairCompletion" />

    <RepairNotRepairableDialog v-model="notRepairableDialog" :loading="savingStatus" @confirm="confirmNotRepairable" />

    <AbbruchSignatureDialog v-model="abbruchSignatureDialog" :loading="savingStatus"
      @confirm="confirmAbbruchSignature" />

    <VdeTestDialog v-model="vdeDialog" :saving="saving" :repair-id="repairRecord?.id"
      :selected-repair-status="selectedRepairStatus" :required-for-status="vdeDialogMode === 'close'"
      :confirm-text="vdeDialogMode === 'close' ? 'VDE speichern & Reparatur abschliessen' : 'VDE speichern'"
      :initial-prufer-user-id="vdeInitialPruferUserId" :users="userStore.users" :pruefgeraete="pruefgeraete"
      @submit="handleVdeSubmit" />

    <!-- Delete Log Confirmation Dialog -->
    <v-dialog v-model="deleteLogDialog" max-width="400px">
      <v-card>
        <v-card-title class="text-h5">Logeintrag löschen</v-card-title>
        <v-card-text>Soll dieser Logeintrag wirklich gelöscht werden? Diese Aktion kann nicht rückgängig gemacht werden.</v-card-text>
        <v-card-actions>
          <v-btn @click="deleteLogDialog = false">Abbrechen</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="error" @click="confirmDeleteLog" :loading="deleteLogLoading">
            Löschen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Edit Log Entry Dialog -->
    <v-dialog v-model="editLogDialog" max-width="600px">
      <v-card>
        <v-card-title class="text-h5">Logeintrag bearbeiten</v-card-title>
        <v-card-text>
          <v-form ref="editLogForm" v-model="editLogFormValid">
            <v-select v-model="editLog.user_id" :items="userStore.users" item-value="id" label="Reparateur" required
              :loading="userStore.loading" :rules="[v => !!v || 'Reparateur ist erforderlich']">
              <template #item="{ props, item }">
                <v-list-item v-bind="props" :title="`${item.raw.vorname} ${item.raw.nachname}`"
                  :subtitle="item.raw.email"></v-list-item>
              </template>
              <template #selection="{ item }">
                {{ item.raw.vorname }} {{ item.raw.nachname }}
              </template>
            </v-select>
            <v-textarea v-model="editLog.reparatur_besch" label="Was wurde gemacht?" rows="3" required
              :rules="[v => !!v || 'Beschreibung ist erforderlich']">
            </v-textarea>
            <v-text-field v-model.number="editLog.reparatur_dauer" label="Dauer in Minuten (Optional)" type="number">
            </v-text-field>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-btn @click="editLogDialog = false">Abbrechen</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="saveEditLog" :disabled="!editLogFormValid" :loading="editLogSaving">
            Speichern
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import confetti from 'canvas-confetti'
import { RepairsService } from '@/api/services/RepairsService'
import {
  useRepairStore,
  normalizeRepairStatus,
  REPAIR_STATUSES,
  getRepairStatusColor,
  getRepairStatusIcon,
  getRepairStatusDetailOptions,
  calculateRepairDurationFromLogs,
  requiresCompletionDetailsForTransition,
  requiresFailureDetailsForTransition
} from '@/stores/repairStore'
import { RepairLogsService } from '@/api/services/RepairLogsService'
import { VdeTestsService, type VdeTestCreate } from '@/api/services/VdeTestsService'
import { ConfigService } from '@/api/services/ConfigService'
import type { Repair, RepairLog, VdeTestResponse, PruefgeraetResponse } from '@/api/types'
import type { VdeFormData } from '@/components/VdeTestDialog.vue'
import RepairSummaryCard from '@/components/RepairSummaryCard.vue'
import ReparateurRequiredDialog from '@/components/ReparateurRequiredDialog.vue'
import RepairCompletionDialog from '@/components/RepairCompletionDialog.vue'
import RepairNotRepairableDialog from '@/components/RepairNotRepairableDialog.vue'
import AbbruchSignatureDialog from '@/components/AbbruchSignatureDialog.vue'
import VdeTestDialog from '@/components/VdeTestDialog.vue'
import { useRepairThread } from '@/composables/useRepairThread'
import { useUserStore } from '@/stores/userStore'

interface NewLogFormData {
  user_id: number | null
  reparatur_dauer: number | null
  reparatur_besch: string
}

const router = useRouter()
const route = useRoute()
const repairStore = useRepairStore()
const userStore = useUserStore()

const loading = ref(true)
const error = ref('')
const saving = ref(false)
const savingStatus = ref(false)
const logFormValid = ref(false)
const logForm = ref<{ validate: () => Promise<{ valid: boolean }>; resetValidation?: () => void } | null>(null)

const repairRecord = ref<Repair | null>(null)
const repairLogs = ref<RepairLog[]>([])
const vdeTests = ref<VdeTestResponse[]>([])
const pruefgeraete = ref<PruefgeraetResponse[]>([])
const disclaimerExists = ref(false)
const disclaimerUrl = computed(() =>
  repairRecord.value?.id ? `/api/repairs/${repairRecord.value.id}/disclaimer` : ''
)

// Log attachments
interface AttachmentInfo { name: string; url: string; content_type: string; size: number }
const logAttachments = ref<Record<number, AttachmentInfo[]>>({})

// Camera state for log dialog
const logVideoElement = ref<HTMLVideoElement | null>(null)
const logPhotoCanvas = ref<HTMLCanvasElement | null>(null)
let logCameraStream: MediaStream | null = null
const logCameraActive = ref(false)
const logCameraPermissionDenied = ref(false)

// Pending attachments for the new log entry
const pendingPhotos = ref<string[]>([])
const pendingFiles = ref<File[]>([])

// Repair status selection
const selectedRepairStatus = ref<string>('')
const selectedStatusDetail = ref<string>('')
const repairStatusOptions = [...REPAIR_STATUSES]
const currentRepairStatus = computed(() => normalizeRepairStatus(repairRecord.value?.status))

watch(selectedRepairStatus, (newStatus) => {
  const allowedDetails = getRepairStatusDetailOptions(newStatus)
  if (selectedStatusDetail.value && !allowedDetails.includes(selectedStatusDetail.value)) {
    selectedStatusDetail.value = ''
  }
})

const { latestVdeTests, lastVdeTestPassed, threadEntries } = useRepairThread(repairLogs, vdeTests)

const summaryVdeTests = computed(() => latestVdeTests.value)

// Check if at least one VDE test exists
const hasVdeTest = computed(() => vdeTests.value.length > 0)
const suggestedRepairDuration = computed(() => calculateRepairDurationFromLogs(repairLogs.value))

// Flatten all log attachments with context for the attachments list
const allLogAttachmentItems = computed(() => {
  const items: (AttachmentInfo & { logLabel: string })[] = []
  for (const log of repairLogs.value) {
    const atts = logAttachments.value[log.id] || []
    const personName = log.user ? `${log.user.vorname} ${log.user.nachname}` : String(log.user_id ?? '?')
    for (const att of atts) {
      items.push({ ...att, logLabel: `${personName} · ${formatDateTime(log.created_at)}` })
    }
  }
  return items
})

function getAttachmentIcon(contentType: string): string {
  if (contentType.startsWith('image/')) return 'mdi-image'
  if (contentType === 'application/pdf') return 'mdi-file-pdf-box'
  return 'mdi-file-outline'
}

// Check if VDE test is required for the selected status
const vdeTestRequired = computed(() => {
  return selectedRepairStatus.value === 'Repariert' || selectedStatusDetail.value === 'Abbruch'
})

const newLog = ref<NewLogFormData>({
  user_id: null,
  reparatur_dauer: null,
  reparatur_besch: ''
})

const logDialog = ref(false)
const vdeDialog = ref(false)
const vdeDialogMode = ref<'manual' | 'close'>('manual')
const vdeInitialPruferUserId = ref<number | null>(null)

// Delete log dialog state
const deleteLogDialog = ref(false)
const deleteLogLoading = ref(false)
const deletingLogId = ref<number | null>(null)

function openDeleteLogDialog(logId: number) {
  deletingLogId.value = logId
  deleteLogDialog.value = true
}

async function confirmDeleteLog() {
  if (!repairRecord.value || !deletingLogId.value) return
  deleteLogLoading.value = true
  try {
    const response = await RepairLogsService.deleteRepairLog(repairRecord.value.id, deletingLogId.value)
    if (response.reply === 'done') {
      showSnackbar('Logeintrag gelöscht')
      deleteLogDialog.value = false
      await loadRepairLogs()
    } else {
      showSnackbar(response.error || 'Fehler beim Löschen', 'error')
    }
  } catch (err) {
    showSnackbar('Fehler beim Löschen: ' + (err as Error).message, 'error')
  } finally {
    deleteLogLoading.value = false
    deletingLogId.value = null
  }
}

// Edit log dialog state
const editLogDialog = ref(false)
const editLogFormValid = ref(false)
const editLogSaving = ref(false)
const editingLogId = ref<number | null>(null)
const editLogForm = ref<{ validate: () => Promise<{ valid: boolean }>; resetValidation?: () => void } | null>(null)
const editLog = ref({ user_id: null as number | null, reparatur_besch: '', reparatur_dauer: 0 as number | null })
const transitionDialog = ref(false)
const completionDialog = ref(false)
const pendingTransitionStatus = ref<string>('')
const transitionUserId = ref<number | null>(null)
const completionData = ref({
  description: '',
  duration: null as number | null,
  needsVdeTest: false
})

const notRepairableDialog = ref(false)
const notRepairableData = ref({
  description: '',
  statusDetail: ''
})

const abbruchSignatureDialog = ref(false)
const pendingAbbruchPayload = ref<{ description: string; statusDetail: string } | null>(null)

const labelPrinterEnabled = ref(false)
const printingLabel = ref(false)

const snackbar = ref({
  show: false,
  message: '',
  color: 'success'
})

function showSnackbar(message: string, color: string = 'success') {
  snackbar.value = {
    show: true,
    message,
    color
  }
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString)
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${day}.${month}.${year} ${hours}:${minutes}`
}

async function loadRepairLogs() {
  if (!repairRecord.value?.id) return

  try {
    const response = await RepairLogsService.listRepairLogs(repairRecord.value.id)
    if (response.data) {
      repairLogs.value = response.data
    }
  } catch (err) {
    console.error('Error loading repair logs:', err)
  }
}

async function loadVdeTests() {
  if (!repairRecord.value?.id) return

  try {
    const response = await VdeTestsService.listVdeTests(repairRecord.value.id)
    if (response.reply === 'done' && response.data) {
      vdeTests.value = response.data
    }
  } catch (err) {
    console.error('Error loading VDE tests:', err)
  }
}

async function loadPruefgeraete() {
  try {
    const devices = await ConfigService.getPruefgeraete()
    pruefgeraete.value = devices
  } catch (err) {
    console.error('Error loading testing devices:', err)
    pruefgeraete.value = []
  }
}

async function printLabel() {
  if (!repairRecord.value?.id) return
  printingLabel.value = true
  try {
    const result = await RepairsService.printLabel(repairRecord.value.id)
    showSnackbar(result.message || 'Label gedruckt')
  } catch (err: any) {
    const msg = err?.body?.error || err?.message || 'Fehler beim Drucken'
    showSnackbar(msg, 'error')
  } finally {
    printingLabel.value = false
  }
}

onMounted(async () => {
  const qrToken = route.params.qrToken as string

  if (!qrToken) {
    error.value = 'Kein QR-Token angegeben'
    loading.value = false
    return
  }

  try {
    // Load testing devices and users first
    await Promise.all([
      loadPruefgeraete(),
      userStore.loaded ? Promise.resolve() : userStore.fetchUsers(),
      ConfigService.getFeatures().then(f => { labelPrinterEnabled.value = f.label_printer }).catch(() => {}),
    ])

    // Fetch repair data by QR token
    const response = await RepairsService.getRepairByQrToken(qrToken)

    if (!response || !response.data) {
      error.value = 'Reparatur nicht gefunden'
      loading.value = false
      return
    }

    const repair = response.data as Repair
    repairRecord.value = repair

    selectedRepairStatus.value = repair.status || 'Offen'
    selectedStatusDetail.value = repair.status_detail || ''

    vdeInitialPruferUserId.value = repair.user_id ?? null

    // Load repair logs, VDE tests, and check for disclaimer
    await Promise.all([loadRepairLogs(), loadVdeTests(), loadLogAttachments()])

    // Check if disclaimer PDF exists
    if (repairRecord.value?.id) {
      try {
        const res = await fetch(`/api/repairs/${repairRecord.value.id}/disclaimer`, { method: 'HEAD' })
        disclaimerExists.value = res.ok
      } catch {
        disclaimerExists.value = false
      }
    }

    loading.value = false
  } catch (err) {
    console.error('Error loading repair:', err)
    error.value = 'Fehler beim Laden der Reparaturdaten: ' + (err as Error).message
    loading.value = false
  }
})

async function loadLogAttachments() {
  if (!repairRecord.value?.id) return
  try {
    const res = await fetch(`/api/repairs/${repairRecord.value.id}/log_attachments`)
    if (res.ok) {
      const data = await res.json()
      if (data.reply === 'done') {
        const mapped: Record<number, AttachmentInfo[]> = {}
        for (const [k, v] of Object.entries(data.data as Record<string, AttachmentInfo[]>)) {
          mapped[Number(k)] = v
        }
        logAttachments.value = mapped
      }
    }
  } catch {
    // silently ignore
  }
}

async function startLogCamera() {
  try {
    logCameraPermissionDenied.value = false
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false })
    logCameraStream = stream
    if (logVideoElement.value) {
      logVideoElement.value.srcObject = stream
      logCameraActive.value = true
    }
  } catch {
    logCameraPermissionDenied.value = true
  }
}

function stopLogCamera() {
  if (logCameraStream) {
    logCameraStream.getTracks().forEach(t => t.stop())
    logCameraStream = null
  }
  if (logVideoElement.value) logVideoElement.value.srcObject = null
  logCameraActive.value = false
}

function captureLogPhoto() {
  if (!logVideoElement.value || !logPhotoCanvas.value) return
  const video = logVideoElement.value
  const canvas = logPhotoCanvas.value
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const ctx = canvas.getContext('2d')
  if (ctx) {
    ctx.drawImage(video, 0, 0)
    pendingPhotos.value.push(canvas.toDataURL('image/jpeg', 0.8))
  }
}

function removePhoto(index: number) {
  pendingPhotos.value.splice(index, 1)
}

function dataUrlToFile(dataUrl: string, filename: string): File {
  const [header, data] = dataUrl.split(',')
  const mime = header.match(/:(.*?);/)?.[1] || 'image/jpeg'
  const bytes = atob(data)
  const arr = new Uint8Array(bytes.length)
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i)
  return new File([arr], filename, { type: mime })
}

async function uploadPendingAttachments(logId: number): Promise<void> {
  const hasPhotos = pendingPhotos.value.length > 0
  const hasFiles = pendingFiles.value.length > 0
  if (!hasPhotos && !hasFiles) return

  const fd = new FormData()
  pendingPhotos.value.forEach((dataUrl, i) => {
    fd.append('files', dataUrlToFile(dataUrl, `foto_${i + 1}.jpg`))
  })
  pendingFiles.value.forEach(f => fd.append('files', f))
  await fetch(`/api/repair_logs/${logId}/attachments`, { method: 'POST', body: fd })
}

async function addLogEntry() {
  if (!repairRecord.value || !logForm.value) return

  const { valid } = await logForm.value.validate()

  if (!valid) return

  saving.value = true

  try {
    const response = await RepairLogsService.createRepairLog(repairRecord.value.id, {
      user_id: newLog.value.user_id ?? undefined,
      reparatur_dauer: newLog.value.reparatur_dauer ?? 0,
      reparatur_besch: newLog.value.reparatur_besch
    })

    if (response.reply === 'done') {
      // Upload any pending attachments
      if (response.id) {
        await uploadPendingAttachments(response.id)
        await loadLogAttachments()
      }

      showSnackbar('Logeintrag erfolgreich hinzugefügt')

      // Close dialog
      closeLogDialog()

      // Reload logs
      await loadRepairLogs()
    } else {
      showSnackbar('Fehler beim Hinzufügen des Logeintrags: ' + (response.error || 'Unbekannter Fehler'), 'error')
    }
  } catch (err) {
    console.error('Error adding log entry:', err)
    showSnackbar('Fehler beim Speichern: ' + (err as Error).message, 'error')
  } finally {
    saving.value = false
  }
}

function openLogDialog() {
  logDialog.value = true
}

function openEditLogDialog(logId: number) {
  const log = repairLogs.value.find(l => l.id === logId)
  if (!log) return
  editingLogId.value = logId
  editLog.value = {
    user_id: log.user_id ?? null,
    reparatur_besch: log.reparatur_besch,
    reparatur_dauer: log.reparatur_dauer ?? null
  }
  editLogDialog.value = true
}

async function downloadVdePdf(testId: number) {
  if (!repairRecord.value?.id) return
  try {
    const res = await fetch(
      `/api/repairs/${repairRecord.value.id}/vde-tests/${testId}/pdf`,
      { credentials: 'include' }
    )
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `vde_pruefprotokoll_${repairRecord.value.id}_${testId}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    showSnackbar('Fehler beim Erzeugen des PDF')
  }
}

async function saveEditLog() {
  if (!repairRecord.value || !editingLogId.value || !editLogForm.value) return
  const { valid } = await editLogForm.value.validate()
  if (!valid) return

  editLogSaving.value = true
  try {
    const response = await RepairLogsService.updateRepairLog(repairRecord.value.id, editingLogId.value, {
      user_id: editLog.value.user_id ?? undefined,
      reparatur_besch: editLog.value.reparatur_besch,
      reparatur_dauer: editLog.value.reparatur_dauer ?? 0
    })
    if (response.reply === 'done') {
      showSnackbar('Logeintrag aktualisiert')
      editLogDialog.value = false
      await loadRepairLogs()
    } else {
      showSnackbar(response.error || 'Fehler beim Speichern', 'error')
    }
  } catch (err) {
    showSnackbar('Fehler beim Speichern: ' + (err as Error).message, 'error')
  } finally {
    editLogSaving.value = false
  }
}

function openVdeDialog() {
  vdeDialogMode.value = 'manual'
  vdeInitialPruferUserId.value = repairRecord.value?.user_id ?? null
  vdeDialog.value = true
}

function openVdeDialogForCloseFlow(preFilledPruferUserId?: number | null) {
  vdeDialogMode.value = 'close'
  vdeInitialPruferUserId.value = preFilledPruferUserId ?? repairRecord.value?.user_id ?? null
  vdeDialog.value = true
}

function closeLogDialog() {
  logDialog.value = false
  stopLogCamera()
  pendingPhotos.value = []
  pendingFiles.value = []
  // Reset form after closing
  setTimeout(() => {
    newLog.value = {
      user_id: null,
      reparatur_dauer: null,
      reparatur_besch: ''
    }
    logForm.value?.resetValidation?.()
  }, 300)
}

function getStatusColor(status: string): string {
  return getRepairStatusColor(status)
}

function getStatusIcon(status: string): string {
  return getRepairStatusIcon(status)
}

function isStatusChangeDisabled(status: string): boolean {
  const targetStatus = normalizeRepairStatus(status)
  return currentRepairStatus.value === targetStatus
    || !repairStore.canTransitionStatus(currentRepairStatus.value, targetStatus)
}

function openRepairCompletionDialog() {
  completionData.value = {
    description: repairRecord.value?.reparatur_besch || '',
    duration: suggestedRepairDuration.value > 0
      ? suggestedRepairDuration.value
      : (repairRecord.value?.reparatur_dauer || 0),
    needsVdeTest: !lastVdeTestPassed.value
  }
  completionDialog.value = true
}

function closeRepairCompletionDialog() {
  completionDialog.value = false
}

function handleCloseRepair(status: string) {
  const fromStatus = normalizeRepairStatus(repairRecord.value?.status)
  selectedRepairStatus.value = status
  const toStatus = normalizeRepairStatus(status)

  if (fromStatus === toStatus) {
    return
  }

  if (requiresCompletionDetailsForTransition(fromStatus, toStatus)) {
    openRepairCompletionDialog()
    return
  }

  if (requiresFailureDetailsForTransition(fromStatus, toStatus)) {
    notRepairableData.value = { description: '', statusDetail: '' }
    notRepairableDialog.value = true
    return
  }

  if (repairStore.requiresReparateurForTransition(fromStatus, toStatus) && !repairRecord.value?.user_id) {
    transitionUserId.value = null
    pendingTransitionStatus.value = status
    transitionDialog.value = true
    return
  }

  // Check if VDE test is required but not present
  if (vdeTestRequired.value && !hasVdeTest.value) {
    openVdeDialogForCloseFlow()
    return
  }

  // Otherwise, close directly
  closeRepair(status)
}

function closeTransitionDialog() {
  transitionDialog.value = false
  pendingTransitionStatus.value = ''
  transitionUserId.value = null
}

async function confirmTransitionWithReparateur(userId: number) {

  const targetStatus = pendingTransitionStatus.value

  closeTransitionDialog()

  if (vdeTestRequired.value && !hasVdeTest.value) {
    openVdeDialogForCloseFlow()
    return
  }

  await closeRepair(targetStatus, userId)
}

async function confirmRepairCompletion(payload: { description: string; duration: number; needsVdeTest: boolean }) {
  completionData.value = {
    description: payload.description,
    duration: payload.duration,
    needsVdeTest: payload.needsVdeTest
  }

  closeRepairCompletionDialog()

  if (payload.needsVdeTest) {
    selectedRepairStatus.value = 'Repariert'
    openVdeDialogForCloseFlow()
    return
  }

  await closeRepair('Repariert')
}

async function handleVdeSubmit(payload: VdeFormData) {
  if (!repairRecord.value?.id) return

  saving.value = true

  try {
    const vdePayload: Omit<VdeTestCreate, 'repair_id'> = {
      // The datetime-local input gives a local-time string; convert to UTC ISO so
      // the backend stores UTC just like auto-generated created_at timestamps.
      created_at: payload.created_at ? new Date(payload.created_at).toISOString() : undefined,
      prufer_user_id: payload.prufer_user_id ?? undefined,
      electrician: payload.electrician || undefined,
      pruefgeraet_name: payload.pruefgeraet_name || undefined,
      pruefgeraet_serial: payload.pruefgeraet_serial || undefined,
      sichtpruefung_gehaeuse: payload.sichtpruefung_gehaeuse ?? undefined,
      sichtpruefung_kabel: payload.sichtpruefung_kabel ?? undefined,
      sichtpruefung_stecker: payload.sichtpruefung_stecker ?? undefined,
      sichtpruefung_zugentlastung: payload.sichtpruefung_zugentlastung ?? undefined,
      sichtpruefung_sicherheit: payload.sichtpruefung_sicherheit ?? undefined,
      schutzklasse: payload.schutzklasse || undefined,
      schutzleiter_pruefung: payload.schutzleiter_pruefung ?? undefined,
      isolationspruefung: payload.isolationspruefung ?? undefined,
      ableitstrom_pruefung: payload.ableitstrom_pruefung ?? undefined,
      gesamtergebnis: payload.gesamtergebnis!,
      bemerkungen: payload.bemerkungen || undefined
    }

    const vdeResponse = await VdeTestsService.createVdeTest(repairRecord.value.id, vdePayload)

    if (vdeResponse.reply !== 'done') {
      showSnackbar('Fehler beim Speichern des VDE Tests', 'error')
      return
    }

    await loadVdeTests()
    vdeDialog.value = false

    if (vdeDialogMode.value === 'manual') {
      showSnackbar('VDE-Test erfolgreich protokolliert')
      return
    }

    if (!payload.gesamtergebnis) {
      selectedRepairStatus.value = repairRecord.value.status || 'In Bearbeitung'
      showSnackbar(
        'VDE-Test nicht bestanden. Die Reparatur kann nicht als repariert abgeschlossen werden. ' +
        'Bitte weiterarbeiten oder den Status auf "Nicht Repariert" setzen.',
        'warning'
      )
      return
    }

    await closeRepair('Repariert')
  } catch (err) {
    console.error('Error saving VDE test:', err)
    showSnackbar('Fehler beim Speichern: ' + (err as Error).message, 'error')
  } finally {
    saving.value = false
  }
}

async function closeRepair(status: string = selectedRepairStatus.value, userId?: number) {
  if (!repairRecord.value?.id || !status) return

  savingStatus.value = true

  try {
    const fromStatus = normalizeRepairStatus(repairRecord.value.status)
    const toStatus = normalizeRepairStatus(status)

    // Only pass statusDetail if it is valid for the target status
    const validDetailsForTarget = getRepairStatusDetailOptions(toStatus)
    const validStatusDetail = validDetailsForTarget.includes(selectedStatusDetail.value)
      ? selectedStatusDetail.value
      : undefined

    if (toStatus === 'Repariert') {
      await repairStore.completeSuccessfulRepair({
        repairId: repairRecord.value.id,
        fromStatus,
        statusDetail: validStatusDetail,
        user_id: userId || repairRecord.value.user_id || undefined,
        repairDescription: completionData.value.description,
        repairDuration: Number(completionData.value.duration ?? 0)
      })
      await RepairLogsService.createRepairLog(repairRecord.value.id, {
        user_id: userId || repairRecord.value.user_id || undefined,
        reparatur_dauer: Number(completionData.value.duration ?? 0),
        reparatur_besch: completionData.value.description,
        status_from: fromStatus,
        status_to: 'Repariert'
      })
    } else {
      await repairStore.transitionRepairStatus({
        repairId: repairRecord.value.id,
        fromStatus,
        toStatus,
        statusDetail: validStatusDetail,
        user_id: userId || repairRecord.value.user_id || undefined
      })
      await RepairLogsService.createRepairLog(repairRecord.value.id, {
        user_id: userId || repairRecord.value.user_id || undefined,
        reparatur_dauer: 0,
        reparatur_besch: '',
        log_type: 'status_change',
        status_from: fromStatus,
        status_to: toStatus
      })
    }

    showSnackbar(`Reparatur erfolgreich abgeschlossen`)
    if (toStatus === 'Repariert') {
      confetti({
        particleCount: 150,
        spread: 80,
        origin: { y: 0.6 }
      })
    }
    repairRecord.value.status = status
    repairRecord.value.status_detail = selectedStatusDetail.value
    if (userId) {
      repairRecord.value.user_id = userId
    }
    if (toStatus === 'Repariert') {
      repairRecord.value.reparatur_besch = completionData.value.description
      repairRecord.value.reparatur_dauer = Number(completionData.value.duration ?? 0)
    }

    // Navigate back after successful close
    setTimeout(() => goBack(), 1500)
  } catch (err) {
    console.error('Error closing repair:', err)
    showSnackbar('Fehler beim Speichern: ' + (err as Error).message, 'error')
  } finally {
    savingStatus.value = false
  }
}

async function confirmNotRepairable(payload: { description: string; statusDetail: string }) {
  notRepairableData.value = payload
  notRepairableDialog.value = false

  if (payload.statusDetail === 'Abbruch') {
    pendingAbbruchPayload.value = payload
    abbruchSignatureDialog.value = true
    return
  }

  await saveNotRepairable(payload)
}

async function confirmAbbruchSignature(_signaturePayload: { signature: string }) {
  abbruchSignatureDialog.value = false
  // Signature data will be stored in a later implementation step
  if (pendingAbbruchPayload.value) {
    await saveNotRepairable(pendingAbbruchPayload.value)
    pendingAbbruchPayload.value = null
  }
}

async function saveNotRepairable(payload: { description: string; statusDetail: string }) {
  if (!repairRecord.value) return

  savingStatus.value = true
  try {
    const fromStatus = normalizeRepairStatus(repairRecord.value.status)
    await repairStore.completeFailedRepair({
      repairId: repairRecord.value.id,
      fromStatus,
      statusDetail: payload.statusDetail || undefined,
      user_id: repairRecord.value.user_id || undefined,
      repairDescription: payload.description
    })
    await RepairLogsService.createRepairLog(repairRecord.value.id, {
      user_id: repairRecord.value.user_id || undefined,
      reparatur_dauer: 0,
      reparatur_besch: payload.description,
      status_from: fromStatus,
      status_to: 'Nicht Repariert'
    })
    showSnackbar('Reparatur als nicht reparierbar abgeschlossen')
    repairRecord.value.status = 'Nicht Repariert'
    repairRecord.value.status_detail = payload.statusDetail
    repairRecord.value.reparatur_besch = payload.description
    selectedRepairStatus.value = 'Nicht Repariert'
    setTimeout(() => goBack(), 1500)
  } catch (err) {
    console.error('Error closing repair as not repairable:', err)
    showSnackbar('Fehler beim Speichern: ' + (err as Error).message, 'error')
  } finally {
    savingStatus.value = false
  }
}

function goBack() {
  router.back()
}
</script>

<style scoped></style>
