import { api } from '@/api/client'
import { computed, ref, shallowRef, toValue, watch, type MaybeRefOrGetter } from 'vue'
import { attachmentUrl, documentExists } from '@/api/documents'
import type {
  Repair,
  RepairAttachmentResponse as RepairAttachment,
  RepairLog,
  VdeTestResponse,
} from '@/api/types'
import { calculateRepairDurationFromLogs } from '@/stores/repairStore'
import { useRepairThread } from '@/composables/useRepairThread'

export interface LogAttachment {
  name: string
  url: string
  content_type: string
  size: number
}

/**
 * Loads and owns everything shown for one repair, identified by its QR token:
 * the repair, its logs, VDE tests, attachments and generated documents.
 * Reloads when the token changes and ignores responses for a previous repair.
 */
export function useRepairDetail(
  qrToken: MaybeRefOrGetter<string | undefined>,
  options: { onLoaded?: (repair: Repair) => void } = {}
) {
  const loading = shallowRef(true)
  const error = shallowRef('')
  const repair = ref<Repair | null>(null)
  const logs = ref<RepairLog[]>([])
  const vdeTests = ref<VdeTestResponse[]>([])
  const attachments = ref<RepairAttachment[]>([])
  const disclaimerExists = shallowRef(false)
  const cancellationExists = shallowRef(false)

  /** Still showing the repair with this id? (it may have changed while awaiting) */
  const isCurrent = (repairId: number) => repair.value?.id === repairId

  async function reloadRepair() {
    const token = toValue(qrToken)
    if (!token) return
    try {
      const response = await api.getRepairByQrToken({ token: token })
      if (response?.data && toValue(qrToken) === token) {
        repair.value = response.data as Repair
      }
    } catch (err) {
      console.error('Error reloading repair record:', err)
    }
  }

  async function reloadLogs() {
    const repairId = repair.value?.id
    if (!repairId) return
    try {
      const response = await api.listRepairLogs({ repairId: repairId })
      if (response.data && isCurrent(repairId)) logs.value = response.data
    } catch (err) {
      console.error('Error loading repair logs:', err)
    }
  }

  async function reloadVdeTests() {
    const repairId = repair.value?.id
    if (!repairId) return
    try {
      const response = await api.listVdeTests({ repairId: repairId })
      if (response.reply === 'done' && response.data && isCurrent(repairId)) {
        vdeTests.value = response.data
      }
    } catch (err) {
      console.error('Error loading VDE tests:', err)
    }
  }

  async function reloadAttachments() {
    const repairId = repair.value?.id
    if (!repairId) return
    try {
      const response = await api.listRepairAttachments({ repairId })
      if (isCurrent(repairId)) attachments.value = response.data ?? []
    } catch (err) {
      console.error('Error loading attachments:', err)
    }
  }

  async function reloadDocuments() {
    const repairId = repair.value?.id
    if (!repairId) return
    const [disclaimer, cancellation] = await Promise.all([
      documentExists(repairId, 'disclaimer'),
      documentExists(repairId, 'cancellation'),
    ])
    if (!isCurrent(repairId)) return
    disclaimerExists.value = disclaimer
    cancellationExists.value = cancellation
  }

  let loadToken = 0

  async function load(token: string | undefined) {
    const current = ++loadToken
    const stillLoading = () => current === loadToken
    repair.value = null
    logs.value = []
    vdeTests.value = []
    attachments.value = []
    disclaimerExists.value = false
    cancellationExists.value = false
    error.value = ''
    loading.value = true

    if (!token) {
      error.value = 'Kein QR-Token angegeben'
      loading.value = false
      return
    }

    try {
      const response = await api.getRepairByQrToken({ token: token })
      if (!stillLoading()) return
      if (!response?.data) {
        error.value = 'Reparatur nicht gefunden'
        loading.value = false
        return
      }
      repair.value = response.data as Repair
      options.onLoaded?.(repair.value)

      await Promise.all([reloadLogs(), reloadVdeTests(), reloadAttachments(), reloadDocuments()])
      if (stillLoading()) loading.value = false
    } catch (err) {
      if (!stillLoading()) return
      console.error('Error loading repair:', err)
      error.value = 'Fehler beim Laden der Reparaturdaten: ' + (err as Error).message
      loading.value = false
    }
  }

  // Navigating /edit/a -> /edit/b (e.g. QR scan) reuses the page component
  watch(() => toValue(qrToken), load, { immediate: true })

  const { latestVdeTests, lastVdeTestPassed, threadEntries } = useRepairThread(
    logs,
    vdeTests,
    repair
  )
  const hasVdeTest = computed(() => vdeTests.value.length > 0)
  const loggedDuration = computed(() => calculateRepairDurationFromLogs(logs.value))

  /** Attachments grouped by the log entry they belong to. */
  const logAttachments = computed<Record<number, LogAttachment[]>>(() => {
    const grouped: Record<number, LogAttachment[]> = {}
    const repairId = repair.value?.id
    if (!repairId) return grouped
    for (const att of attachments.value) {
      if (att.log_id == null) continue
      ;(grouped[att.log_id] ??= []).push({
        name: att.original_filename,
        url: attachmentUrl(repairId, att.id),
        content_type: att.content_type,
        size: att.size,
      })
    }
    return grouped
  })

  return {
    loading,
    error,
    repair,
    logs,
    vdeTests,
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
  }
}
