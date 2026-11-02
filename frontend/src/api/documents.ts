/*
 * URLs of files served by the API (opened or downloaded directly by the browser)
 * and the existence check for generated repair PDFs, which uses HEAD and is
 * therefore not part of the generated client.
 */
import { sessionFetch } from './session'

export type RepairDocument = 'disclaimer' | 'cancellation'

export function attachmentUrl(repairId: number, attachmentId: number): string {
  return `/api/repairs/${repairId}/attachments/${attachmentId}`
}

export function documentUrl(repairId: number, document: RepairDocument): string {
  return `/api/repairs/${repairId}/${document}`
}

/** Whether a generated PDF exists; network errors count as "no". */
export async function documentExists(repairId: number, document: RepairDocument): Promise<boolean> {
  try {
    const res = await sessionFetch(documentUrl(repairId, document), { method: 'HEAD' })
    return res.ok
  } catch {
    return false
  }
}
