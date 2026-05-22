/* VDE Tests API Service */
import type {
  VdeTestResponse,
  VdeTestCreate,
} from "../generated/data-contracts";

export type { VdeTestResponse, VdeTestCreate };

const BASE = "/api";
const HEADERS = { "Content-Type": "application/json" };
const CREDS = "include" as const;

async function apiFetch<T>(
  url: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
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

export interface VdeTestListResponse {
  reply: string;
  data: VdeTestResponse[];
  total: number;
  error?: string;
}

export interface VdeTestCreateResponse {
  reply: string;
  message?: string;
  data?: VdeTestResponse;
  id?: number;
  error?: string;
}

export class VdeTestsService {
  static listVdeTests(repairId: number): Promise<VdeTestListResponse> {
    return apiFetch(`/repairs/${repairId}/vde-tests`);
  }

  static createVdeTest(
    repairId: number,
    body: Omit<VdeTestCreate, "repair_id">,
  ): Promise<VdeTestCreateResponse> {
    return apiFetch(`/repairs/${repairId}/vde-tests`, "POST", {
      ...body,
      repair_id: repairId,
    });
  }

  static getVdeTest(
    repairId: number,
    testId: number,
  ): Promise<{ reply: string; data?: VdeTestResponse; error?: string }> {
    return apiFetch(`/repairs/${repairId}/vde-tests/${testId}`);
  }
}
