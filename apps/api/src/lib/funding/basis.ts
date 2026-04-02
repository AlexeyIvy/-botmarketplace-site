/**
 * Basis spread computation for funding rate arbitrage.
 *
 * Basis = (perpPrice - spotPrice) / spotPrice
 *
 * A positive basis means perp trades at a premium to spot (contango),
 * which typically correlates with positive funding (longs pay shorts).
 * A negative basis means perp trades at a discount (backwardation).
 *
 * Pure functions — no side effects, deterministic.
 */

import type { SpreadSnapshot } from "./types.js";

/**
 * Compute basis in basis points between perp and spot price.
 *
 * @param spotPrice  Spot market price.
 * @param perpPrice  Perpetual futures price.
 * @returns Basis in basis points (bps). Positive = contango (perp premium).
 */
export function computeBasisBps(spotPrice: number, perpPrice: number): number {
  if (spotPrice <= 0 || !isFinite(spotPrice)) return 0;
  if (!isFinite(perpPrice)) return 0;
  return ((perpPrice - spotPrice) / spotPrice) * 10_000;
}

/**
 * Build a SpreadSnapshot from raw price data.
 */
export function buildSpreadSnapshot(
  symbol: string,
  spotPrice: number,
  perpPrice: number,
  timestamp: number,
): SpreadSnapshot {
  return {
    symbol,
    spotPrice,
    perpPrice,
    basisBps: computeBasisBps(spotPrice, perpPrice),
    timestamp,
  };
}

/**
 * Compute the annualized basis yield from a basis in bps.
 *
 * Assumes continuous funding at the given basis level.
 * Annualized = basisBps / 10_000 * (365 / holdingDays) * 100
 *
 * @param basisBps     Current basis in bps.
 * @param holdingDays  Assumed holding period in days. Default: 1 (daily roll).
 * @returns Annualized yield as a percentage.
 */
export function annualizedBasisYieldPct(basisBps: number, holdingDays = 1): number {
  if (holdingDays <= 0) return 0;
  return (basisBps / 10_000) * (365 / holdingDays) * 100;
}
