import type { SettingResponse } from "../generated/data-contracts";

const BASE = "/api";
const HEADERS = { "Content-Type": "application/json" };
const CREDS = "include" as const;

async function apiFetch<T>(url: string, method = "GET", body?: unknown): Promise<T> {
  const opts: RequestInit = { method, credentials: CREDS };
  if (body !== undefined) {
    opts.headers = HEADERS;
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(BASE + url, opts);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    let error = text;
    try {
      error = JSON.parse(text)?.error ?? text;
    } catch {
      /* ignore */
    }
    throw { status: res.status, body: { error } };
  }
  return res.json() as Promise<T>;
}

export class SettingsService {
  /** Get all active settings grouped by category (public). */
  static getGrouped(): Promise<Record<string, Array<{ id: number; name: string; serial_number?: string }>>> {
    return apiFetch(`/settings`);
  }

  /** Get all settings including inactive — admin only. */
  static getAll(): Promise<{ reply: string; data: SettingResponse[] }> {
    return apiFetch(`/settings/all`);
  }

  /** Create a new setting entry — admin only. */
  static create(body: {
    category: string;
    name: string;
    serial_number?: string | null;
    sort_order?: number;
  }): Promise<{ reply: string; data: SettingResponse }> {
    return apiFetch(`/settings`, "POST", body);
  }

  /** Update a setting entry — admin only. */
  static update(
    id: number,
    body: {
      name?: string;
      serial_number?: string | null;
      sort_order?: number;
      is_active?: boolean;
    }
  ): Promise<{ reply: string; data: SettingResponse }> {
    return apiFetch(`/settings/${id}`, "PUT", body);
  }

  /** Delete a setting entry — admin only. */
  static delete(id: number): Promise<{ reply: string }> {
    return apiFetch(`/settings/${id}`, "DELETE");
  }
}
