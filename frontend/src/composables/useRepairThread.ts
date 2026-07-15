import { computed, type ComputedRef } from 'vue'
import type { RepairLog, VdeTestResponse, Repair } from '@/api/types'

export interface RepairThreadEntry {
  uniqueKey: string
  type: 'repair' | 'vde' | 'status_change' | 'created' | 'assignee_change'
  id: number
  created_at: string
  dateOnly?: boolean
  person: string
  duration: number
  description: string
  status_from?: string
  status_to?: string
  vdePassed?: boolean
}

export function buildVdeSummary(test: VdeTestResponse): string {
  const resultText =
    test.gesamtergebnis === true ? 'VDE-Test bestanden' : 'VDE-Test nicht bestanden'

  const details: string[] = []
  if (test.pruefgeraet_name) details.push(`Pruefgeraet: ${test.pruefgeraet_name}`)
  if (test.bemerkungen) details.push(test.bemerkungen)

  return details.length ? `${resultText}. ${details.join(' | ')}` : resultText
}

export function useRepairThread(
  repairLogs: ComputedRef<RepairLog[]> | { value: RepairLog[] },
  vdeTests: ComputedRef<VdeTestResponse[]> | { value: VdeTestResponse[] },
  repairRecord?: ComputedRef<Repair | null> | { value: Repair | null }
) {
  const sortedVdeTests = computed(() =>
    [...vdeTests.value].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
  )

  const latestVdeTests = computed(() => sortedVdeTests.value.slice(0, 1))

  const lastVdeTestPassed = computed(() => sortedVdeTests.value[0]?.gesamtergebnis === true)

  const threadEntries = computed<RepairThreadEntry[]>(() => {
    const repairEntries: RepairThreadEntry[] = repairLogs.value.map((log) => ({
      uniqueKey: `repair-${log.id}`,
      type: log.log_type === 'status_change' ? 'status_change' : log.log_type === 'assignee_change' ? 'assignee_change' : 'repair',
      id: log.id,
      created_at: log.created_at,
      person: log.user
        ? `${log.user.vorname} ${log.user.nachname}`
        : log.user_id
          ? String(log.user_id)
          : '?',
      duration: log.reparatur_dauer ?? 0,
      description: log.reparatur_besch ?? '',
      status_from: log.status_from ?? undefined,
      status_to: log.status_to ?? undefined,
    }))

    const vdeEntries: RepairThreadEntry[] = vdeTests.value.map((test) => ({
      uniqueKey: `vde-${test.id}`,
      type: 'vde',
      id: test.id,
      created_at: test.created_at,
      person: test.prufer || 'Unbekannt',
      duration: 0,
      description: buildVdeSummary(test),
      vdePassed: test.gesamtergebnis === true,
    }))

    const createdEntries: RepairThreadEntry[] = repairRecord?.value
      ? [
          {
            uniqueKey: 'created-0',
            type: 'created',
            id: repairRecord.value.id,
            created_at: repairRecord.value.datum,
            dateOnly: true,
            person: repairRecord.value.created_by
              ? `${repairRecord.value.created_by.vorname} ${repairRecord.value.created_by.nachname}`
              : '',
            duration: 0,
            description: '',
          },
        ]
      : []

    return [...repairEntries, ...vdeEntries, ...createdEntries].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
  })

  return {
    latestVdeTests,
    lastVdeTestPassed,
    threadEntries,
  }
}
