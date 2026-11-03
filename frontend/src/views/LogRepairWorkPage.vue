<script setup lang="ts">
import { api } from '@/api/client'
import type { VdeTestCreate } from '@/api/types'
import { onMounted, ref, shallowRef, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
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
import CountBadge from '@/components/ui/CountBadge.vue'
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
// Side panel from md up; tabs and a bottom action bar on phones and portrait tablets
const { mdAndUp } = useDisplay()
const contentTab = shallowRef<'activity' | 'attachments'>('activity')

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
  // Reload for derived data the form doesn't have (e.g. the category name)
  void reloadRepair()
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

const quickActions = computed(() => [
  {
    key: 'log',
    title: 'Neuer Logeintrag',
    icon: 'mdi-note-plus',
    loading: false,
    run: () => {
      logDialog.value = true
    },
  },
  { key: 'vde', title: 'VDE-Test protokollieren', icon: 'mdi-flash', loading: false, run: openVdeDialog },
  ...(labelPrinterEnabled.value
    ? [
        {
          key: 'label',
          title: 'Label drucken',
          icon: 'mdi-printer',
          loading: printingLabel.value,
          run: () => void printLabel(),
        },
      ]
    : []),
])

const attachmentsPanelProps = computed(() => ({
  repairId: repair.value!.id,
  attachments: attachments.value,
  disclaimerExists: disclaimerExists.value,
  cancellationExists: cancellationExists.value,
  showCancellation: repair.value!.status_detail === 'Abbruch',
}))

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
  <v-container fluid class="page-container pb-16">
    <div v-if="loading" class="d-flex align-center ga-3 pa-4">
      <v-progress-circular indeterminate color="primary"></v-progress-circular>
      <span>Lade Reparaturdaten...</span>
    </div>

    <v-alert v-else-if="error" type="error" class="ma-4">{{ error }}</v-alert>

    <template v-else-if="repair">
      <v-btn variant="text" prepend-icon="mdi-arrow-left" class="mb-2" @click="router.back()">
        Zurück
      </v-btn>

      <v-row class="align-start">
        <!-- Main column: summary, activity, attachments -->
        <v-col cols="12" md="8">
          <RepairSummaryCard
            :repair-data="repair"
            :vde-tests="latestVdeTests"
            :logged-duration="loggedDuration"
            @updated="onRepairFieldsUpdated"
          />

          <!-- Small screens: the side panel's assignee moves here -->
          <v-card v-if="!mdAndUp" class="mb-4">
            <v-card-text>
              <RepairAssigneeSelect
                :repair-id="repair.id"
                :assignee-id="repair.user_id ?? null"
                @assigned="onAssigned"
              />
            </v-card-text>
          </v-card>

          <template v-if="mdAndUp">
            <RepairActivityTimeline
              :entries="threadEntries"
              :attachment-counts="attachmentCounts"
              @edit-log="openEditLogDialog"
              @download-vde="downloadVdePdf"
            />
            <RepairAttachmentsPanel v-bind="attachmentsPanelProps" class="mt-6" @changed="reloadAttachments" />
          </template>

          <!-- Small screens: one section at a time -->
          <template v-else>
            <v-tabs v-model="contentTab" grow class="mb-4">
              <v-tab value="activity" prepend-icon="mdi-history">Verlauf</v-tab>
              <v-tab value="attachments" prepend-icon="mdi-paperclip">
                Anhänge
                <CountBadge v-if="attachments.length" :count="attachments.length" />
              </v-tab>
            </v-tabs>
            <RepairActivityTimeline
              v-if="contentTab === 'activity'"
              :show-title="false"
              :entries="threadEntries"
              :attachment-counts="attachmentCounts"
              @edit-log="openEditLogDialog"
              @download-vde="downloadVdePdf"
            />
            <RepairAttachmentsPanel
              v-else
              v-bind="attachmentsPanelProps"
              :show-title="false"
              @changed="reloadAttachments"
            />
          </template>
        </v-col>

        <!-- Side panel (md+): stays in view while scrolling -->
        <v-col v-if="mdAndUp" cols="12" md="4" class="side-panel">
          <v-card>
            <v-card-item title="Status" prepend-icon="mdi-swap-horizontal" />
            <v-card-text class="d-flex flex-column ga-2">
              <v-btn
                v-if="bestNextStatus"
                :color="getRepairStatusColor(bestNextStatus)"
                :prepend-icon="getRepairStatusIcon(bestNextStatus)"
                :loading="savingStatus"
                size="large"
                variant="flat"
                block
                @click="handleCloseRepair(bestNextStatus)"
              >
                {{ bestNextStatus }}
              </v-btn>
              <v-btn
                v-for="status in otherNextStatuses"
                :key="status"
                :color="getRepairStatusColor(status)"
                :prepend-icon="getRepairStatusIcon(status)"
                :disabled="savingStatus"
                variant="tonal"
                block
                @click="handleCloseRepair(status)"
              >
                {{ status }}
              </v-btn>
            </v-card-text>

            <v-divider />
            <v-card-text>
              <RepairAssigneeSelect
                :repair-id="repair.id"
                :assignee-id="repair.user_id ?? null"
                @assigned="onAssigned"
              />
            </v-card-text>

            <v-divider />
            <v-card-text class="d-flex flex-column ga-2">
              <v-btn
                v-for="action in quickActions"
                :key="action.key"
                :prepend-icon="action.icon"
                :loading="action.loading"
                variant="tonal"
                color="primary"
                size="large"
                block
                @click="action.run"
              >
                {{ action.title }}
              </v-btn>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Small screens: actions within thumb reach -->
      <div v-if="!mdAndUp" class="action-bar d-flex align-center ga-2 pa-3">
        <v-btn
          v-if="bestNextStatus"
          :color="getRepairStatusColor(bestNextStatus)"
          :prepend-icon="getRepairStatusIcon(bestNextStatus)"
          :loading="savingStatus"
          size="large"
          variant="flat"
          class="flex-grow-1"
          @click="handleCloseRepair(bestNextStatus)"
        >
          {{ bestNextStatus }}
        </v-btn>
        <v-btn
          icon="mdi-note-plus"
          size="large"
          variant="tonal"
          color="primary"
          aria-label="Neuer Logeintrag"
          @click="logDialog = true"
        />
        <v-menu location="top end">
          <template #activator="{ props: menuProps }">
            <v-btn v-bind="menuProps" icon="mdi-dots-vertical" size="large" variant="tonal" aria-label="Weitere Aktionen" />
          </template>
          <v-list>
            <v-list-subheader v-if="otherNextStatuses.length">Status ändern</v-list-subheader>
            <v-list-item
              v-for="status in otherNextStatuses"
              :key="status"
              :prepend-icon="getRepairStatusIcon(status)"
              :title="status"
              @click="handleCloseRepair(status)"
            />
            <v-divider v-if="otherNextStatuses.length" />
            <v-list-item
              v-for="action in quickActions.filter((a) => a.key !== 'log')"
              :key="action.key"
              :prepend-icon="action.icon"
              :title="action.title"
              @click="action.run"
            />
          </v-list>
        </v-menu>
      </div>
    </template>

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

.side-panel {
  position: sticky;
  top: calc(var(--v-layout-top, 0px) + 16px);
}

/* Sits above the app footer (Vuetify sets --v-layout-bottom on v-main) */
.action-bar {
  position: sticky;
  bottom: var(--v-layout-bottom, 0px);
  z-index: 2;
  margin: 0 -16px;
  background: rgb(var(--v-theme-surface));
  border-top: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
}
</style>
