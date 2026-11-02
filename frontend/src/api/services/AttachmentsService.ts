/* Repair attachments and generated repair documents (disclaimer, cancellation) */
import { sessionFetch } from "../session";

export interface RepairAttachment {
  id: number;
  repair_id: number;
  log_id: number | null;
  attachment_type: string;
  original_filename: string;
  stored_filename: string;
  content_type: string;
  size: number;
  uploaded_at: string;
  uploaded_by_id: number | null;
}

export type RepairDocument = "disclaimer" | "cancellation";

const base = (repairId: number) => `/api/repairs/${repairId}`;

export function attachmentUrl(repairId: number, attachmentId: number): string {
  return `${base(repairId)}/attachments/${attachmentId}`;
}

export function documentUrl(repairId: number, document: RepairDocument): string {
  return `${base(repairId)}/${document}`;
}

async function ensureOk(res: Response): Promise<Response> {
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.error ?? `HTTP ${res.status}`);
  }
  return res;
}

export const AttachmentsService = {
  async list(repairId: number): Promise<RepairAttachment[]> {
    const res = await ensureOk(await sessionFetch(`${base(repairId)}/attachments`));
    const data = await res.json();
    if (data.reply !== "done") throw new Error(data.error ?? "Unexpected response");
    return data.data as RepairAttachment[];
  },

  async upload(
    repairId: number,
    files: File[],
    fields: { attachment_type: "misc" | "log_entry"; log_id?: number; uploaded_by_id?: number },
  ): Promise<void> {
    const fd = new FormData();
    files.forEach((file) => fd.append("files", file));
    fd.append("attachment_type", fields.attachment_type);
    if (fields.log_id !== undefined) fd.append("log_id", String(fields.log_id));
    if (fields.uploaded_by_id !== undefined) fd.append("uploaded_by_id", String(fields.uploaded_by_id));
    await ensureOk(await sessionFetch(`${base(repairId)}/attachments`, { method: "POST", body: fd }));
  },

  async remove(repairId: number, attachmentId: number): Promise<void> {
    await ensureOk(await sessionFetch(attachmentUrl(repairId, attachmentId), { method: "DELETE" }));
  },

  /** Whether a generated PDF exists; network errors count as "no". */
  async documentExists(repairId: number, document: RepairDocument): Promise<boolean> {
    try {
      const res = await sessionFetch(documentUrl(repairId, document), { method: "HEAD" });
      return res.ok;
    } catch {
      return false;
    }
  },
};
