/**
 * Funding rate ingestion — normalizes exchange API responses into
 * typed FundingSnapshot and SpreadSnapshot records.
 *
 * This module handles parsing/normalization only. Actual HTTP calls
 * to the exchange are the caller's responsibility (bybitCandles.ts
 * or a dedicated funding fetcher).
 *
 * Bybit API response shapes:
 *   GET /v5/market/funding/history → { list: [{ symbol, fundingRate, fundingRateTimestamp }] }
 *   GET /v5/market/tickers?category=linear → { list: [{ symbol, fundingRate, nextFundingTime, lastPrice }] }
 *   GET /v5/market/tickers?category=spot → { list: [{ symbol, lastPrice }] }
 *
 * Pure functions — no HTTP, no side effects, deterministic.
 */

import type { FundingSnapshot, SpreadSnapshot } from "./types.js";
import { computeBasisBps } from "./basis.js";

// ── Bybit raw response types (subset we use) ───────────────────────────────

export interface BybitFundingHistoryItem {
  symbol: string;
  fundingRate: string;
  fundingRateTimestamp: string;
}

export interface BybitLinearTicker {
  symbol: string;
  fundingRate: string;
  nextFundingTime: string;
  lastPrice: string;
}

export interface BybitSpotTicker {
  symbol: string;
  lastPrice: string;
}

// ── Normalization functions ─────────────────────────────────────────────────

/**
 * Parse a Bybit funding history item into a FundingSnapshot.
 */
export function parseFundingHistoryItem(item: BybitFundingHistoryItem): FundingSnapshot {
  const timestamp = Number(item.fundingRateTimestamp);
  return {
    symbol: item.symbol,
    fundingRate: parseFloat(item.fundingRate),
    nextFundingAt: timestamp + 8 * 60 * 60 * 1000, // next settlement is 8h later
    timestamp,
  };
}

/**
 * Parse a batch of Bybit funding history items.
 * Returns snapshots sorted by timestamp ascending.
 */
export function parseFundingHistory(items: BybitFundingHistoryItem[]): FundingSnapshot[] {
  return items
    .map(parseFundingHistoryItem)
    .sort((a, b) => a.timestamp - b.timestamp);
}

/**
 * Parse a Bybit linear ticker into a FundingSnapshot (current rate).
 */
export function parseLinearTicker(ticker: BybitLinearTicker): FundingSnapshot {
  return {
    symbol: ticker.symbol,
    fundingRate: parseFloat(ticker.fundingRate),
    nextFundingAt: Number(ticker.nextFundingTime),
    timestamp: Date.now(), // current observation time
  };
}

/**
 * Build a SpreadSnapshot from a linear ticker (perp) and a spot ticker.
 *
 * @param perpTicker   Bybit linear ticker with lastPrice.
 * @param spotTicker   Bybit spot ticker with lastPrice.
 * @param timestamp    Observation time (ms epoch). Pass explicitly for determinism in tests.
 * @returns SpreadSnapshot, or null if symbols don't match or prices are invalid.
 */
export function buildSpreadFromTickers(
  perpTicker: BybitLinearTicker,
  spotTicker: BybitSpotTicker,
  timestamp: number,
): SpreadSnapshot | null {
  const perpPrice = parseFloat(perpTicker.lastPrice);
  const spotPrice = parseFloat(spotTicker.lastPrice);

  if (!isFinite(perpPrice) || !isFinite(spotPrice) || spotPrice <= 0) {
    return null;
  }

  return {
    symbol: perpTicker.symbol,
    spotPrice,
    perpPrice,
    basisBps: computeBasisBps(spotPrice, perpPrice),
    timestamp,
  };
}
