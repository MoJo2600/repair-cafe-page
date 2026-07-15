import { ref, computed, type Ref, type ComputedRef } from 'vue'
import {
  useRepairStore,
  normalizeRepairStatus,
  REPAIR_STATUSES,
  getRepairStatusDetailOptions,
  requiresCompletionDetailsForTransition,
  requiresFailureDetailsForTransition,
  type RepairStatus,
} from '@/stores/repairStore'
import { RepairLogsService } from '@/api/services/RepairLogsService'
import confetti from 'canvas-confetti'
import type { Repair } from '@/api/types'

export interface UseRepairStatusTransitionOptions {
  repairRecord: Ref<Repair | null>
  selectedRepairStatus: Ref<string>
  selectedStatusDetail: Ref<string>
  currentRepairStatus: ComputedRef<string>
  hasVdeTest: ComputedRef<boolean>
  lastVdeTestPassed: ComputedRef<boolean>
  suggestedRepairDuration: ComputedRef<number>
  selectedAssigneeId: Ref<number | null>
  showSnackbar: (msg: string, color?: string) => void
  loadRepairLogs: () => Promise<void>
  /** Called when a status transition requires a VDE test first. */
  onNeedsVdeTest: (preFilledUserId?: number | null) => void
}

export function useRepairStatusTransition(options: UseRepairStatusTransitionOptions) {
  const repairStore = useRepairStore()

  const savingStatus = ref(false)
  const transitionDialog = ref(false)
  const completionDialog = ref(false)
  const notRepairableDialog = ref(false)
  const pendingTransitionStatus = ref('')
  const transitionUserId = ref<number | null>(null)
  const completionData = ref({
    description: '',
    duration: null as number | null,
    needsVdeTest: false,
  })
  const notRepairableData = ref({ description: '', statusDetail: '', duration: 0 })
  const abbruchSignatureDialog = ref(false)
  const pendingAbbruchPayload = ref<{ description: string; statusDetail: string; duration: number } | null>(null)

  // ── Status helpers ────────────────────────────────────────────────────

  function isStatusChangeDisabled(status: string): boolean {
    const target = normalizeRepairStatus(status) as RepairStatus
    const from = options.currentRepairStatus.value as RepairStatus
    return from === target || !repairStore.canTransitionStatus(from, target)
  }

  const availableNextStatuses = computed<RepairStatus[]>(() =>
    [...REPAIR_STATUSES].filter((s) => !isStatusChangeDisabled(s))
  )

  const bestNextStatus = computed<RepairStatus | null>(() => {
    const current = options.currentRepairStatus.value
    const preferred: RepairStatus | null =
      current === 'Offen'
        ? 'In Bearbeitung'
        : current === 'In Bearbeitung'
          ? 'Repariert'
          : current === 'Nicht Repariert'
            ? 'In Bearbeitung'
            : null
    if (preferred && availableNextStatuses.value.includes(preferred)) return preferred
    return availableNextStatuses.value[0] ?? null
  })

  const otherNextStatuses = computed<RepairStatus[]>(() =>
    availableNextStatuses.value.filter((s) => s !== bestNextStatus.value)
  )

  const vdeTestRequired = computed(
    () =>
      options.selectedRepairStatus.value === 'Repariert' ||
      options.selectedStatusDetail.value === 'Abbruch'
  )

  // ── Dialogs ───────────────────────────────────────────────────────────

  function openRepairCompletionDialog() {
    completionData.value = {
      description: options.repairRecord.value?.reparatur_besch || '',
      duration:
        options.suggestedRepairDuration.value > 0
          ? options.suggestedRepairDuration.value
          : options.repairRecord.value?.reparatur_dauer || 0,
      needsVdeTest: !options.lastVdeTestPassed.value,
    }
    completionDialog.value = true
  }

  function closeRepairCompletionDialog() {
    completionDialog.value = false
  }

  function closeTransitionDialog() {
    transitionDialog.value = false
    pendingTransitionStatus.value = ''
    transitionUserId.value = null
  }

  // ── Main status change handler ────────────────────────────────────────

  function handleCloseRepair(status: string) {
    const fromStatus = normalizeRepairStatus(options.repairRecord.value?.status)
    options.selectedRepairStatus.value = status
    const toStatus = normalizeRepairStatus(status)

    if (fromStatus === toStatus) return

    if (requiresCompletionDetailsForTransition(fromStatus, toStatus)) {
      openRepairCompletionDialog()
      return
    }

    if (requiresFailureDetailsForTransition(fromStatus, toStatus)) {
      notRepairableData.value = { description: '', statusDetail: '', duration: options.suggestedRepairDuration.value }
      notRepairableDialog.value = true
      return
    }

    if (
      repairStore.requiresReparateurForTransition(fromStatus, toStatus) &&
      !options.repairRecord.value?.user_id
    ) {
      transitionUserId.value = null
      pendingTransitionStatus.value = status
      transitionDialog.value = true
      return
    }

    if (vdeTestRequired.value && !options.hasVdeTest.value) {
      options.onNeedsVdeTest(options.repairRecord.value?.user_id ?? null)
      return
    }

    closeRepair(status)
  }

  async function confirmTransitionWithReparateur(userId: number) {
    const targetStatus = pendingTransitionStatus.value
    closeTransitionDialog()

    if (vdeTestRequired.value && !options.hasVdeTest.value) {
      options.onNeedsVdeTest(userId)
      return
    }

    await closeRepair(targetStatus, userId)
  }

  async function confirmRepairCompletion(payload: {
    description: string
    duration: number
    needsVdeTest: boolean
  }) {
    completionData.value = {
      description: payload.description,
      duration: payload.duration,
      needsVdeTest: payload.needsVdeTest,
    }
    closeRepairCompletionDialog()

    if (payload.needsVdeTest) {
      options.selectedRepairStatus.value = 'Repariert'
      options.onNeedsVdeTest(options.repairRecord.value?.user_id ?? null)
      return
    }

    await closeRepair('Repariert')
  }

  // ── Core repair close ─────────────────────────────────────────────────

  async function closeRepair(status: string = options.selectedRepairStatus.value, userId?: number) {
    if (!options.repairRecord.value?.id || !status) return
    savingStatus.value = true
    try {
      const fromStatus = normalizeRepairStatus(options.repairRecord.value.status)
      const toStatus = normalizeRepairStatus(status)
      const validDetailsForTarget = getRepairStatusDetailOptions(toStatus)
      const validStatusDetail = validDetailsForTarget.includes(options.selectedStatusDetail.value)
        ? options.selectedStatusDetail.value
        : undefined

      if (toStatus === 'Repariert') {
        await repairStore.completeSuccessfulRepair({
          repairId: options.repairRecord.value.id,
          fromStatus,
          statusDetail: validStatusDetail,
          user_id: userId || options.repairRecord.value.user_id || undefined,
          repairDescription: completionData.value.description,
          repairDuration: Number(completionData.value.duration ?? 0),
        })
        await RepairLogsService.createRepairLog(options.repairRecord.value.id, {
          user_id: userId || options.repairRecord.value.user_id || undefined,
          reparatur_dauer: Number(completionData.value.duration ?? 0),
          reparatur_besch: completionData.value.description,
          status_from: fromStatus,
          status_to: 'Repariert',
        })
      } else {
        await repairStore.transitionRepairStatus({
          repairId: options.repairRecord.value.id,
          fromStatus,
          toStatus,
          statusDetail: validStatusDetail,
          user_id: userId || options.repairRecord.value.user_id || undefined,
        })
        await RepairLogsService.createRepairLog(options.repairRecord.value.id, {
          user_id: userId || options.repairRecord.value.user_id || undefined,
          reparatur_dauer: 0,
          reparatur_besch: '',
          log_type: 'status_change',
          status_from: fromStatus,
          status_to: toStatus,
        })
      }

      options.showSnackbar(`Status update erfolgreich: ${toStatus}`)
      if (toStatus === 'Repariert') {
        confetti({ particleCount: 150, spread: 80, origin: { y: 0.6 } })
      }

      options.repairRecord.value.status = status
      options.repairRecord.value.status_detail = options.selectedStatusDetail.value
      if (userId) options.repairRecord.value.user_id = userId
      if (toStatus === 'Repariert') {
        options.repairRecord.value.reparatur_besch = completionData.value.description
        options.repairRecord.value.reparatur_dauer = Number(completionData.value.duration ?? 0)
      }
      await options.loadRepairLogs()
    } catch (err) {
      console.error('Error closing repair:', err)
      options.showSnackbar('Fehler beim Speichern: ' + (err as Error).message, 'error')
    } finally {
      savingStatus.value = false
    }
  }

  // ── Not-repairable flow ───────────────────────────────────────────────

  async function confirmNotRepairable(payload: { description: string; statusDetail: string; duration: number }) {
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
    if (pendingAbbruchPayload.value) {
      await saveNotRepairable(pendingAbbruchPayload.value)
      pendingAbbruchPayload.value = null
    }
  }

  async function saveNotRepairable(payload: { description: string; statusDetail: string; duration: number }) {
    if (!options.repairRecord.value) return
    savingStatus.value = true
    try {
      const fromStatus = normalizeRepairStatus(options.repairRecord.value.status)
      await repairStore.completeFailedRepair({
        repairId: options.repairRecord.value.id,
        fromStatus,
        statusDetail: payload.statusDetail || undefined,
        user_id: options.repairRecord.value.user_id || undefined,
        repairDescription: payload.description,
        repairDuration: payload.duration,
      })
      await RepairLogsService.createRepairLog(options.repairRecord.value.id, {
        user_id: options.repairRecord.value.user_id || undefined,
        reparatur_dauer: payload.duration,
        reparatur_besch: payload.description,
        status_from: fromStatus,
        status_to: 'Nicht Repariert',
      })
      options.showSnackbar('Reparatur als nicht reparierbar abgeschlossen')
      options.repairRecord.value.status = 'Nicht Repariert'
      options.repairRecord.value.status_detail = payload.statusDetail
      options.repairRecord.value.reparatur_besch = payload.description
      options.repairRecord.value.reparatur_dauer = payload.duration
      options.selectedRepairStatus.value = 'Nicht Repariert'
    } catch (err) {
      console.error('Error closing repair as not repairable:', err)
      options.showSnackbar('Fehler beim Speichern: ' + (err as Error).message, 'error')
    } finally {
      savingStatus.value = false
    }
  }

  return {
    // state
    savingStatus,
    transitionDialog,
    transitionUserId,
    completionDialog,
    completionData,
    notRepairableDialog,
    notRepairableData,
    abbruchSignatureDialog,
    // computed
    availableNextStatuses,
    bestNextStatus,
    otherNextStatuses,
    // functions
    handleCloseRepair,
    closeRepair,
    closeTransitionDialog,
    confirmTransitionWithReparateur,
    confirmRepairCompletion,
    openRepairCompletionDialog,
    closeRepairCompletionDialog,
    confirmNotRepairable,
    confirmAbbruchSignature,
    saveNotRepairable,
  }
}
