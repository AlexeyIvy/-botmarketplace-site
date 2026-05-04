/**
 * Typed client for the funding scanner endpoint (docs/55-T3 §UI).
 *
 * Wraps GET /terminal/funding/scanner. The route runs the
 * `scanFundingCandidates` library against the last 7 days of
 * FundingSnapshot rows joined with the latest SpreadSnapshot per
 * symbol — see `apps/api/src/routes/funding.ts` for the
 * implementation. This client is the single import point for the
 * lab/funding page.
 */

import { apiFetch } from "../api";

// ---------------------------------------------------------------------------
// Types — match `apps/api/src/lib/funding/types.ts` exactly. The route
// serialises `nextFundingAt` from ms epoch to ISO string before returning.
// ---------------------------------------------------------------------------

export interface FundingCandidate {
  symbol: string;
  /** Current funding rate (decimal, e.g. 0.0001 = 0.01%). */
  currentRate: number;
  /** Annualized funding yield as a percentage (e.g. 10.95). */
  annualizedYieldPct: number;
  /** Current basis in basis points: (perp - spot) / spot * 10_000. */
  basisBps: number;
  /** Number of consecutive same-sign funding periods. */
  streak: number;
  /** Average funding rate over the lookback window (decimal). */
  avgRate: number;
  /** Next funding settlement time as ISO-8601 string, or null when no
   *  snapshot is available yet for the candidate. */
  nextFundingAt: string | null;
}

export interface ScannerResponse {
  candidates: FundingCandidate[];
  /** Server-side scan timestamp (ISO-8601). Useful so the UI can show a
   *  "scanned at" label distinct from the page load time. */
  updatedAt: string;
}

export interface ScannerOptions {
  /** Minimum absolute annualized yield (%) to qualify. Default 5. */
  minYield?: number;
  /** Maximum absolute basis (bps) to qualify. Default 50. */
  maxBasis?: number;
  /** Minimum consecutive same-sign funding streak. Default 3. */
  minStreak?: number;
  /** Top-N candidates to return. Default 10. */
  limit?: number;
}

// ---------------------------------------------------------------------------
// Endpoint
// ---------------------------------------------------------------------------

function buildQuery(opts: ScannerOptions): string {
  const params: string[] = [];
  if (opts.minYield !== undefined) params.push(`minYield=${opts.minYield}`);
  if (opts.maxBasis !== undefined) params.push(`maxBasis=${opts.maxBasis}`);
  if (opts.minStreak !== undefined) params.push(`minStreak=${opts.minStreak}`);
  if (opts.limit !== undefined) params.push(`limit=${opts.limit}`);
  return params.length > 0 ? `?${params.join("&")}` : "";
}

/**
 * Run the funding scanner with the given thresholds. Returns the ranked
 * candidates plus the server-side `updatedAt` timestamp.
 */
export function scanFundingCandidates(opts: ScannerOptions = {}) {
  return apiFetch<ScannerResponse>(`/terminal/funding/scanner${buildQuery(opts)}`);
}
