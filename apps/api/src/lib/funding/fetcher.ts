/**
 * HTTP fetch layer for Bybit funding/ticker data.
 *
 * Uses native fetch (Node 18+). Each function retries once on failure.
 */

import type { BybitFundingHistoryItem, BybitLinearTicker, BybitSpotTicker } from "./ingestion.js";
import { logger } from "../logger.js";

const BYBIT_BASE = "https://api.bybit.com";

// ── Generic helper ────────────────────────────────────────────────────────────

async function fetchWithRetry<T>(url: string, label: string): Promise<T> {
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status} ${res.statusText}`);
      }
      const json = (await res.json()) as { retCode: number; retMsg: string; result: T };
      if (json.retCode !== 0) {
        throw new Error(`Bybit API error: ${json.retMsg} (code ${json.retCode})`);
      }
      return json.result;
    } catch (err) {
      if (attempt === 0) {
        logger.warn({ err, url, label }, "Fetch failed, retrying once");
        continue;
      }
      throw err;
    }
  }
  // Unreachable, but satisfies TS
  throw new Error("fetchWithRetry: exhausted retries");
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Fetch funding rate history for a symbol.
 * Returns up to `limit` most recent items (default 200).
 */
export async function fetchFundingHistory(
  symbol: string,
  limit = 200,
): Promise<BybitFundingHistoryItem[]> {
  const url = `${BYBIT_BASE}/v5/market/funding/history?category=linear&symbol=${encodeURIComponent(symbol)}&limit=${limit}`;
  const result = await fetchWithRetry<{ list: BybitFundingHistoryItem[] }>(url, "fundingHistory");
  return result.list;
}

/**
 * Fetch all linear (perpetual) tickers.
 */
export async function fetchLinearTickers(): Promise<BybitLinearTicker[]> {
  const url = `${BYBIT_BASE}/v5/market/tickers?category=linear`;
  const result = await fetchWithRetry<{ list: BybitLinearTicker[] }>(url, "linearTickers");
  return result.list;
}

/**
 * Fetch all spot tickers.
 */
export async function fetchSpotTickers(): Promise<BybitSpotTicker[]> {
  const url = `${BYBIT_BASE}/v5/market/tickers?category=spot`;
  const result = await fetchWithRetry<{ list: BybitSpotTicker[] }>(url, "spotTickers");
  return result.list;
}
