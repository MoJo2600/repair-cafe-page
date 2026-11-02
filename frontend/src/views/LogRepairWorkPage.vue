<script setup lang="ts">
import { api } from '@/api/client'
import type { VdeTestCreate } from '@/api/types'
import { onMounted, ref, shallowRef, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { PruefgeraetResponse, Repair } from '@/api/types'
import {
  getRepairStatusColor,
  getRepairStatusDetailOptions,
  getRepairStatusIcon,
  normalizeRepairStatus,
} from '@/domain/repairStatus'
import { useUserStore } from '@/stores/userStore'
import { useRepairDetail } from '@/composables/useRepairDetail'
import { useRepairStatusTransition } from '@/composables/useRepairStatusTransition'
import { useToast } from '@/composables/useToast'
import { errorMessage } from '@/utils/errors'
import RepairSummaryCard from '@/components/RepairSummaryCard.vue'
import RepairActivityTimeline from '@/components/RepairActivityTimeline.vue'
import RepairAttachmentsPanel from '@/components/RepairAttachmentsPanel.vue'
import RepairAssigneeSelect from '@/components/RepairAssigneeSelect.vue'
import LogEntryDialog from '@/components/LogEntryDialog.vue'
import EditLogDialog from '@/components/EditLogDialog.vue'
import ReparateurRequiredDialog from '@/components/ReparateurRequiredDialog.vue'
import RepairCompletionDialog from '@/components/RepairCompletionDialog.vue'
import RepairNotRepairableDialog from '@/components/RepairNotRepairableDialog.vue'
import AbbruchSignatureDialog from '@/components/AbbruchSignatureDialog.vue'
import VdeTestDialog, { type VdeFormData } from '@/components/VdeTestDialog.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const toast = useToast()

// ── Repair data ───────────────────────────────────────────────────────────────
const selectedRepairStatus = ref('')
const selectedStatusDetail = ref('')
const vdeInitialPruferUserId = ref<number | null>(null)

const {
  loading,
  error,
  repair,
  logs,
  attachments,
  disclaimerExists,
  cancellationExists,
  latestVdeTests,
  lastVdeTestPassed,
  threadEntries,
  hasVdeTest,
  loggedDuration,
  logAttachments,
  reloadRepair,
  reloadLogs,
  reloadVdeTests,
  reloadAttachments,
} = useRepairDetail(() => route.params.qrToken as string | undefined, {
  onLoaded(loaded) {
    selectedRepairStatus.value = loaded.status || 'Offen'
    selectedStatusDetail.value = loaded.status_detail || ''
    vdeInitialPruferUserId.value = loaded.user_id ?? null
  },
})

const currentRepairStatus = computed(() => normalizeRepairStatus(repair.value?.status))
const attachmentCounts = computed(() =>
  Object.fromEntries(Object.entries(logAttachments.value).map(([id, list]) => [id, list.length]))
)

watch(selectedRepairStatus, (newStatus) => {
  const allowedDetails = getRepairStatusDetailOptions(newStatus)
  if (selectedStatusDetail.value && !allowedDetails.includes(selectedStatusDetail.value)) {
    selectedStatusDetail.value = ''
  }
})

// ── Data that does not depend on the opened repair ────────────────────────────
const pruefgeraete = ref<PruefgeraetResponse[]>([])
const labelPrinterEnabled = shallowRef(false)

onMounted(() => {
  void Promise.all([
    api.getPruefgeraete()
      .then((devices) => {
        pruefgeraete.value = devices
      })
      .catch((err) => console.error('Error loading testing devices:', err)),
    userStore.loaded ? Promise.resolve() : userStore.fetchUsers(),
    api.getFeatures()
      .then((f) => {
        labelPrinterEnabled.value = f.label_printer ?? false
      })
      .catch(() => {}),
  ])
})

// ── Dialogs ───────────────────────────────────────────────────────────────────
const logDialog = shallowRef(false)
const editLogDialog = shallowRef(false)
const editingLogId = ref<number | null>(null)
const editingLog = computed(() => logs.value.find((l) => l.id === editingLogId.value) ?? null)
const vdeDialog = shallowRef(false)
const vdeDialogMode = ref<'manual' | 'close'>('manual')

// A different repair was opened (e.g. QR scan from this page)
watch(
  () => route.params.qrToken,
  () => {
    logDialog.value = false
    editLogDialog.value = false
    vdeDialog.value = false
  }
)

function openEditLogDialog(logId: number) {
  editingLogId.value = logId
  editLogDialog.value = true
}

function openVdeDialog() {
  vdeDialogMode.value = 'manual'
  vdeInitialPruferUserId.value = repair.value?.user_id ?? null
  vdeDialog.value = true
}

function openVdeDialogForCloseFlow(preFilledPruferUserId?: number | null) {
  vdeDialogMode.value = 'close'
  vdeInitialPruferUserId.value = preFilledPruferUserId ?? repair.value?.user_id ?? null
  vdeDialog.value = true
}

// ── Status transitions ────────────────────────────────────────────────────────
const {
  savingStatus,
  transitionDialog,
  transitionUserId,
  completionDialog,
  completionData,
  notRepairableDialog,
  abbruchSignatureDialog,
  availableNextStatuses,
  bestNextStatus,
  otherNextStatuses,
  handleCloseRepair,
  closeRepair,
  confirmTransitionWithReparateur,
  confirmRepairCompletion,
  confirmNotRepairable,
  confirmAbbruchSignature,
} = useRepairStatusTransition({
  repairRecord: repair,
  selectedRepairStatus,
  selectedStatusDetail,
  currentRepairStatus,
  hasVdeTest,
  lastVdeTestPassed,
  suggestedRepairDuration: loggedDuration,
  loadRepairLogs: reloadLogs,
  onNeedsVdeTest: openVdeDialogForCloseFlow,
  onCancellationSigned: () => {
    cancellationExists.value = true
  },
})

// ── Child component events ────────────────────────────────────────────────────
function onRepairFieldsUpdated(fields: Partial<Repair>) {
  if (repair.value) repair.value = { ...repair.value, ...fields }
}

function onAssigned(userId: number | null) {
  if (!repair.value) return
  repair.value.user_id = userId ?? undefined
  repair.value.user = userId ? userStore.getUserById(userId) : undefined
  void reloadLogs()
}

function onLogsChanged() {
  void Promise.all([reloadRepair(), reloadLogs(), reloadAttachments()])
}

// ── Actions ───────────────────────────────────────────────────────────────────
const printingLabel = shallowRef(false)
const savingVde = shallowRef(false)

async function printLabel() {
  if (!repair.value) return
  printingLabel.value = true
  try {
    const result = await api.printRepairLabel({ id: repair.value.id }, {})
    toast.success(result.message || 'Label gedruckt')
  } catch (err) {
    toast.error(errorMessage(err, 'Fehler beim Drucken'))
  } finally {
    printingLabel.value = false
  }
}

async function downloadVdePdf(testId: number) {
  if (!repair.value) return
  const repairId = repair.value.id
  try {
    const pdf = await api.getVdeTestPdf({ repairId, testId }, { format: 'blob' })
    const url = URL.createObjectURL(pdf)
    const link = document.createElement('a')
    link.href = url
    link.download = `vde_pruefprotokoll_${repairId}_${testId}.pdf`
    link.click()
    URL.revokeObjectURL(url)
  } catch {
    toast.error('Fehler beim Erzeugen des PDF')
  }
}

async function handleVdeSubmit(payload: VdeFormData) {
  if (!repair.value) return
  savingVde.value = true
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
      bemerkungen: payload.bemerkungen || undefined,
    }

    const vdeResponse = await api.createVdeTest({ repairId: repair.value.id }, { repair_id: repair.value.id, ...vdePayload })
    if (vdeResponse.reply !== 'done') {
      toast.error('Fehler beim Speichern des VDE Tests')
      return
    }

    await reloadVdeTests()
    vdeDialog.value = false

    if (vdeDialogMode.value === 'manual') {
      toast.success('VDE-Test erfolgreich protokolliert')
      return
    }

    if (!payload.gesamtergebnis) {
      selectedRepairStatus.value = repair.value.status || 'In Bearbeitung'
      toast.warning(
        'VDE-Test nicht bestanden. Die Reparatur kann nicht als repariert abgeschlossen werden. ' +
          'Bitte weiterarbeiten oder den Status auf "Nicht Repariert" setzen.'
      )
      return
    }

    await closeRepair('Repariert')
  } catch (err) {
    console.error('Error saving VDE test:', err)
    toast.error('Fehler beim Speichern: ' + errorMessage(err, 'Unbekannter Fehler'))
  } finally {
    savingVde.value = false
  }
}
</script>

<template>
  <v-container class="d-flex justify-center align-center page">
    <v-card max-width="1200px" width="100%">
      <v-card-text v-if="loading">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
        <span class="ml-3">Lade Reparaturdaten...</span>
      </v-card-text>

      <v-card-text v-else-if="error">
        <v-alert type="error">{{ error }}</v-alert>
      </v-card-text>

      <v-card-text v-else-if="repair">
        <v-row class="align-start">
          <!-- Left column: summary, activity, attachments -->
          <v-col cols="12" md="8">
            <RepairSummaryCard
              :repair-data="repair"
              :vde-tests="latestVdeTests"
              :logged-duration="loggedDuration"
              @updated="onRepairFieldsUpdated"
            />

            <RepairActivityTimeline
              :entries="threadEntries"
              :attachment-counts="attachmentCounts"
              @edit-log="openEditLogDialog"
              @download-vde="downloadVdePdf"
            />

            <RepairAttachmentsPanel
              class="mt-6"
              :repair-id="repair.id"
              :attachments="attachments"
              :disclaimer-exists="disclaimerExists"
              :cancellation-exists="cancellationExists"
              :show-cancellation="repair.status_detail === 'Abbruch'"
              @changed="reloadAttachments"
            />
          </v-col>

          <!-- Right column: status, assignee, quick actions -->
          <v-col cols="12" md="4">
            <div class="d-flex align-center ga-3 flex-wrap mb-6">
              <v-btn-group v-if="availableNextStatuses.length > 0" divided>
                <v-btn
                  :color="getRepairStatusColor(bestNextStatus ?? '')"
                  :prepend-icon="getRepairStatusIcon(bestNextStatus ?? '')"
                  :loading="savingStatus"
                  @click="bestNextStatus && handleCloseRepair(bestNextStatus)"
                >
                  {{ bestNextStatus }}
                </v-btn>
                <v-menu v-if="otherNextStatuses.length > 0">
                  <template #activator="{ props: menuProps }">
                    <v-btn
                      v-bind="menuProps"
                      :color="getRepairStatusColor(bestNextStatus ?? '')"
                      icon="mdi-chevron-down"
                    ></v-btn>
                  </template>
                  <v-list density="compact">
                    <v-list-item
                      v-for="status in otherNextStatuses"
                      :key="status"
                      :prepend-icon="getRepairStatusIcon(status)"
                      :title="status"
                      @click="handleCloseRepair(status)"
                    ></v-list-item>
                  </v-list>
                </v-menu>
              </v-btn-group>
            </div>

            <RepairAssigneeSelect
              :repair-id="repair.id"
              :assignee-id="repair.user_id ?? null"
              @assigned="onAssigned"
            />

            <div class="d-flex flex-column ga-2 mt-6">
              <span class="text-body-large text-grey-darken-1">Quick Actions</span>
              <v-btn
                variant="tonal"
                color="primary"
                prepend-icon="mdi-plus"
                block
                @click="logDialog = true"
              >
                Neuer Logeintrag
              </v-btn>
              <v-btn
                variant="tonal"
                color="primary"
                prepend-icon="mdi-flash"
                block
                @click="openVdeDialog"
              >
                VDE Test protokollieren
              </v-btn>
              <v-btn
                v-if="labelPrinterEnabled"
                variant="tonal"
                color="primary"
                prepend-icon="mdi-printer"
                :loading="printingLabel"
                block
                @click="printLabel"
              >
                Label drucken
              </v-btn>
            </div>
          </v-col>
        </v-row>
      </v-card-text>

      <v-card-actions v-if="!loading && !error" class="flex-wrap ga-2">
        <v-btn prepend-icon="mdi-arrow-left" @click="router.back()">Zurück</v-btn>
      </v-card-actions>
    </v-card>

    <template v-if="repair">
      <LogEntryDialog v-model="logDialog" :repair-id="repair.id" @saved="onLogsChanged" />

      <EditLogDialog
        v-model="editLogDialog"
        :repair-id="repair.id"
        :log="editingLog"
        :attachments="editingLogId ? (logAttachments[editingLogId] ?? []) : []"
        @changed="onLogsChanged"
      />
    </template>

    <ReparateurRequiredDialog
      v-model="transitionDialog"
      v-model:user-id="transitionUserId"
      title="Reparatur starten"
      message="Für den Wechsel von 'Offen' zu 'In Bearbeitung' muss ein Reparateur angegeben werden."
      confirm-text="Weiter"
      @confirm="confirmTransitionWithReparateur"
    />

    <RepairCompletionDialog
      v-model="completionDialog"
      v-model:description="completionData.description"
      v-model:duration="completionData.duration"
      v-model:needs-vde-test="completionData.needsVdeTest"
      :suggested-duration="loggedDuration"
      :has-any-vde-test="hasVdeTest"
      :last-vde-test-passed="lastVdeTestPassed"
      :loading="savingStatus"
      @confirm="confirmRepairCompletion"
    />

    <RepairNotRepairableDialog
      v-model="notRepairableDialog"
      :suggested-duration="loggedDuration"
      :loading="savingStatus"
      @confirm="confirmNotRepairable"
    />

    <AbbruchSignatureDialog
      v-model="abbruchSignatureDialog"
      :loading="savingStatus"
      @confirm="confirmAbbruchSignature"
    />

    <VdeTestDialog
      v-model="vdeDialog"
      :saving="savingVde"
      :repair-id="repair?.id"
      :selected-repair-status="selectedRepairStatus"
      :required-for-status="vdeDialogMode === 'close'"
      :confirm-text="
        vdeDialogMode === 'close' ? 'VDE speichern & Reparatur abschliessen' : 'VDE speichern'
      "
      :initial-prufer-user-id="vdeInitialPruferUserId"
      :users="userStore.users"
      :pruefgeraete="pruefgeraete"
      @submit="handleVdeSubmit"
    />
  </v-container>
</template>

<style scoped>
.page {
  min-height: 80vh;
}
</style>
