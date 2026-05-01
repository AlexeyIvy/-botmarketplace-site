/**
 * Typed clients for the strategy-preset endpoints (docs/51-T2/T3/T5).
 *
 * These wrap the shared `apiFetch`/`apiFetchNoWorkspace` helpers from
 * `../api` so the Lab Library page does not have to assemble headers or
 * problem-details handling itself.
 */

import { apiFetch, apiFetchNoWorkspace } from "../api";
import type { ProblemDetails } from "../api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type PresetCategory = "trend" | "dca" | "scalping" | "smc" | "arb";
export type PresetVisibility = "PRIVATE" | "PUBLIC";
export type PresetTimeframe = "M1" | "M5" | "M15" | "H1";

export interface PresetDefaultBotConfig {
  symbol: string;
  timeframe: PresetTimeframe;
  quoteAmount: number;
  maxOpenPositions: number;
  [k: string]: unknown;
}

/** GET /presets list row — no `dslJson`, only metadata + default config. */
export interface PresetSummary {
  slug: string;
  name: string;
  description: string;
  category: PresetCategory;
  defaultBotConfigJson: PresetDefaultBotConfig;
  datasetBundleHintJson: Record<string, unknown> | null;
  visibility: PresetVisibility;
  createdAt: string;
  updatedAt: string;
}

/** GET /presets/:slug — full record including `dslJson`. */
export interface PresetDetail extends PresetSummary {
  dslJson: unknown;
}

export interface InstantiateOverrides {
  symbol?: string;
  timeframe?: PresetTimeframe;
  quoteAmount?: number;
  maxOpenPositions?: number;
  name?: string;
}

export interface InstantiateResult {
  botId: string;
  strategyId: string;
  strategyVersionId: string;
}

export interface ListOptions {
  category?: PresetCategory;
  visibility?: PresetVisibility;
  /** Pass an admin token to bypass the PUBLIC-only filter for anonymous reads. */
  adminToken?: string;
}

// ---------------------------------------------------------------------------
// Result type — mirrors apiFetch's discriminated union
// ---------------------------------------------------------------------------

export type PresetResult<T> =
  | { ok: true; data: T }
  | { ok: false; problem: ProblemDetails };

// ---------------------------------------------------------------------------
// Clients
// ---------------------------------------------------------------------------

function buildQuery(opts: ListOptions): string {
  const params: string[] = [];
  if (opts.category) params.push(`category=${encodeURIComponent(opts.category)}`);
  if (opts.visibility) params.push(`visibility=${encodeURIComponent(opts.visibility)}`);
  return params.length ? `?${params.join("&")}` : "";
}

function adminHeader(token?: string): Record<string, string> {
  return token ? { "X-Admin-Token": token } : {};
}

/**
 * GET /presets — list. Anonymous callers see only PUBLIC; pass `adminToken`
 * to see PRIVATE entries (intended for the admin lane in /lab/library).
 *
 * Workspace-less endpoint: list does not require an active workspace.
 */
export function listPresets(opts: ListOptions = {}): Promise<PresetResult<PresetSummary[]>> {
  return apiFetchNoWorkspace<PresetSummary[]>(`/presets${buildQuery(opts)}`, {
    headers: adminHeader(opts.adminToken),
  });
}

/**
 * GET /presets/:slug — full record (PUBLIC anonymous, or PRIVATE with admin
 * token). Returns 404 — not 403 — when the caller cannot see the preset.
 */
export function getPreset(
  slug: string,
  opts: { adminToken?: string } = {},
): Promise<PresetResult<PresetDetail>> {
  return apiFetchNoWorkspace<PresetDetail>(`/presets/${encodeURIComponent(slug)}`, {
    headers: adminHeader(opts.adminToken),
  });
}

/**
 * POST /presets/:slug/instantiate — atomic Strategy + StrategyVersion + Bot
 * create in the active workspace. Caller must be authenticated and have
 * `X-Workspace-Id` set; admin token is only required for PRIVATE presets.
 */
export function instantiatePreset(
  slug: string,
  body: { overrides?: InstantiateOverrides } = {},
  opts: { adminToken?: string } = {},
): Promise<PresetResult<InstantiateResult>> {
  return apiFetch<InstantiateResult>(`/presets/${encodeURIComponent(slug)}/instantiate`, {
    method: "POST",
    headers: adminHeader(opts.adminToken),
    body: JSON.stringify(body),
  });
}
